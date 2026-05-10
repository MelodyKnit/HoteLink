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


def mark_no_show_order(order, *, today) -> bool:
    """将离店日期已过且未入住的已支付订单标记为未入住。"""
    from apps.bookings.models import BookingOrder
    from apps.operations.models import SystemNotice

    if order.status not in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}:
        return False
    if order.payment_status != BookingOrder.PAYMENT_PAID:
        return False
    if order.check_out_date >= today:
        return False

    note = f"系统自动标记未入住：离店日 {order.check_out_date} 已过，订单未办理入住/退房"
    remark_changed = append_operator_remark(order, note)
    order.status = BookingOrder.STATUS_NO_SHOW
    order.no_show_at = timezone.now()
    update_fields = ["status", "no_show_at", "updated_at"]
    if remark_changed:
        update_fields.append("operator_remark")
    order.save(update_fields=update_fields)

    SystemNotice.objects.create(
        user_id=order.user_id,
        notice_type=SystemNotice.TYPE_ORDER,
        title="订单已标记为未入住",
        content=f"订单 {order.order_no} 的离店日期已过，系统已标记为未入住。支付记录仍保留，如需处理退款或申诉请联系客服。",
        related_order=order,
    )
    return True


def refresh_order_lifecycle(order, *, today=None) -> bool:
    """刷新已加锁订单的过期生命周期状态。"""
    current_day = today or timezone.localdate()
    if complete_overdue_checked_in_order(order, today=current_day):
        return True
    if mark_no_show_order(order, today=current_day):
        return True
    return False


def repair_overdue_order_lifecycles(*, user_id=None, batch_size: int = 200, today=None) -> dict:
    """批量修复过期订单状态，避免列表或详情继续展示陈旧生命周期。"""
    from apps.bookings.models import BookingOrder

    current_day = today or timezone.localdate()
    safe_batch_size = max(int(batch_size), 1)
    queryset = BookingOrder.objects.filter(
        status__in=[
            BookingOrder.STATUS_CHECKED_IN,
            BookingOrder.STATUS_PAID,
            BookingOrder.STATUS_CONFIRMED,
        ],
        check_out_date__lt=current_day,
    )
    if user_id is not None:
        queryset = queryset.filter(user_id=user_id)

    order_ids = list(
        queryset.order_by("check_out_date", "id").values_list("id", flat=True)[:safe_batch_size]
    )

    completed_count = 0
    no_show_count = 0
    for order_id in order_ids:
        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(pk=order_id).first()
            if not order:
                continue
            previous_status = order.status
            if not refresh_order_lifecycle(order, today=current_day):
                continue
            if order.status == BookingOrder.STATUS_COMPLETED and previous_status != order.status:
                completed_count += 1
            if order.status == BookingOrder.STATUS_NO_SHOW and previous_status != order.status:
                no_show_count += 1

    return {
        "checked": len(order_ids),
        "auto_completed": completed_count,
        "marked_no_show": no_show_count,
        "date": current_day.isoformat(),
    }


def build_checkin_reminder_content(order) -> str:
    """Build a concise pre-arrival reminder message for an upcoming order.

    Args:
        order: Booking order that is expected to check in soon.

    Returns:
        A SystemNotice-safe message containing hotel address, room type, and check-in guidance.
    """
    hotel = order.hotel
    room_type = order.room_type
    hotel_name = hotel.name if hotel else "预订酒店"
    address = hotel.address if hotel and hotel.address else "请在订单详情中查看酒店地址"
    phone = hotel.phone if hotel and hotel.phone else "酒店联系电话以订单详情为准"
    room_name = room_type.name if room_type else "已订房型"
    content = (
        f"您预订的{hotel_name}{order.check_in_date}入住，房型：{room_name}。"
        f"地址：{address}；联系电话：{phone}。请携带有效证件，建议提前确认交通与到店时间。"
    )
    return content[:255]


def create_checkin_reminder_notice(order) -> bool:
    """Create one idempotent pre-arrival notice for an order.

    Args:
        order: Booking order that should receive a check-in reminder.

    Returns:
        True when a new notice is created, otherwise False.
    """
    from apps.operations.models import SystemNotice

    exists = SystemNotice.objects.filter(
        user_id=order.user_id,
        related_order=order,
        notice_type=SystemNotice.TYPE_ORDER,
        title="入住提醒",
    ).exists()
    if exists:
        return False

    # Keep the reminder idempotent because Celery Beat may retry or run on multiple workers.
    SystemNotice.objects.create(
        user_id=order.user_id,
        notice_type=SystemNotice.TYPE_ORDER,
        title="入住提醒",
        content=build_checkin_reminder_content(order),
        related_order=order,
    )
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
def send_upcoming_checkin_reminders(self, batch_size: int = 500, days_before: int = 1):
    """周期巡检：为即将入住的有效订单发送行前提醒。"""
    from apps.bookings.models import BookingOrder

    safe_batch_size = max(int(batch_size), 1)
    safe_days_before = max(int(days_before), 0)
    target_date = timezone.localdate() + timedelta(days=safe_days_before)
    order_ids = list(
        BookingOrder.objects.filter(
            check_in_date=target_date,
            status__in=[BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED],
        )
        .order_by("check_in_date", "id")
        .values_list("id", flat=True)[:safe_batch_size]
    )

    sent_count = 0
    for order_id in order_ids:
        with transaction.atomic():
            order = (
                BookingOrder.objects.select_for_update()
                .select_related("hotel", "room_type")
                .filter(pk=order_id)
                .first()
            )
            if not order:
                continue
            if create_checkin_reminder_notice(order):
                sent_count += 1

    logger.info(
        "send_upcoming_checkin_reminders: checked=%s sent=%s target_date=%s",
        len(order_ids),
        sent_count,
        target_date.isoformat(),
    )
    return {"checked": len(order_ids), "sent": sent_count, "target_date": target_date.isoformat()}


@shared_task(bind=True)
def sweep_order_lifecycle_anomalies(self, batch_size: int = 500):
    """周期巡检：修复订单生命周期异常，避免过期状态长期滞留。"""
    from apps.bookings.models import BookingOrder

    safe_batch_size = max(int(batch_size), 1)
    today = timezone.localdate()

    result = repair_overdue_order_lifecycles(batch_size=safe_batch_size, today=today)

    logger.info(
        "sweep_order_lifecycle_anomalies: checked=%s auto_completed=%s marked_no_show=%s today=%s",
        result["checked"],
        result["auto_completed"],
        result["marked_no_show"],
        today.isoformat(),
    )
    return {
        **result,
        "marked": result["marked_no_show"],
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
