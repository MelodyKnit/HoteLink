from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_coupontemplate_usercoupon_coupon_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='images',
            field=models.JSONField(blank=True, default=list, help_text='评价图片URL列表'),
        ),
    ]
