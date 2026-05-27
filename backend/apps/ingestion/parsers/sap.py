import pandas as pd
from decimal import Decimal
from datetime import datetime
from apps.ingestion.parsers.base import BaseParser
from apps.tenants.models import FacilityMapping
import logging

logger = logging.getLogger(__name__)

class SAPParser(BaseParser):
    VERSION = "1.0.0"

    # Default material mapping. Can be overridden by tenant metadata.
    DEFAULT_MATERIAL_MAP = {
        "50045": {"fuel_type": "diesel", "canonical_unit": "L"},
        "50046": {"fuel_type": "natural_gas_kg", "canonical_unit": "KG"},
        "GAS-":  {"fuel_type": "natural_gas_m3", "canonical_unit": "M3"},
    }

    # Header aliases
    HEADER_MAP = {
        "WERK": "plant_code",
        "WERKS": "plant_code",
        "WERKSNAME": "plant_name",
        "MENGE": "quantity",
        "MENGENEINHEIT": "unit",
        "MEINS": "unit",
        "BUDAT": "posting_date",
        "BUCHUNGSDATUM": "posting_date",
        "MATNR": "material_number",
        "MATERIAL": "material_number",
        "BWART": "movement_type",
        "BEWEGUNGSART": "movement_type",
        "KOSTL": "cost_center",
        "KOSTENSTELLE": "cost_center",
        "BUKRS": "company_code",
        "BUCHUNGSKREIS": "company_code",
    }

    def __init__(self, file_path, tenant=None, metadata=None):
        super().__init__(file_path, metadata)
        self.tenant = tenant
        # Load tenant-specific mapping or fallback
        self.material_map = self.metadata.get("material_map", self.DEFAULT_MATERIAL_MAP)

    def parse_date(self, date_str):
        if not date_str or pd.isna(date_str):
            return None
        date_str = str(date_str).strip()
        for fmt in ['%Y%m%d', '%d.%m.%Y', '%m/%d/%Y', '%Y-%m-%d']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        raise ValueError(f"Date format not recognized: '{date_str}'")

    def resolve_fuel_and_unit(self, material_number):
        if not material_number or pd.isna(material_number):
            return "unknown_material", "unknown"
            
        mat_str = str(material_number).strip()
        # Clean leading zeroes for match
        mat_clean = mat_str.lstrip('0')
        
        for prefix, info in self.material_map.items():
            prefix_clean = prefix.strip().lstrip('0')
            if mat_str.startswith(prefix) or mat_clean.startswith(prefix_clean):
                return info["fuel_type"], info["canonical_unit"]
                
        return f"unknown_material_{mat_str}", "unknown"

    def parse(self):
        # Read the file chunk-by-chunk using Pandas to keep memory low
        # SE16 outputs are often tab-separated flat files. We try to read them.
        try:
            chunks = pd.read_csv(
                self.file_path,
                sep='\t',
                chunksize=1000,
                dtype=str,
                skipinitialspace=True,
                keep_default_na=False
            )
        except Exception as e:
            logger.error("Failed to read SAP file %s: %s", self.file_path, str(e))
            yield {
                "row_index": 0,
                "raw_payload": {},
                "parse_status": "PARSE_ERROR",
                "error_message": f"File is not a valid tab-delimited file: {str(e)}"
            }
            return

        row_index = 0
        for chunk in chunks:
            # Map column headers to canonical English keys
            # Convert column names to uppercase and strip
            columns_mapped = {}
            for col in chunk.columns:
                col_clean = str(col).strip().upper()
                mapped_col = self.HEADER_MAP.get(col_clean, col_clean.lower())
                columns_mapped[col] = mapped_col

            chunk = chunk.rename(columns=columns_mapped)

            for _, row in chunk.iterrows():
                row_index += 1
                raw_payload = row.to_dict()

                try:
                    # Extract fields
                    plant_code = raw_payload.get('plant_code', '').strip()
                    qty_str = raw_payload.get('quantity', '').strip()
                    unit = raw_payload.get('unit', '').strip()
                    posting_date_raw = raw_payload.get('posting_date', '').strip()
                    material_number = raw_payload.get('material_number', '').strip()
                    movement_type = raw_payload.get('movement_type', '').strip()

                    # Validations
                    if not qty_str:
                        raise ValueError("Missing quantity field")
                    if not posting_date_raw:
                        raise ValueError("Missing posting date field")

                    quantity = Decimal(qty_str.replace(',', ''))  # Handle comma formatting if present
                    posting_date = self.parse_date(posting_date_raw)

                    # Resolve material
                    fuel_type, canonical_unit = self.resolve_fuel_and_unit(material_number)

                    # Determine Activity Type & Scope from movement type & material
                    # 201/261 = consumption -> Scope 1
                    # 101/501 = goods receipt -> Scope 3
                    if movement_type in ['201', '261']:
                        activity_type = f"{fuel_type}_combustion"
                        scope = "SCOPE_1"
                    elif movement_type in ['101', '501']:
                        activity_type = f"purchased_{fuel_type}"
                        scope = "SCOPE_3"
                    else:
                        # Fallback for other movement types
                        activity_type = f"sap_movement_{movement_type}_{fuel_type}"
                        scope = "SCOPE_3"

                    # Resolve FacilityMapping (Plant Code -> Facility)
                    facility_id = plant_code
                    facility_name = ""
                    country_code = ""
                    
                    if self.tenant and plant_code:
                        try:
                            mapping = FacilityMapping.objects.filter(
                                tenant=self.tenant, 
                                plant_code=plant_code
                            ).first()
                            if mapping:
                                facility_id = mapping.facility_id
                                facility_name = mapping.facility_name
                                country_code = mapping.country_code
                        except Exception as e:
                            logger.error("Facility lookup error: %s", str(e))

                    yield {
                        "row_index": row_index,
                        "raw_payload": raw_payload,
                        "parse_status": "OK",
                        "error_message": "",
                        "activity_data": {
                            "source_type": "SAP",
                            "activity_type": activity_type,
                            "scope": scope,
                            "quantity": quantity,
                            "unit": unit,
                            "period_start": posting_date,
                            "period_end": posting_date,
                            "facility_id": facility_id,
                            "facility_name": facility_name,
                            "country_code": country_code,
                            "metadata": {
                                "material_number": material_number,
                                "movement_type": movement_type,
                                "cost_center": raw_payload.get('cost_center', '').strip(),
                                "company_code": raw_payload.get('company_code', '').strip()
                            }
                        }
                    }

                except Exception as e:
                    logger.warning("Row parsing error in SAP row %d: %s", row_index, str(e))
                    yield {
                        "row_index": row_index,
                        "raw_payload": raw_payload,
                        "parse_status": "PARSE_ERROR",
                        "error_message": str(e)
                    }
