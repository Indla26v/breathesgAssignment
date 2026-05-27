from django.db import models
from apps.tenants.models import Tenant
from apps.tenants.managers import TenantAwareManager
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Batch(models.Model):
    QUEUED = 'QUEUED'
    INGESTING = 'INGESTING'
    NORMALIZING = 'NORMALIZING'
    PENDING_REVIEW = 'PENDING_REVIEW'
    PARTIAL_FAILURE = 'PARTIAL_FAILURE'
    APPROVED = 'APPROVED'
    LOCKED = 'LOCKED'
    FAILED = 'FAILED'

    STATUS_CHOICES = [
        (QUEUED, 'Queued'),
        (INGESTING, 'Ingesting'),
        (NORMALIZING, 'Normalizing'),
        (PENDING_REVIEW, 'Pending Review'),
        (PARTIAL_FAILURE, 'Partial Failure'),
        (APPROVED, 'Approved'),
        (LOCKED, 'Locked'),
        (FAILED, 'Failed'),
    ]

    SAP = 'SAP'
    UTILITY = 'UTILITY'
    TRAVEL = 'TRAVEL'

    SOURCE_CHOICES = [
        (SAP, 'SAP Fuel & Procurement'),
        (UTILITY, 'Utility / Electricity'),
        (TRAVEL, 'Corporate Travel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='batches')
    source_type = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=QUEUED)
    original_filename = models.CharField(max_length=500)
    file_ref = models.CharField(max_length=1000)  # S3 or local storage path
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_batches')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    record_count = models.IntegerField(null=True)
    flagged_count = models.IntegerField(null=True)
    approved_count = models.IntegerField(null=True)
    error_message = models.TextField(blank=True)
    parser_version = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict)  # Source-specific config used

    # Multi-tenancy isolation manager
    objects = TenantAwareManager()

    # Plain django manager for celery/internal usage bypassing middleware filters
    admin_objects = models.Manager()

    def __str__(self):
        return f"{self.original_filename} ({self.source_type} - {self.status})"

class RawRecord(models.Model):
    OK = 'OK'
    PARSE_ERROR = 'PARSE_ERROR'
    SKIPPED = 'SKIPPED'

    PARSE_STATUS_CHOICES = [
        (OK, 'Ok'),
        (PARSE_ERROR, 'Parse Error'),
        (SKIPPED, 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='raw_records')
    row_index = models.IntegerField()
    raw_payload = models.JSONField()  # Entire original row as parsed
    parse_status = models.CharField(max_length=50, choices=PARSE_STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('batch', 'row_index')

    def __str__(self):
        return f"RawRecord {self.row_index} for Batch {self.batch.id}"
