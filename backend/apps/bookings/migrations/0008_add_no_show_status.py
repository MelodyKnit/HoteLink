"""Add no-show lifecycle state to booking orders."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0007_bookingorder_member_points_earned"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookingorder",
            name="no_show_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="bookingorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending_payment", "待支付"),
                    ("paid", "已支付"),
                    ("confirmed", "已确认"),
                    ("checked_in", "已入住"),
                    ("completed", "已完成"),
                    ("no_show", "未入住"),
                    ("cancelled", "已取消"),
                    ("refunding", "退款中"),
                    ("refunded", "已退款"),
                ],
                db_index=True,
                default="pending_payment",
                max_length=32,
            ),
        ),
    ]
