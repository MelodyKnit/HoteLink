"""apps/reports/models.py —— 报表任务模型。"""

from django.db import models


class ReportTask(models.Model):
    """报表任务模型，记录统计范围与执行状态。"""
    TYPE_REVENUE_SUMMARY = "revenue_summary"
    TYPE_ORDER_SUMMARY = "order_summary"
    TYPE_REVIEW_SUMMARY = "review_summary"
    TYPE_CHOICES = [
        (TYPE_REVENUE_SUMMARY, "营收报表"),
        (TYPE_ORDER_SUMMARY, "订单报表"),
        (TYPE_REVIEW_SUMMARY, "评价报表"),
    ]

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "待处理"),
        (STATUS_RUNNING, "执行中"),
        (STATUS_SUCCESS, "成功"),
        (STATUS_FAILED, "失败"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, null=True, blank=True, related_name="report_tasks")
    report_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default=TYPE_REVENUE_SUMMARY)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    result_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Report Task"
        verbose_name_plural = "Report Tasks"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.report_type}-{self.id}"
