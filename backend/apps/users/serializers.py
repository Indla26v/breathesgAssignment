from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'tenant', 'tenant_name', 'tenant_slug', 'created_at']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims for tenant isolation and roles
        token['tenant_id'] = str(user.tenant.id)
        token['role'] = user.role
        token['email'] = user.email
        return token
