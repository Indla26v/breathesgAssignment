from rest_framework import serializers
from apps.ingestion.models import Batch, RawRecord
from django.contrib.auth import get_user_model

User = get_user_model()

class BatchSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)

    class Meta:
        model = Batch
        fields = [
            'id', 'source_type', 'status', 'original_filename', 
            'file_ref', 'uploaded_by', 'uploaded_by_email', 'uploaded_by_name',
            'uploaded_at', 'record_count', 'flagged_count', 'approved_count',
            'error_message', 'parser_version', 'metadata'
        ]
        read_only_fields = [
            'id', 'status', 'uploaded_by', 'uploaded_at', 
            'record_count', 'flagged_count', 'approved_count', 
            'error_message', 'parser_version'
        ]

class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ['id', 'batch', 'row_index', 'raw_payload', 'parse_status', 'error_message', 'created_at']
        read_only_fields = ['id', 'batch', 'row_index', 'created_at']
