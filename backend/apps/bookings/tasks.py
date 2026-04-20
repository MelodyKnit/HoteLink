"""apps/bookings/tasks.py —— 订单相关异步任务。"""

import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def append_operator_remark(order, message: str) -> bool:
    """向订单备注追加系统提示（幂等），并控制字段长度。"""
    normalized = (message or "").strip()
    if not normalized:
        return False

    current = (order.operator_remark or "").strip()
    if normalized in current:
        return False

    if not current:
        next_value = normalized[:255]
    elif len(normalized) >= 255:
        next_value = normalized[:255]
    else:
        remain = 255 - len(normalized) - 1
        if remain <= 0:
            next_value = normalized
        else:
            prefix = current[-remain:]
            next_value = f"{prefix}；{normalized}" if prefix else normalized

    if next_value == current:
        return False
    order.operator_remark = next_value
    return True


def cancel_timeout_unpaid_order(order, *, cancel_minutes: int) -> bool:
    """将待支付且超时的订单取消，并回滚优惠券与发送通知。"""
    from apps.bookings.models import BookingOrder
    from apps.crm.models import UserCoupon
    from apps.operations.models import SystemNotice

    if order.status != BookingOrder.STATUS_PENDING_PAYMENT:
        return False
    if order.payment_status == BookingOrder.PAYMENT_PAID:
        return False

    order.status = BookingOrder.STATUS_CANCELLED
    order.cancelled_at = timezone.now()
    order.operator_remark = f"系统自动取消：超过{cancel_minutes}分钟未支付"
    order.save(update_fields=["status", "cancelled_at", "operator_remark", "updated_at"])

    # 归还库存
    from datetime import timedelta
    from django.db.models import F
    from apps.hotels.models import RoomInventory
    nights = (order.check_out_date - order.check_in_date).days
    date_range = [order.check_in_date + timedelta(days=i) for i in range(nights)]
    RoomInventory.objects.filter(
        room_type_id=order.room_type_id, date__in=date_range,
    ).update(stock=F("stock") + 1)

    if order.coupon_id:
        UserCoupon.objects.filter(
            pk=order.coupon_id,
            status=UserCoupon.STATUS_USED,
            used_order_id=order.id,
        ).update(status=UserCoupon.STATUS_UNUSED, used_order=None, used_at=None)

    SystemNotice.objects.create(
        user_id=order.user_id,
        notice_type=SystemNotice.TYPE_ORDER,
        title="订单已自动取消",
        content=f"订单 {order.order_no} 因超过{cancel_minutes}分钟未支付已被系统自动取消。如需预订请重新下单。",
        related_order=order,
    )
    return True


def complete_overdue_checked_in_order(order, *, today) -> bool:
    """将离店日期已过仍显示已入住的订单自动完结。"""
    from apps.bookings.models import BookingOrder
    from apps.operations.models import SystemNotice

    if order.status != BookingOrder.STATUS_CHECKED_IN:
        return False
    if order.check_out_date >= today:
        return False

    note = f"系统自动完结：离店日 {order.check_out_date} 已过，自动补退房"
    remark_changed = append_operator_remark(order, note)
    order.status = BookingOrder.STATUS_COMPLETED
    order.completed_at = timezone.now()
    update_fields = ["status", "completed_at", "updated_at"]
    if remark_changed:
        update_fields.append("operator_remark")
    order.save(update_fields=update_fields)

    SystemNotice.objects.create(
        user_id=order.user_id,
        notice_type=SystemNotice.TYPE_ORDER,
        title="订单已自动完结",
        content=f"订单 {order.order_no} 因超过离店日期未办理退房，系统已自动完结。如有疑问请联系客服。",
        related_order=order,
    )
    return True


def mark_overdue_unchecked_in_order(order, *, today) -> bool:
    """标记已过离店日期但仍未办理入住/退房的已支付订单。"""
    from apps.bookings.models import BookingOrder

    if order.status not in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}:
        return False
    if order.check_out_date >= today:
        return False

    note = f"系统异常提醒：离店日 {order.check_out_date} 已过，仍未办理入住/退房，请人工核查"
    changed = append_operator_remark(order, note)
    if not changed:
        return False
    order.save(update_fields=["operator_remark", "updated_at"])
    return True


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def auto_cancel_unpaid_order(self, order_id: int):
    """未支付自动取消订单，归还优惠券并发送系统通知。"""
    from apps.bookings.models import BookingOrder
    from apps.operations.models import PlatformConfig

    cancel_minutes = PlatformConfig.load().order_auto_cancel_minutes
    with transaction.atomic():
        try:
            order = BookingOrder.objects.select_for_update().get(pk=order_id)
        except BookingOrder.DoesNotExist:
            logger.warning("auto_cancel: order %s not found, skipping", order_id)
            return
        cancelled = cancel_timeout_unpaid_order(order, cancel_minutes=cancel_minutes)

    if cancelled:
        logger.info("auto_cancel: order %s cancelled successfully", order.order_no)
    else:
        logger.info("auto_cancel: order %s status=%s payment_status=%s, skipping", order.order_no, order.status, order.payment_status)


