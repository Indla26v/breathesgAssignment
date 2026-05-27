from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from apps.normalization.models import NormalizedRecord
from apps.normalization.serializers import NormalizedRecordSerializer
from apps.normalization.converters import convert_unit
from apps.normalization.anomaly import detect_anomalies
from apps.review.models import ApprovalEvent
from apps.users.permissions import IsAnalyst
from apps.ingestion.models import Batch
import logging

logger = logging.getLogger(__name__)

class NormalizedRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAnalyst]
    serializer_class = NormalizedRecordSerializer

    def get_queryset(self):
        # TenantAwareManager automatically filters by current tenant
        queryset = NormalizedRecord.objects.all().order_by('-created_at')
        
        status_param = self.request.query_params.get('status')
        scope_param = self.request.query_params.get('scope')
        has_flags = self.request.query_params.get('has_flags')
        
        if status_param:
            queryset = queryset.filter(status=status_param)
        if scope_param:
            queryset = queryset.filter(scope=scope_param)
        if has_flags:
            if has_flags.lower() == 'true':
                queryset = queryset.exclude(anomaly_flags=[])
            elif has_flags.lower() == 'false':
                queryset = queryset.filter(anomaly_flags=[])
                
        return queryset

    def partial_update(self, request, *args, **kwargs):
        record = self.get_object()
        
        # 1. Enforce audit-lock immutability
        if record.status == NormalizedRecord.LOCKED:
            return Response({
                "errors": [{"code": "LOCKED_RECORD", "field": None, "message": "Immutable audit trail. Locked records cannot be edited."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        quantity_str = request.data.get('quantity')
        unit = request.data.get('unit')
        note = request.data.get('note', '')

        if not note:
            return Response({
                "errors": [{"code": "VALIDATION_ERROR", "field": "note", "message": "A change note is required to edit values."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build change snapshot
        previous_val = {
            "quantity": str(record.quantity),
            "unit": record.unit,
            "canonical_quantity": str(record.canonical_quantity),
            "canonical_unit": record.canonical_unit
        }

        with transaction.atomic():
            if quantity_str is not None:
                try:
                    record.quantity = Decimal(str(quantity_str))
                except Exception:
                    return Response({
                        "errors": [{"code": "VALIDATION_ERROR", "field": "quantity", "message": "Invalid quantity format."}],
                        "data": None
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            if unit is not None:
                record.unit = str(unit)

            # Re-run unit conversion
            canonical_qty, canonical_unit, conv_flag = convert_unit(record.quantity, record.unit, record.activity_type)
            record.canonical_quantity = canonical_qty
            record.canonical_unit = canonical_unit

            # Track edit history
            record.is_edited = True
            if not isinstance(record.edit_history, list):
                record.edit_history = []
                
            record.edit_history.append({
                "timestamp": timezone.now().isoformat(),
                "analyst": request.user.email,
                "note": note,
                "previous": previous_val
            })

            # Re-run anomaly detection rules to clear out corrected flags
            record.anomaly_flags = detect_anomalies(record)
            record.save()

            # Record ApprovalEvent
            ApprovalEvent.objects.create(
                record=record,
                analyst=request.user,
                action=ApprovalEvent.EDITED,
                note=note,
                previous_value=previous_val
            )

        serializer = self.get_serializer(record)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        record = self.get_object()
        
        if record.status == NormalizedRecord.LOCKED:
            return Response({
                "errors": [{"code": "LOCKED_RECORD", "field": None, "message": "Locked records cannot be approved."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            record.status = NormalizedRecord.APPROVED
            record.save()
            
            ApprovalEvent.objects.create(
                record=record,
                analyst=request.user,
                action=ApprovalEvent.APPROVED,
                note=request.data.get('note', '')
            )

            # Update batch stats (approved count)
            batch = record.batch
            batch.approved_count = NormalizedRecord.objects.filter(batch=batch, status=NormalizedRecord.APPROVED).count()
            batch.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        record = self.get_object()
        
        if record.status == NormalizedRecord.LOCKED:
            return Response({
                "errors": [{"code": "LOCKED_RECORD", "field": None, "message": "Locked records cannot be rejected."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        note = request.data.get('note', '')
        if not note:
            return Response({
                "errors": [{"code": "VALIDATION_ERROR", "field": "note", "message": "A rejection note is required."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            record.status = NormalizedRecord.REJECTED
            record.save()
            
            ApprovalEvent.objects.create(
                record=record,
                analyst=request.user,
                action=ApprovalEvent.REJECTED,
                note=note
            )

            # Update batch stats
            batch = record.batch
            batch.approved_count = NormalizedRecord.objects.filter(batch=batch, status=NormalizedRecord.APPROVED).count()
            batch.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        record = self.get_object()
        
        if record.status == NormalizedRecord.LOCKED:
            return Response({
                "errors": [{"code": "LOCKED_RECORD", "field": None, "message": "Locked records cannot be flagged."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        note = request.data.get('note', '')
        if not note:
            return Response({
                "errors": [{"code": "VALIDATION_ERROR", "field": "note", "message": "A note explaining the flag is required."}],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            record.status = NormalizedRecord.PENDING_REVIEW
            record.save()
            
            ApprovalEvent.objects.create(
                record=record,
                analyst=request.user,
                action=ApprovalEvent.FLAGGED,
                note=note
            )

        serializer = self.get_serializer(record)
        return Response(serializer.data)

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAnalyst]

    def get(self, request):
        # Gather stats scoped by current tenant
        batches = Batch.objects.all()
        records = NormalizedRecord.objects.all()

        pending_batches = batches.filter(status__in=[
            Batch.QUEUED, Batch.INGESTING, Batch.NORMALIZING, 
            Batch.PENDING_REVIEW, Batch.PARTIAL_FAILURE
        ]).count()

        records_awaiting_review = records.filter(status=NormalizedRecord.PENDING_REVIEW).count()
        
        # Count records that are pending and have non-empty anomaly flags
        flagged_records = 0
        for rec in records.filter(status=NormalizedRecord.PENDING_REVIEW):
            if rec.anomaly_flags:
                flagged_records += 1

        locked_records = records.filter(status=NormalizedRecord.LOCKED).count()

        # Scope Breakdown
        scope_1_count = records.filter(scope=NormalizedRecord.SCOPE_1).count()
        scope_2_count = records.filter(scope=NormalizedRecord.SCOPE_2).count()
        scope_3_count = records.filter(scope=NormalizedRecord.SCOPE_3).count()

        # Source Breakdown
        sap_count = records.filter(source_type=Batch.SAP).count()
        utility_count = records.filter(source_type=Batch.UTILITY).count()
        travel_count = records.filter(source_type=Batch.TRAVEL).count()

        return Response({
            "pending_batches": pending_batches,
            "records_awaiting_review": records_awaiting_review,
            "flagged_records": flagged_records,
            "locked_records": locked_records,
            "by_scope": {
                "scope_1": scope_1_count,
                "scope_2": scope_2_count,
                "scope_3": scope_3_count
            },
            "by_source": {
                "sap": sap_count,
                "utility": utility_count,
                "travel": travel_count
            }
        })
