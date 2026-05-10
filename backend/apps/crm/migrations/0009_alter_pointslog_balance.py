"""Align points log balance help text with split point balances."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0008_pointslog_point_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pointslog",
            name="balance",
            field=models.PositiveIntegerField(help_text="变动后对应类型积分余额"),
        ),
    ]
