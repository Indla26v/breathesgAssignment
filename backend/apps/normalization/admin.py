from django.contrib import admin
from apps.normalization.models import NormalizedRecord, ScopeMapping

@admin.register(ScopeMapping)
class ScopeMappingAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'scope')
    list_filter = ('scope',)
    search_fields = ('activity_type',)

@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'scope', 'canonical_quantity', 'canonical_unit', 'status', 'tenant')
    list_filter = ('scope', 'status', 'tenant', 'source_type')
    search_fields = ('activity_type', 'facility_id', 'facility_name')
