from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0006_systemnotice_related_order"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aicalllog",
            name="error_message",
            field=models.TextField(blank=True),
        ),
    ]
