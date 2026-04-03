from django.db import models


class ReportSnapshot(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Report Snapshot"
        verbose_name_plural = "Report Snapshots"

    def __str__(self) -> str:
        return self.name
