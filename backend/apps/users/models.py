from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.tenants.models import Tenant
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'PLATFORM_ADMIN')
        
        # Ensure a default tenant exists for the superuser
        tenant_slug = 'breathe-esg'
        tenant, _ = Tenant.objects.get_or_create(
            slug=tenant_slug,
            defaults={'name': 'Breathe Platform Admin'}
        )
        extra_fields['tenant'] = tenant
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ANALYST = 'ANALYST'
    TENANT_ADMIN = 'TENANT_ADMIN'
    PLATFORM_ADMIN = 'PLATFORM_ADMIN'
    
    ROLE_CHOICES = [
        (ANALYST, 'Analyst'),
        (TENANT_ADMIN, 'Tenant Admin'),
        (PLATFORM_ADMIN, 'Platform Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default=ANALYST)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for Django Admin
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return f"{self.email} ({self.role})"
