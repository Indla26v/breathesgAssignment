import traceback
from decimal import Decimal
import pandas as pd
from django.core.files.storage import default_storage
from django.utils import timezone
from celery import shared_task
from apps.ingestion.models import Batch, RawRecord
from apps.normalization.models import NormalizedRecord
from apps.normalization.converters import convert_unit
from apps.normalization.classifiers import classify_scope
from apps.normalization.anomaly import detect_anomalies
from apps.audit.models import AuditLog
from apps.tenants.middleware import set_current_tenant, set_bypass_tenant_filter
from apps.ingestion.parsers.sap import SAPParser
from apps.ingestion.parsers.utility import UtilityParser
from apps.ingestion.parsers.travel import TravelParser
import logging
import json

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def ingest_and_normalize(self, batch_id):
    """
    Celery task that downloads a batch file, parses it, registers RawRecord rows,
    normalizes it, runs anomaly checks, and commits NormalizedRecord rows.
    """
    logger.info("Starting ingestion and normalization for batch: %s", batch_id)
    
    # 1. Retrieve the Batch bypassing middleware tenant scoping
    set_bypass_tenant_filter(True)
    try:
        batch = Batch.admin_objects.get(id=batch_id)
    except Batch.DoesNotExist:
        logger.error("Batch with ID %s does not exist", batch_id)
        return
        
    set_current_tenant(batch.tenant)

    # Log start with structured context
    logger.info(
        json.dumps({
            "message": "Task started",
            "batch_id": str(batch.id),
            "tenant_id": str(batch.tenant.id),
            "source_type": batch.source_type
        })
    )

    batch.status = Batch.INGESTING
    batch.save()

    parser = None
    try:
        # 2. Open the file from Django's default storage (supports S3 and local storage)
        with default_storage.open(batch.file_ref, 'r') as file_obj:
            # 3. Instantiate the correct parser
            if batch.source_type == Batch.SAP:
                parser = SAPParser(file_obj, tenant=batch.tenant, metadata=batch.metadata)
            elif batch.source_type == Batch.UTILITY:
                parser = UtilityParser(file_obj, tenant=batch.tenant, metadata=batch.metadata)
            elif batch.source_type == Batch.TRAVEL:
                parser = TravelParser(file_obj, tenant=batch.tenant, metadata=batch.metadata)
            else:
                raise ValueError(f"Unsupported source type: {batch.source_type}")

            # 4. Stream-parse the file row by row
            raw_records = []
            parsed_rows = []
            seen_indices = set()
            
            for parsed_row in parser.parse():
                row_idx = parsed_row["row_index"]
                
                # Check if we already created a RawRecord for this row (e.g. on split utility periods)
                if row_idx not in seen_indices:
                    raw_rec = RawRecord(
                        batch=batch,
                        row_index=row_idx,
                        raw_payload=parsed_row["raw_payload"],
                        parse_status=parsed_row["parse_status"],
                        error_message=parsed_row["error_message"]
                    )
                    raw_records.append(raw_rec)
                    seen_indices.add(row_idx)
                
                # If parse was successful, retain the parsed metadata/activity_data for normalization
                if parsed_row["parse_status"] == RawRecord.OK:
                    parsed_rows.append((row_idx, parsed_row["activity_data"]))

                # Bulk insert RawRecord instances in chunks of 500
                if len(raw_records) >= 500:
                    RawRecord.objects.bulk_create(raw_records)
                    raw_records = []
                    
            if raw_records:
                RawRecord.objects.bulk_create(raw_records)

        # Set parser version in Batch
        batch.parser_version = getattr(parser, 'VERSION', '1.0.0')
        batch.save()

        total_parsed = len(RawRecord.objects.filter(batch=batch))
        ok_parsed = len(RawRecord.objects.filter(batch=batch, parse_status=RawRecord.OK))
        failed_parsed = total_parsed - ok_parsed

        logger.info("Parsed %d rows, OK: %d, FAILED: %d", total_parsed, ok_parsed, failed_parsed)

        # 5. Check if 100% of rows failed parsing
        if total_parsed > 0 and ok_parsed == 0:
            raise ValueError(f"All {total_parsed} rows failed parsing. Batch cannot be processed.")
        elif total_parsed == 0:
            raise ValueError("No rows found in the uploaded file.")

        # 6. Begin Normalization Step
        batch.status = Batch.NORMALIZING
        batch.save()

        normalized_records = []
        
        # Pull matching raw records to link them (since bulk_create didn't set ids on the objects in memory)
        raw_db_records = {r.row_index: r for r in RawRecord.objects.filter(batch=batch)}

        for row_idx, act_data in parsed_rows:
            # Re-associate with database record (which now has an ID)
            raw_db_rec = raw_db_records[row_idx]
            
            # Extract fields
            quantity = act_data["quantity"]
            unit = act_data["unit"]
            activity_type = act_data["activity_type"]
            scope = act_data["scope"]
            period_start = act_data["period_start"]
            period_end = act_data["period_end"]
            facility_id = act_data.get("facility_id", "")
            facility_name = act_data.get("facility_name", "")
            country_code = act_data.get("country_code", "")
            
            # Step 1: Unit Converter
            canonical_qty, canonical_unit, conv_flag = convert_unit(quantity, unit, activity_type)
            
            # Step 2: Scope Classifier (redundancy lookup/validation)
            classified_scope = classify_scope(activity_type, batch.source_type)
            
            # Step 4: Provenance Recorder fields
            source_system = f"{batch.source_type}_PARSER"
            source_batch_ref = str(batch.id)
            ingest_timestamp = timezone.now()
            parser_version = getattr(parser, 'VERSION', '1.0.0')

            # Build NormalizedRecord instance pre-save
            norm_rec = NormalizedRecord(
                tenant=batch.tenant,
                batch=batch,
                raw_record=raw_db_rec,
                source_type=batch.source_type,
                activity_type=activity_type,
                scope=classified_scope,
                quantity=quantity,
                unit=unit,
                canonical_quantity=canonical_qty,
                canonical_unit=canonical_unit,
                period_start=period_start,
                period_end=period_end,
                facility_id=facility_id,
                facility_name=facility_name,
                country_code=country_code,
                origin_iata=act_data.get("origin_iata", ""),
                destination_iata=act_data.get("destination_iata", ""),
                distance_km=act_data.get("distance_km"),
                distance_inferred=act_data.get("distance_inferred", False),
                source_system=source_system,
                source_batch_ref=source_batch_ref,
                ingest_timestamp=ingest_timestamp,
                parser_version=parser_version,
                status=NormalizedRecord.PENDING_REVIEW,
                anomaly_flags=[]
            )

            # Step 3: Anomaly Detector (checks duplicate ranges, 3sigma, zero values, future dates)
            # Inject unit converter flags into the raw payload to let anomaly detector read it
            if conv_flag:
                raw_db_rec.raw_payload['_metadata'] = raw_db_rec.raw_payload.get('_metadata', {})
                raw_db_rec.raw_payload['_metadata']['unit_conversion_failed'] = True
            
            # Also inject the billing split flag if any
            if act_data.get("metadata", {}).get("_metadata", {}).get("billing_period_split"):
                raw_db_rec.raw_payload['_metadata'] = raw_db_rec.raw_payload.get('_metadata', {})
                raw_db_rec.raw_payload['_metadata']['billing_period_split'] = True

            norm_rec.anomaly_flags = detect_anomalies(norm_rec)
            normalized_records.append(norm_rec)

            if len(normalized_records) >= 500:
                NormalizedRecord.objects.bulk_create(normalized_records)
                normalized_records = []

        if normalized_records:
            NormalizedRecord.objects.bulk_create(normalized_records)

        # 7. Update Batch stats
        record_count = NormalizedRecord.objects.filter(batch=batch).count()
        # count how many records have at least one anomaly flag
        flagged_count = 0
        for nr in NormalizedRecord.objects.filter(batch=batch):
            if nr.anomaly_flags:
                flagged_count += 1
                
        batch.record_count = record_count
        batch.flagged_count = flagged_count
        batch.approved_count = 0

        # If more than 50% of the raw rows failed parsing, mark batch as PARTIAL_FAILURE
        if total_parsed > 0 and (failed_parsed / total_parsed) > 0.5:
            batch.status = Batch.PARTIAL_FAILURE
        else:
            batch.status = Batch.PENDING_REVIEW
            
        batch.save()

        # Audit logging: BATCH_INGESTED
        AuditLog.admin_objects.create(
            tenant=batch.tenant,
            batch=batch,
            actor=batch.uploaded_by,
            action="BATCH_INGESTED",
            metadata={
                "record_count": record_count,
                "flagged_count": flagged_count,
                "status": batch.status
            }
        )

        logger.info(
            json.dumps({
                "message": "Task completed successfully",
                "batch_id": str(batch.id),
                "record_count": record_count,
                "flagged_count": flagged_count
            })
        )

    except Exception as exc:
        # Traceback summary
        tb_str = traceback.format_exc()
        logger.error("Error ingesting batch %s: %s", batch_id, tb_str)
        
        # Set Batch as failed
        batch.status = Batch.FAILED
        batch.error_message = tb_str.split('\n')[-2] or "Unknown ingestion error"
        batch.save()
        
        # Audit logging: BATCH_FAILED
        AuditLog.admin_objects.create(
            tenant=batch.tenant,
            batch=batch,
            actor=batch.uploaded_by,
            action="BATCH_FAILED",
            metadata={"error": batch.error_message}
        )
        
        # Celery retries (only for transient errors, e.g. S3 connectivity. Not for parse errors)
        # Check if it was a ValueError (usually programmer/file format error) or other exceptions
        is_transient = not isinstance(exc, (ValueError, KeyError, TypeError, pd.errors.EmptyDataError))
        
        if is_transient and self.request.retries < self.max_retries:
            logger.info("Retrying batch ingestion due to transient error...")
            # Set batch status back to QUEUED for retry
            batch.status = Batch.QUEUED
            batch.save()
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        logger.info(
            json.dumps({
                "message": "Task failed permanently",
                "batch_id": str(batch.id),
                "error": str(exc)
            })
        )
