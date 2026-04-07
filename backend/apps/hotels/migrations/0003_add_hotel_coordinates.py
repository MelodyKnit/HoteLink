from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hotels", "0002_add_hotel_images_and_room_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="hotel",
            name="latitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="hotel",
            name="longitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
