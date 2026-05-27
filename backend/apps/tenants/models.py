from django.db import models
import uuid

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class FacilityMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='facility_mappings')
    plant_code = models.CharField(max_length=100)
    facility_id = models.CharField(max_length=255)
    facility_name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=3, blank=True)

    class Meta:
        unique_together = ('tenant', 'plant_code')

    def __str__(self):
        return f"{self.plant_code} -> {self.facility_name} ({self.tenant.name})"
