from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'role', 'tenant', 'is_active', 'is_staff')
    list_filter = ('role', 'tenant', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
