from rest_framework import serializers
from apps.audit.models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source='actor.email', read_only=True)
    actor_name = serializers.CharField(source='actor.full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'tenant', 'batch', 'actor', 'actor_email', 'actor_name',
            'action', 'record_snapshot', 'metadata', 'timestamp'
        ]
        read_only_fields = [
            'id', 'tenant', 'batch', 'actor', 'actor_email', 'actor_name',
            'action', 'record_snapshot', 'metadata', 'timestamp'
        ]
