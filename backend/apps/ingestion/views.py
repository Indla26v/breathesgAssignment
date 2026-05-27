from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.db import transaction
from apps.ingestion.models import Batch, RawRecord
from apps.ingestion.serializers import BatchSerializer
from apps.normalization.models import NormalizedRecord
from apps.users.permissions import IsAnalyst
from apps.ingestion.tasks import ingest_and_normalize
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class BatchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAnalyst]
    serializer_class = BatchSerializer

    def get_queryset(self):
        # TenantAwareManager automatically filters by the current request's tenant
        queryset = Batch.objects.all().order_by('-uploaded_at')
        
        status_param = self.request.query_params.get('status')
        source_param = self.request.query_params.get('source_type')
        
        if status_param:
            queryset = queryset.filter(status=status_param)
        if source_param:
            queryset = queryset.filter(source_type=source_param)
            
        return queryset

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        source_type = request.data.get('source_type')
        metadata_raw = request.data.get('metadata', '{}')

        if not uploaded_file:
            return Response({
                "errors": [{"code": "VALIDATION_ERROR", "field": "file", "message": "No file was uploaded."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        if source_type not in [Batch.SAP, Batch.UTILITY, Batch.TRAVEL]:
            return Response({
                "errors": [{"code": "VALIDATION_ERROR", "field": "source_type", "message": f"Invalid source type: '{source_type}'."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            metadata = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw
        except Exception:
            return Response({
                "errors": [{"code": "VALIDATION_ERROR", "field": "metadata", "message": "Metadata must be valid JSON."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 1. Save uploaded file to S3/local media storage
        # Generate a unique path to avoid collisions
        unique_id = uuid.uuid4()
        storage_path = f"batches/{request.tenant.id}/{unique_id}_{uploaded_file.name}"
        
        try:
            file_name = default_storage.save(storage_path, uploaded_file)
        except Exception as e:
            logger.error("Failed to write file to storage: %s", str(e))
            return Response({
                "errors": [{"code": "STORAGE_ERROR", "field": None, "message": "Failed to save file to object storage."}],
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Register Batch record in DB
        with transaction.atomic():
            batch = Batch.objects.create(
                tenant=request.tenant,
                source_type=source_type,
                status=Batch.QUEUED,
                original_filename=uploaded_file.name,
                file_ref=file_name,
                uploaded_by=request.user,
                metadata=metadata,
                parser_version="1.0.0"
            )

        # 3. Trigger async Celery ingestion
        celery_task = ingest_and_normalize.delay(str(batch.id))

        serializer = self.get_serializer(batch)
        response_data = serializer.data
        response_data['task_id'] = celery_task.id

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='status')
    def status_polling(self, request, pk=None):
        """Lightweight endpoint for polling ingestion progress."""
        batch = self.get_object()
        return Response({
            "id": str(batch.id),
            "status": batch.status,
            "record_count": batch.record_count,
            "flagged_count": batch.flagged_count,
            "error_message": batch.error_message
        })

    @action(detail=True, methods=['get'], url_path='records')
    def get_records(self, request, pk=None):
        """Returns NormalizedRecords for this batch with filtering."""
        batch = self.get_object()
        # Fetch records. Using import here to avoid circular dependencies
        from apps.normalization.serializers import NormalizedRecordSerializer
        
        records = NormalizedRecord.objects.filter(batch=batch).order_by('created_at')
        
        status_param = request.query_params.get('status')
        scope_param = request.query_params.get('scope')
        has_flags = request.query_params.get('has_flags')

        if status_param:
            records = records.filter(status=status_param)
        if scope_param:
            records = records.filter(scope=scope_param)
        if has_flags:
            if has_flags.lower() == 'true':
                records = records.exclude(anomaly_flags=[])
            elif has_flags.lower() == 'false':
                records = records.filter(anomaly_flags=[])

        # Pagination using DRF standard paginator
        page = self.paginate_queryset(records)
        if page is not None:
            serializer = NormalizedRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NormalizedRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='sign-off')
    def sign_off(self, request, pk=None):
        batch = self.get_object()
        from apps.audit.models import AuditLog
        from apps.normalization.serializers import NormalizedRecordSerializer

        # 1. Validate that all records are reviewed (none in PENDING_REVIEW)
        pending_count = NormalizedRecord.objects.filter(batch=batch, status=NormalizedRecord.PENDING_REVIEW).count()
        if pending_count > 0:
            return Response({
                "errors": [{
                    "code": "PENDING_RECORDS",
                    "field": None,
                    "message": f"Cannot sign off batch. There are still {pending_count} records pending review."
                }],
                "data": None
            }, status=status.HTTP_409_CONFLICT)

        # 2. Retrieve approved records
        approved_records = NormalizedRecord.objects.filter(batch=batch, status=NormalizedRecord.APPROVED)
        
        with transaction.atomic():
            # 3. Transition APPROVED records -> LOCKED
            for record in approved_records:
                record.status = NormalizedRecord.LOCKED
                record.save()
                
                # Write individual record snapshot to insert-only AuditLog
                snapshot = NormalizedRecordSerializer(record).data
                AuditLog.objects.create(
                    tenant=batch.tenant,
                    batch=batch,
                    actor=request.user,
                    action="RECORD_LOCKED",
                    record_snapshot=snapshot,
                    metadata={"original_status": "APPROVED"}
                )
                
            # Lock the batch itself
            batch.status = Batch.LOCKED
            # Recalculate and update approved count
            batch.approved_count = approved_records.count()
            batch.save()
            
            # Write BATCH_LOCKED to AuditLog
            AuditLog.objects.create(
                tenant=batch.tenant,
                batch=batch,
                actor=request.user,
                action="BATCH_LOCKED",
                record_snapshot=None,
                metadata={
                    "record_count": batch.record_count,
                    "approved_count": batch.approved_count,
                    "flagged_count": batch.flagged_count
                }
            )
            
        return Response({
            "data": {
                "message": "Batch signed off and locked successfully."
            },
            "errors": []
        })

    @action(detail=True, methods=['get'], url_path='audit-log')
    def get_audit_log(self, request, pk=None):
        """Returns read-only audit trail for the batch."""
        batch = self.get_object()
        from apps.audit.models import AuditLog
        from apps.audit.serializers import AuditLogSerializer

        logs = AuditLog.objects.filter(batch=batch).order_by('timestamp')
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
