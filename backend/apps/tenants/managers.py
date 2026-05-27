from django.db import models
from apps.tenants.middleware import get_current_tenant, get_bypass_tenant_filter

class TenantAwareQuerySet(models.QuerySet):
    def filter_by_tenant(self):
        if get_bypass_tenant_filter():
            return self
        tenant = get_current_tenant()
        if tenant is not None:
            return self.filter(tenant=tenant)
        # Return empty or filter by None if no tenant is set
        return self.filter(tenant=None)

class TenantAwareManager(models.Manager):
    def get_queryset(self):
        # Automatically apply the tenant filter to all queries
        return TenantAwareQuerySet(self.model, using=self._db).filter_by_tenant()
