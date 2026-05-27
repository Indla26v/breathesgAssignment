from apps.normalization.models import ScopeMapping
import logging

logger = logging.getLogger(__name__)

DEFAULT_SCOPE_MAP = {
    # SAP
    'diesel_combustion': 'SCOPE_1',
    'natural_gas_kg_combustion': 'SCOPE_1',
    'natural_gas_m3_combustion': 'SCOPE_1',
    'purchased_diesel': 'SCOPE_3',
    'purchased_natural_gas_kg': 'SCOPE_3',
    'purchased_natural_gas_m3': 'SCOPE_3',
    
    # Utility
    'purchased_electricity': 'SCOPE_2',
    'natural_gas_utility': 'SCOPE_1',
    
    # Travel
    'flight': 'SCOPE_3',
    'hotel_stay': 'SCOPE_3',
    'car_rental': 'SCOPE_3',
    'taxi_rideshare': 'SCOPE_3',
    'rail': 'SCOPE_3',
    'rail_or_road_unspecified': 'SCOPE_3',
}

def classify_scope(activity_type, source_type):
    """
    Resolves the GHG Protocol scope (SCOPE_1, SCOPE_2, or SCOPE_3)
    based on the activity type. Queries the database first to allow
    admin customization, then falls back to a hardcoded dictionary.
    """
    try:
        # Check if there is an admin-defined mapping in database
        mapping = ScopeMapping.objects.filter(activity_type=activity_type).first()
        if mapping:
            return mapping.scope
    except Exception as e:
        logger.debug("ScopeMapping DB query failed (likely during initial migrations): %s", str(e))

    # Fallback to hardcoded mapping
    act_lower = str(activity_type).strip().lower()
    
    # Try direct match
    if act_lower in DEFAULT_SCOPE_MAP:
        return DEFAULT_SCOPE_MAP[act_lower]
        
    # Try partial match (e.g. if activity is diesel_combustion_process, matches diesel_combustion)
    for key, scope in DEFAULT_SCOPE_MAP.items():
        if key in act_lower:
            return scope
            
    # Default to Scope 3 for value-chain activities if unclassified
    return 'SCOPE_3'