@shared_task(bind=True)
def sweep_timeout_unpaid_orders(self, batch_size: int = 500):
    """周期巡检：批量取消超过配置时间仍未支付的订单。"""
    from apps.bookings.models import BookingOrder
    from apps.operations.models import PlatformConfig

    cancel_minutes = PlatformConfig.load().order_auto_cancel_minutes
    deadline = timezone.now() - timedelta(minutes=cancel_minutes)
    stale_ids = list(
        BookingOrder.objects.filter(
            status=BookingOrder.STATUS_PENDING_PAYMENT,
            payment_status=BookingOrder.PAYMENT_UNPAID,
            created_at__lte=deadline,
        )
        .order_by("created_at")
        .values_list("id", flat=True)[: max(int(batch_size), 1)]
    )

    cancelled_count = 0
    for order_id in stale_ids:
        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(pk=order_id).first()
            if not order:
                continue
            if cancel_timeout_unpaid_order(order, cancel_minutes=cancel_minutes):
                cancelled_count += 1

    logger.info(
        "sweep_timeout_unpaid_orders: checked=%s cancelled=%s deadline=%s",
        len(stale_ids),
        cancelled_count,
        deadline.isoformat(),
    )
    return {"checked": len(stale_ids), "cancelled": cancelled_count, "cancel_minutes": cancel_minutes}


@shared_task(bind=True)
def sweep_order_lifecycle_anomalies(self, batch_size: int = 500):
    """周期巡检：修复订单生命周期异常，避免过期状态长期滞留。"""
    from apps.bookings.models import BookingOrder

    safe_batch_size = max(int(batch_size), 1)
    today = timezone.localdate()

    overdue_checked_in_ids = list(
        BookingOrder.objects.filter(
            status=BookingOrder.STATUS_CHECKED_IN,
            check_out_date__lt=today,
        )
        .order_by("check_out_date", "id")
        .values_list("id", flat=True)[:safe_batch_size]
    )

    completed_count = 0
    for order_id in overdue_checked_in_ids:
        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(pk=order_id).first()
            if not order:
                continue
            if complete_overdue_checked_in_order(order, today=today):
                completed_count += 1

    overdue_unchecked_in_ids = list(
        BookingOrder.objects.filter(
            status__in=[BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED],
            check_out_date__lt=today,
        )
        .order_by("check_out_date", "id")
        .values_list("id", flat=True)[:safe_batch_size]
    )

    marked_count = 0
    for order_id in overdue_unchecked_in_ids:
        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(pk=order_id).first()
            if not order:
                continue
            if mark_overdue_unchecked_in_order(order, today=today):
                marked_count += 1

    logger.info(
        "sweep_order_lifecycle_anomalies: overdue_checked_in=%s auto_completed=%s overdue_unchecked_in=%s marked=%s today=%s",
        len(overdue_checked_in_ids),
        completed_count,
        len(overdue_unchecked_in_ids),
        marked_count,
        today.isoformat(),
    )
    return {
        "overdue_checked_in": len(overdue_checked_in_ids),
        "auto_completed": completed_count,
        "overdue_unchecked_in": len(overdue_unchecked_in_ids),
        "marked": marked_count,
        "date": today.isoformat(),
    }


@shared_task(bind=True)
def sweep_expired_coupons(self, batch_size: int = 1000):
    """周期巡检：将已过有效期但仍为 unused 的用户优惠券标记为 expired。"""
    from apps.crm.models import UserCoupon

    today = timezone.localdate()
    updated = UserCoupon.objects.filter(
        status=UserCoupon.STATUS_UNUSED,
        valid_end__lt=today,
    ).update(status=UserCoupon.STATUS_EXPIRED)

    logger.info("sweep_expired_coupons: marked_expired=%s today=%s", updated, today.isoformat())
    return {"marked_expired": updated, "date": today.isoformat()}
