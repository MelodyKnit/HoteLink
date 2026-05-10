"""Add invoice request processing fields and immutable buyer snapshots."""

from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone
import django.db.models.deletion


def snapshot_existing_invoice_requests(apps, schema_editor):
    """Backfill historical invoice requests from their linked order and title."""
    invoice_request_model = apps.get_model("crm", "InvoiceRequest")

    for invoice_request in invoice_request_model.objects.select_related("invoice_title", "order").iterator():
        title = invoice_request.invoice_title
        order = invoice_request.order
        invoice_request.amount = getattr(order, "pay_amount", None) or Decimal("0.00")
        invoice_request.invoice_type_snapshot = getattr(title, "invoice_type", "") or "personal"
        invoice_request.title_snapshot = getattr(title, "title", "") or ""
        invoice_request.tax_no_snapshot = getattr(title, "tax_no", "") or ""
        invoice_request.email_snapshot = getattr(title, "email", "") or ""
        invoice_request.updated_at = timezone.now()
        invoice_request.save(
            update_fields=[
                "amount",
                "invoice_type_snapshot",
                "title_snapshot",
                "tax_no_snapshot",
                "email_snapshot",
                "updated_at",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("crm", "0009_alter_pointslog_balance"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoicerequest",
            name="amount",
            field=models.DecimalField(decimal_places=2, default=0, help_text="申请时订单可开票金额快照", max_digits=10),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="email_snapshot",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="invoice_code",
            field=models.CharField(blank=True, help_text="发票代码，数电票可为空", max_length=64),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="invoice_file_url",
            field=models.CharField(blank=True, help_text="电子发票文件或外部下载地址", max_length=500),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="invoice_no",
            field=models.CharField(blank=True, help_text="发票号码", max_length=64),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="invoice_type_snapshot",
            field=models.CharField(choices=[("personal", "个人发票"), ("company", "企业发票")], default="personal", max_length=20),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="issued_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="processed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="processor",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="processed_invoice_requests", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="processor_remark",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="tax_no_snapshot",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="title_snapshot",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="invoicerequest",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.RunPython(snapshot_existing_invoice_requests, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="invoicerequest",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddConstraint(
            model_name="invoicerequest",
            constraint=models.UniqueConstraint(fields=("order",), name="uniq_invoice_request_order"),
        ),
    ]
