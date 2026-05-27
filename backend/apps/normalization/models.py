from django.db import models
from apps.tenants.models import Tenant
from apps.tenants.managers import TenantAwareManager
from apps.ingestion.models import Batch, RawRecord
import uuid

class NormalizedRecord(models.Model):
    PENDING_REVIEW = 'PENDING_REVIEW'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    LOCKED = 'LOCKED'
    SUPERSEDED = 'SUPERSEDED'

    STATUS_CHOICES = [
        (PENDING_REVIEW, 'Pending Review'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (LOCKED, 'Locked'),
        (SUPERSEDED, 'Superseded'),
    ]

    SCOPE_1 = 'SCOPE_1'
    SCOPE_2 = 'SCOPE_2'
    SCOPE_3 = 'SCOPE_3'

    SCOPE_CHOICES = [
        (SCOPE_1, 'Scope 1'),
        (SCOPE_2, 'Scope 2'),
        (SCOPE_3, 'Scope 3'),
    ]

    SOURCE_CHOICES = Batch.SOURCE_CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='normalized_records')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='normalized_records')
    raw_record = models.ForeignKey(RawRecord, on_delete=models.CASCADE, null=True, related_name='normalized_records')
    
    # Activity identity
    source_type = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    activity_type = models.CharField(max_length=100)
    # e.g., diesel_combustion, natural_gas, purchased_electricity, flight_economy, hotel_stay, car_rental
    
    scope = models.CharField(max_length=50, choices=SCOPE_CHOICES)

    # Quantities — always store both original and canonical
    quantity = models.DecimalField(max_digits=20, decimal_places=6)
    unit = models.CharField(max_length=50)  # original unit
    canonical_quantity = models.DecimalField(max_digits=20, decimal_places=6)
    canonical_unit = models.CharField(max_length=50)  # normalized unit

    # Temporal
    period_start = models.DateField()
    period_end = models.DateField()

    # Location / facility
    facility_id = models.CharField(max_length=255, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=3, blank=True)  # ISO 3166-1

    # Travel-specific
    origin_iata = models.CharField(max_length=10, blank=True)
    destination_iata = models.CharField(max_length=10, blank=True)
    distance_km = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    distance_inferred = models.BooleanField(default=False)

    # Provenance
    source_system = models.CharField(max_length=100)
    source_batch_ref = models.CharField(max_length=255, blank=True)
    ingest_timestamp = models.DateTimeField()
    parser_version = models.CharField(max_length=50)

    # Review state
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=PENDING_REVIEW)
    anomaly_flags = models.JSONField(default=list)
    # Each flag: {"code": "UNIT_UNCERTAINTY", "severity": "WARNING", "message": "...", "field": "unit"}

    # Edit tracking (if analyst corrects a value)
    is_edited = models.BooleanField(default=False)
    edit_history = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = TenantAwareManager()
    admin_objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'period_start', 'period_end']),
            models.Index(fields=['batch', 'status']),
        ]

    def __str__(self):
        return f"{self.activity_type} - {self.canonical_quantity} {self.canonical_unit} ({self.status})"

class ScopeMapping(models.Model):
    activity_type = models.CharField(max_length=100, unique=True)
    scope = models.CharField(max_length=50, choices=NormalizedRecord.SCOPE_CHOICES)

    def __str__(self):
        return f"{self.activity_type} -> {self.scope}"

