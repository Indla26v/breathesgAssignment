from rest_framework import serializers
from apps.review.models import ApprovalEvent

class ApprovalEventSerializer(serializers.ModelSerializer):
    analyst_name = serializers.CharField(source='analyst.full_name', read_only=True)
    analyst_email = serializers.EmailField(source='analyst.email', read_only=True)

    class Meta:
        model = ApprovalEvent
        fields = [
            'id', 'record', 'analyst', 'analyst_name', 'analyst_email',
            'action', 'note', 'previous_value', 'timestamp'
        ]
        read_only_fields = ['id', 'analyst', 'timestamp']
