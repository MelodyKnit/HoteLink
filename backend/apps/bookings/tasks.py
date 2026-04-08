"""apps/bookings/tasks.py —— 订单相关异步任务。"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def auto_cancel_unpaid_order(self, order_id: int):
    """未支付自动取消订单，归还优惠券并发送系统通知。"""
    from apps.bookings.models import BookingOrder
    from apps.crm.models import UserCoupon
    from apps.operations.models import PlatformConfig, SystemNotice

    try:
        order = BookingOrder.objects.select_related("coupon").get(pk=order_id)
    except BookingOrder.DoesNotExist:
        logger.warning("auto_cancel: order %s not found, skipping", order_id)
        return

    # 仅取消仍处于待支付状态的订单
    if order.status != BookingOrder.STATUS_PENDING_PAYMENT:
        logger.info("auto_cancel: order %s status is %s, skipping", order.order_no, order.status)
        return

    order.status = BookingOrder.STATUS_CANCELLED
    cancel_minutes = PlatformConfig.load().order_auto_cancel_minutes
    order.operator_remark = f"系统自动取消：超过{cancel_minutes}分钟未支付"
    order.save(update_fields=["status", "operator_remark", "updated_at"])

    # 归还优惠券
    if order.coupon_id:
        UserCoupon.objects.filter(
            pk=order.coupon_id, status=UserCoupon.STATUS_USED,
        ).update(status=UserCoupon.STATUS_UNUSED, used_order=None, used_at=None)

    # 发送通知
    SystemNotice.objects.create(
        user_id=order.user_id,
        notice_type=SystemNotice.TYPE_ORDER,
        title="订单已自动取消",
        content=f"订单 {order.order_no} 因超过{cancel_minutes}分钟未支付已被系统自动取消。如需预订请重新下单。",
    )

    logger.info("auto_cancel: order %s cancelled successfully", order.order_no)
