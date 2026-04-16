import re

from django.db import migrations, models


def backfill_related_order(apps, schema_editor):
    SystemNotice = apps.get_model("operations", "SystemNotice")
    BookingOrder = apps.get_model("bookings", "BookingOrder")

    pattern = re.compile(r"订单(?:号)?[\s:：#]*([A-Za-z0-9_-]{6,64})", re.IGNORECASE)

    candidates = []
    queryset = (
        SystemNotice.objects
        .filter(related_order_id__isnull=True, notice_type__in=["order", "payment"])
        .only("id", "title", "content")
    )
    for notice in queryset.iterator():
        text = f"{notice.title or ''} {notice.content or ''}".strip()
        if not text:
            continue
        match = pattern.search(text)
        if not match:
            continue
        order_no = match.group(1).strip()
        if not order_no:
            continue
        candidates.append((notice.id, order_no))

    if not candidates:
        return

    order_nos = sorted({order_no for _, order_no in candidates})
    order_id_map = {
        order_no: order_id
        for order_no, order_id in BookingOrder.objects.filter(order_no__in=order_nos).values_list("order_no", "id")
    }

    for notice_id, order_no in candidates:
        order_id = order_id_map.get(order_no)
        if not order_id:
            continue
        SystemNotice.objects.filter(id=notice_id, related_order_id__isnull=True).update(related_order_id=order_id)


def reverse_backfill_related_order(apps, schema_editor):
    SystemNotice = apps.get_model("operations", "SystemNotice")
    SystemNotice.objects.filter(notice_type__in=["order", "payment"]).update(related_order_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0003_bookingorder_status_timestamps"),
        ("operations", "0005_runtime_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemnotice",
            name="related_order",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="system_notices", to="bookings.bookingorder"),
        ),
        migrations.RunPython(backfill_related_order, reverse_backfill_related_order),
    ]
