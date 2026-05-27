import pandas as pd
import re
from decimal import Decimal
from datetime import datetime
from apps.ingestion.parsers.base import BaseParser
import logging

logger = logging.getLogger(__name__)

class UtilityParser(BaseParser):
    VERSION = "1.0.0"

    def __init__(self, file_path, tenant=None, metadata=None):
        super().__init__(file_path, metadata)
        self.tenant = tenant

    def parse_date(self, date_str):
        if not date_str or pd.isna(date_str):
            return None
        date_str = str(date_str).strip()
        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%Y%m%d']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        raise ValueError(f"Date format not recognized: '{date_str}'")

    def parse(self):
        try:
            # Load the CSV using Pandas chunking
            chunks = pd.read_csv(
                self.file_path,
                chunksize=1000,
                dtype=str,
                keep_default_na=False
            )
        except Exception as e:
            logger.error("Failed to read Utility CSV %s: %s", self.file_path, str(e))
            yield {
                "row_index": 0,
                "raw_payload": {},
                "parse_status": "PARSE_ERROR",
                "error_message": f"Invalid CSV file: {str(e)}"
            }
            return

        row_index = 0
        for chunk in chunks:
            # Standardize column headers (remove spaces and lowercase)
            columns_mapped = {}
            for col in chunk.columns:
                col_clean = str(col).strip()
                columns_mapped[col] = col_clean

            chunk = chunk.rename(columns=columns_mapped)

            # Find the usage/consumption column and its unit
            usage_col = None
            detected_unit = 'kWh'  # Default fallback
            
            for col in chunk.columns:
                col_lower = col.lower()
                if 'usage' in col_lower or 'consumption' in col_lower or 'quantity' in col_lower:
                    usage_col = col
                    # Extract unit from parenthesis if exists, e.g. Usage (kWh)
                    match = re.search(r'\(([^)]+)\)', col)
                    if match:
                        detected_unit = match.group(1).strip()
                    break

            if not usage_col:
                # If no usage column is found, try to locate any numeric looking column or fallback to 'usage'
                usage_col = 'Usage (kWh)'

            for _, row in chunk.iterrows():
                row_index += 1
                raw_payload = row.to_dict()

                try:
                    # Required fields
                    meter_id = raw_payload.get('Meter ID', raw_payload.get('meter_id', '')).strip()
                    service_address = raw_payload.get('Service Address', raw_payload.get('service_address', '')).strip()
                    read_from_str = raw_payload.get('Read Date From', raw_payload.get('read_date_from', '')).strip()
                    read_to_str = raw_payload.get('Read Date To', raw_payload.get('read_date_to', '')).strip()
                    qty_str = raw_payload.get(usage_col, '').strip()

                    if not meter_id:
                        raise ValueError("Missing Meter ID")
                    if not read_from_str or not read_to_str:
                        raise ValueError("Missing billing period date range")
                    if not qty_str:
                        raise ValueError(f"Missing quantity under column '{usage_col}'")

                    quantity = Decimal(qty_str.replace(',', ''))
                    read_from = self.parse_date(read_from_str)
                    read_to = self.parse_date(read_to_str)

                    if read_from > read_to:
                        raise ValueError("Read Date From is after Read Date To")

                    # Determine unit (check metadata meter mapping first, fallback to header)
                    row_unit = self.metadata.get("meter_unit_map", {}).get(meter_id, detected_unit)

                    # Identify activity and scope based on unit
                    unit_upper = row_unit.upper()
                    if unit_upper in ['THERM', 'THERMS']:
                        activity_type = "natural_gas_utility"
                        scope = "SCOPE_1"
                    else:
                        activity_type = "purchased_electricity"
                        scope = "SCOPE_2"

                    # Proportional Billing Period Splitting
                    import calendar
                    from datetime import date, timedelta

                    segments = []
                    if read_from.month != read_to.month or read_from.year != read_to.year:
                        total_days = (read_to - read_from).days + 1
                        curr_date = read_from
                        while curr_date <= read_to:
                            # End of current month
                            _, last_day = calendar.monthrange(curr_date.year, curr_date.month)
                            month_end = date(curr_date.year, curr_date.month, last_day)
                            segment_end = min(month_end, read_to)
                            
                            seg_days = (segment_end - curr_date).days + 1
                            seg_qty = (Decimal(seg_days) / Decimal(total_days)) * quantity
                            # Round to 6 decimal places to match database DecimalField
                            seg_qty = seg_qty.quantize(Decimal('1.000000'))

                            segments.append({
                                "start": curr_date,
                                "end": segment_end,
                                "quantity": seg_qty,
                                "split": True
                            })
                            curr_date = segment_end + timedelta(days=1)
                    else:
                        segments.append({
                            "start": read_from,
                            "end": read_to,
                            "quantity": quantity,
                            "split": False
                        })

                    # Yield structured record for each segment
                    for segment in segments:
                        yield {
                            "row_index": row_index,
                            "raw_payload": raw_payload,
                            "parse_status": "OK",
                            "error_message": "",
                            "activity_data": {
                                "source_type": "UTILITY",
                                "activity_type": activity_type,
                                "scope": scope,
                                "quantity": segment["quantity"],
                                "unit": row_unit,
                                "period_start": segment["start"],
                                "period_end": segment["end"],
                                "facility_id": meter_id,
                                "facility_name": service_address or f"Meter {meter_id}",
                                "country_code": "US",
                                "metadata": {
                                    "account_number": raw_payload.get('Account Number', ''),
                                    "rate_schedule": raw_payload.get('Rate Schedule', ''),
                                    "charges": raw_payload.get('Charges ($)', ''),
                                    "_metadata": {
                                        "billing_period_split": segment["split"]
                                    }
                                }
                            }
                        }

                except Exception as e:
                    logger.warning("Row parsing error in Utility row %d: %s", row_index, str(e))
                    yield {
                        "row_index": row_index,
                        "raw_payload": raw_payload,
                        "parse_status": "PARSE_ERROR",
                        "error_message": str(e)
                    }
