import numpy as np
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.normalization.models import NormalizedRecord
from apps.tenants.models import FacilityMapping
import logging

logger = logging.getLogger(__name__)

def detect_anomalies(record):
    """
    Runs anomaly detection checks on a NormalizedRecord.
    Returns a list of flag dicts, e.g.:
    {
        "code": "ZERO_VALUE",
        "severity": "WARNING",
        "message": "...",
        "field": "canonical_quantity"
    }
    """
    flags = []
    
    # Pre-fetch variables
    quantity = record.canonical_quantity
    unit = record.canonical_unit
    start = record.period_start
    end = record.period_end
    facility_id = record.facility_id
    activity_type = record.activity_type
    tenant = record.tenant
    
    # 1. ZERO_VALUE
    if quantity == 0:
        flags.append({
            "code": "ZERO_VALUE",
            "severity": "WARNING",
            "message": "Canonical quantity is zero.",
            "field": "canonical_quantity"
        })
        
    # 2. NEGATIVE_VALUE
    # Ignore for solar net metering
    is_solar = "solar" in activity_type.lower() or "net_meter" in activity_type.lower()
    if quantity < 0 and not is_solar:
        flags.append({
            "code": "NEGATIVE_VALUE",
            "severity": "ERROR",
            "message": "Negative quantity detected for non-solar activity.",
            "field": "canonical_quantity"
        })
        
    # 3. MISSING_PERIOD
    if start is None or end is None:
        flags.append({
            "code": "MISSING_PERIOD",
            "severity": "ERROR",
            "message": "Billing or activity period start/end date is missing.",
            "field": "period_start"
        })
        
    # 4. FUTURE_DATE
    today = date.today()
    if end and end > today:
        flags.append({
            "code": "FUTURE_DATE",
            "severity": "ERROR",
            "message": f"Activity period end date ({end}) is in the future.",
            "field": "period_end"
        })
        
    # 5. UNKNOWN_FACILITY
    # If it's an SAP or UTILITY record, verify if the facility_id exists in FacilityMapping
    if record.source_type in ['SAP', 'UTILITY'] and facility_id:
        try:
            mapping_exists = FacilityMapping.objects.filter(
                tenant=tenant, 
                plant_code=facility_id
            ).exists()
            if not mapping_exists:
                # Also check if it matches mapped facility_id
                mapping_exists_2 = FacilityMapping.objects.filter(
                    tenant=tenant,
                    facility_id=facility_id
                ).exists()
                if not mapping_exists_2:
                    flags.append({
                        "code": "UNKNOWN_FACILITY",
                        "severity": "WARNING",
                        "message": f"Facility ID '{facility_id}' is not mapped to any known facility.",
                        "field": "facility_id"
                    })
        except Exception as e:
            logger.error("Error checking facility mapping: %s", str(e))
            
    # 6. UNIT_UNCERTAINTY
    # Checked during unit conversion. If conversion yielded unit uncertainty.
    # We can pass the conversion_flag to the detector or check if the record unit is flagged
    if record.unit == 'unknown' or record.canonical_unit == 'unknown':
        flags.append({
            "code": "UNIT_UNCERTAINTY",
            "severity": "WARNING",
            "message": f"Original unit '{record.unit}' could not be matched to a canonical unit.",
            "field": "unit"
        })
        
    # 7. DISTANCE_INFERRED
    if record.distance_inferred:
        flags.append({
            "code": "DISTANCE_INFERRED",
            "severity": "WARNING",
            "message": f"Flight distance was inferred using Great-Circle distance between '{record.origin_iata}' and '{record.destination_iata}'.",
            "field": "distance_km"
        })
        
    # 8. DUPLICATE_PERIOD
    # Check for overlapping periods with same facility and activity
    if start and end and facility_id:
        try:
            # Query overlaps: s1 <= e2 AND e1 >= s2
            overlapping_records = NormalizedRecord.objects.filter(
                tenant=tenant,
                facility_id=facility_id,
                activity_type=activity_type,
                period_start__lte=end,
                period_end__gte=start
            )
            if record.id:
                overlapping_records = overlapping_records.exclude(id=record.id)
                
            if overlapping_records.exists():
                flags.append({
                    "code": "DUPLICATE_PERIOD",
                    "severity": "ERROR",
                    "message": "Overlapping activity period detected for the same facility/meter.",
                    "field": "period_start"
                })
        except Exception as e:
            logger.error("Error checking overlapping periods: %s", str(e))

    # 9. STATISTICAL_OUTLIER
    # Trailing 12-month mean for tenant + facility + activity
    if start and facility_id:
        try:
            one_year_ago = start - timedelta(days=365)
            history = NormalizedRecord.objects.filter(
                tenant=tenant,
                facility_id=facility_id,
                activity_type=activity_type,
                period_start__gte=one_year_ago,
                period_start__lt=start
            )
            if record.id:
                history = history.exclude(id=record.id)
                
            history_vals = list(history.values_list('canonical_quantity', flat=True))
            
            if len(history_vals) >= 3:
                history_floats = [float(val) for val in history_vals]
                mean = np.mean(history_floats)
                std = np.std(history_floats)
                
                qty_float = float(quantity)
                # Check if it is > 3σ from mean
                if std > 0 and abs(qty_float - mean) > 3.0 * std:
                    flags.append({
                        "code": "STATISTICAL_OUTLIER",
                        "severity": "WARNING",
                        "message": f"Quantity {quantity} is a statistical outlier (> 3σ from trailing 12-month mean: {mean:.2f} ± {std:.2f}).",
                        "field": "canonical_quantity"
                    })
        except Exception as e:
            logger.error("Error running statistical outlier check: %s", str(e))

    # 10. BILLING_PERIOD_SPLIT
    # Checked if split is indicated in metadata
    if record.raw_record and record.raw_record.raw_payload:
        metadata = record.raw_record.raw_payload.get('_metadata', {})
        if metadata.get('billing_period_split'):
            flags.append({
                "code": "BILLING_PERIOD_SPLIT",
                "severity": "WARNING",
                "message": "This record was split proportionally across a month boundary.",
                "field": "period_start"
            })

    return flags
