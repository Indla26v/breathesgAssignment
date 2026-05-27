from decimal import Decimal
import pint
import logging

logger = logging.getLogger(__name__)

# Initialize pint unit registry
ureg = pint.UnitRegistry()

def convert_unit(quantity, source_unit, activity_type=None):
    """
    Converts a quantity and its source unit to the canonical unit.
    Returns: (canonical_quantity, canonical_unit, error_flag)
    
    Rules:
    - L (liters) -> stays as L
    - KG -> stays as KG  
    - M3 -> stays as M3
    - GAL -> L (* 3.78541)
    - MMBTU -> MMBTU
    - kWh -> kWh
    - MWh -> kWh (* 1000)
    - Therms -> kWh (* 29.3001)
    - GJ -> kWh (* 277.778)
    - MI -> KM (* 1.60934)
    - night/nights -> night
    - day/days -> day
    - Unknown unit -> UNIT_UNCERTAINTY flag, store original, do not convert
    """
    if quantity is None:
        return Decimal('0'), 'unknown', 'UNIT_UNCERTAINTY'
        
    # Ensure quantity is a Decimal
    try:
        qty_dec = Decimal(str(quantity))
    except Exception:
        qty_dec = Decimal('0')

    # Normalize unit string (case-insensitive, trimmed)
    unit_raw = str(source_unit).strip()
    unit_upper = unit_raw.upper()

    # Define strict conversion map for common/standard enterprise units
    # Format: {SOURCE_UNIT: (CANONICAL_UNIT, MULTIPLIER)}
    strict_map = {
        'L': ('L', Decimal('1')),
        'LITER': ('L', Decimal('1')),
        'LITERS': ('L', Decimal('1')),
        
        'KG': ('KG', Decimal('1')),
        'KILOGRAM': ('KG', Decimal('1')),
        'KILOGRAMS': ('KG', Decimal('1')),
        
        'M3': ('M3', Decimal('1')),
        'CUBIC_METER': ('M3', Decimal('1')),
        'CUBIC_METERS': ('M3', Decimal('1')),
        
        'GAL': ('L', Decimal('3.78541')),
        'GALLON': ('L', Decimal('3.78541')),
        'GALLONS': ('L', Decimal('3.78541')),
        
        'MMBTU': ('MMBTU', Decimal('1')),
        
        'KWH': ('kWh', Decimal('1')),
        'KILOWATT_HOUR': ('kWh', Decimal('1')),
        'KILOWATT_HOURS': ('kWh', Decimal('1')),
        
        'MWH': ('kWh', Decimal('1000')),
        'MEGAWATT_HOUR': ('kWh', Decimal('1000')),
        'MEGAWATT_HOURS': ('kWh', Decimal('1000')),
        
        'THERM': ('kWh', Decimal('29.3001')),
        'THERMS': ('kWh', Decimal('29.3001')),
        
        'GJ': ('kWh', Decimal('277.778')),
        'GIGAJOULE': ('kWh', Decimal('277.778')),
        'GIGAJOULES': ('kWh', Decimal('277.778')),
        
        'MI': ('KM', Decimal('1.60934')),
        'MILE': ('KM', Decimal('1.60934')),
        'MILES': ('KM', Decimal('1.60934')),
        
        'KM': ('KM', Decimal('1')),
        'KILOMETER': ('KM', Decimal('1')),
        'KILOMETERS': ('KM', Decimal('1')),
        
        'NIGHT': ('night', Decimal('1')),
        'NIGHTS': ('night', Decimal('1')),
        
        'DAY': ('day', Decimal('1')),
        'DAYS': ('day', Decimal('1')),
        
        'TRIP': ('trip', Decimal('1')),
        'TRIPS': ('trip', Decimal('1')),
    }

    # Try matching the strict map first
    if unit_upper in strict_map:
        canonical_unit, factor = strict_map[unit_upper]
        return qty_dec * factor, canonical_unit, None

    # Fallback to pint registry for physical dimensions
    try:
        # Lowercase is generally preferred by pint
        unit_lower = unit_raw.lower()
        q = ureg.Quantity(float(qty_dec), unit_lower)
        
        if q.is_compatible_with('kWh'):
            val = Decimal(str(q.to('kWh').magnitude))
            return val, 'kWh', None
        elif q.is_compatible_with('liter'):
            val = Decimal(str(q.to('liter').magnitude))
            return val, 'L', None
        elif q.is_compatible_with('kilogram'):
            val = Decimal(str(q.to('kilogram').magnitude))
            return val, 'KG', None
        elif q.is_compatible_with('kilometer'):
            val = Decimal(str(q.to('kilometer').magnitude))
            return val, 'KM', None
            
    except Exception as e:
        logger.warning("Pint conversion failed for unit '%s': %s", unit_raw, str(e))

    # If all conversions fail, flag unit uncertainty and return original values
    return qty_dec, unit_raw, 'UNIT_UNCERTAINTY'
