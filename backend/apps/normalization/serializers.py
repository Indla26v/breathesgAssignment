from rest_framework import serializers
from apps.normalization.models import NormalizedRecord

class NormalizedRecordSerializer(serializers.ModelSerializer):
    raw_payload = serializers.JSONField(source='raw_record.raw_payload', read_only=True)
    parse_error = serializers.CharField(source='raw_record.error_message', read_only=True)
    batch_filename = serializers.CharField(source='batch.original_filename', read_only=True)
    approval_events = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'tenant', 'batch', 'batch_filename', 'raw_record', 'raw_payload', 'parse_error',
            'source_type', 'activity_type', 'scope', 'quantity', 'unit',
            'canonical_quantity', 'canonical_unit', 'period_start', 'period_end',
            'facility_id', 'facility_name', 'country_code',
            'origin_iata', 'destination_iata', 'distance_km', 'distance_inferred',
            'source_system', 'source_batch_ref', 'ingest_timestamp', 'parser_version',
            'status', 'anomaly_flags', 'is_edited', 'edit_history', 'approval_events',
            'created_at', 'updated_at'
        ]

    def get_approval_events(self, obj):
        from apps.review.serializers import ApprovalEventSerializer
        events = obj.approval_events.all().order_by('timestamp')
        return ApprovalEventSerializer(events, many=True).data
        read_only_fields = [
            'id', 'tenant', 'batch', 'raw_record', 'source_type', 'activity_type', 'scope',
            'canonical_quantity', 'canonical_unit', 'period_start', 'period_end',
            'facility_id', 'facility_name', 'country_code',
            'origin_iata', 'destination_iata', 'distance_km', 'distance_inferred',
            'source_system', 'source_batch_ref', 'ingest_timestamp', 'parser_version',
            'anomaly_flags', 'is_edited', 'edit_history', 'created_at', 'updated_at'
        ]
