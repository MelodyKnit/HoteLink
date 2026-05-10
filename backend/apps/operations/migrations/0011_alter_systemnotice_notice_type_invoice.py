"""Add invoice notice type for invoice processing results."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0010_aicalllog_idx_aicalllog_scene_created_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="systemnotice",
            name="notice_type",
            field=models.CharField(
                choices=[
                    ("order", "订单通知"),
                    ("payment", "支付通知"),
                    ("activity", "活动通知"),
                    ("system", "系统通知"),
                    ("review", "评价通知"),
                    ("member", "会员通知"),
                    ("coupon", "优惠券通知"),
                    ("invoice", "发票通知"),
                ],
                default="system",
                max_length=20,
            ),
        ),
    ]
