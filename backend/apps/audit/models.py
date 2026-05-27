from django.db import models
from apps.tenants.models import Tenant
from apps.tenants.managers import TenantAwareManager
from apps.ingestion.models import Batch
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='audit_logs')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=100)  # e.g., BATCH_LOCKED, RECORD_APPROVED, BATCH_INGESTED
    record_snapshot = models.JSONField(null=True, blank=True)  # Full state at lock time
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()
    admin_objects = models.Manager()

    class Meta:
        # This table is INSERT-only. Never update or delete.
        managed = True

    def __str__(self):
        return f"{self.action} - {self.timestamp}"
