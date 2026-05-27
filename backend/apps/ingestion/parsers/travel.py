import pandas as pd
import math
import os
import urllib.request
from decimal import Decimal
from datetime import datetime
from apps.ingestion.parsers.base import BaseParser
import logging

logger = logging.getLogger(__name__)

# Haversine formula for Great-Circle distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlon/2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class TravelParser(BaseParser):
    VERSION = "1.0.0"

    EXPENSE_MAP = {
        "Airfare":         "flight",
        "Air":             "flight",
        "Hotel":           "hotel_stay",
        "Lodging":         "hotel_stay",
        "Car Rental":      "car_rental",
        "Rental Car":      "car_rental",
        "Taxi":            "taxi_rideshare",
        "Uber":            "taxi_rideshare",
        "Rail":            "rail",
        "Train":           "rail",
        "Ground Transport":"rail_or_road_unspecified"
    }

    # Static fallback airports for offline usage or unit test safety
    FALLBACK_AIRPORTS = {
        "SFO": (37.6189, -122.375),
        "JFK": (40.6398, -73.7789),
        "LHR": (51.4706, -0.461941),
        "CDG": (49.0097, 2.5479),
        "LAX": (33.9425, -118.408),
        "SIN": (1.35019, 103.994),
        "DXB": (25.2528, 55.3644),
        "HND": (35.5494, 139.7798),
        "SYD": (-33.9461, 151.1772),
        "CDG": (49.0097, 2.5479),
    }

    _airports_cache = None

    def __init__(self, file_path, tenant=None, metadata=None):
        super().__init__(file_path, metadata)
        self.tenant = tenant
        self.airports = self._get_airports()

    @classmethod
    def _get_airports(cls):
        """Loads and caches airport database from OpenFlights fixture."""
        if cls._airports_cache is not None:
            return cls._airports_cache

        airports = dict(cls.FALLBACK_AIRPORTS)
        fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../fixtures'))
        os.makedirs(fixture_dir, exist_ok=True)
        fixture_path = os.path.join(fixture_dir, 'airports.dat')

        # Download if missing
        if not os.path.exists(fixture_path):
            url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
            try:
                logger.info("Downloading OpenFlights airports database...")
                urllib.request.urlretrieve(url, fixture_path)
            except Exception as e:
                logger.warning("Could not download OpenFlights dataset, using fallback airports. Error: %s", str(e))

        if os.path.exists(fixture_path):
            try:
                import csv
                with open(fixture_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) > 7:
                            iata = row[4]
                            if iata and len(iata) == 3:
                                try:
                                    lat = float(row[6])
                                    lng = float(row[7])
                                    airports[iata.upper()] = (lat, lng)
                                except ValueError:
                                    pass
            except Exception as e:
                logger.error("Error reading airports.dat: %s", str(e))

        cls._airports_cache = airports
        return airports

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
            chunks = pd.read_csv(
                self.file_path,
                chunksize=1000,
                dtype=str,
                keep_default_na=False
            )
        except Exception as e:
            logger.error("Failed to read Concur CSV %s: %s", self.file_path, str(e))
            yield {
                "row_index": 0,
                "raw_payload": {},
                "parse_status": "PARSE_ERROR",
                "error_message": f"Invalid CSV file: {str(e)}"
            }
            return

        row_index = 0
        for chunk in chunks:
            # Map column names
            columns_mapped = {}
            for col in chunk.columns:
                col_clean = str(col).strip()
                columns_mapped[col] = col_clean
            chunk = chunk.rename(columns=columns_mapped)

            for _, row in chunk.iterrows():
                row_index += 1
                raw_payload = row.to_dict()

                try:
                    # Core fields
                    expense_type = raw_payload.get('Expense Type', '').strip()
                    travel_date_raw = raw_payload.get('Travel Date', '').strip()
                    vendor = raw_payload.get('Vendor', '').strip()
                    
                    if not expense_type:
                        raise ValueError("Missing Expense Type")
                    if not travel_date_raw:
                        raise ValueError("Missing Travel Date")

                    travel_date = self.parse_date(travel_date_raw)

                    # Map raw expense type to activity type
                    activity_type = self.EXPENSE_MAP.get(expense_type)
                    if not activity_type:
                        activity_type = f"travel_{expense_type.lower().replace(' ', '_')}"

                    scope = "SCOPE_3"  # All business travel is Scope 3

                    # Initialize record payload
                    qty = Decimal('0')
                    unit = 'unknown'
                    dist_inferred = False
                    origin = raw_payload.get('Origin', '').strip().upper()
                    destination = raw_payload.get('Destination', '').strip().upper()
                    distance_km = None
                    flags = []

                    # FLIGHT PROCESSING
                    if activity_type == 'flight':
                        dist_str = raw_payload.get('Distance', '').strip()
                        dist_unit = raw_payload.get('Distance Unit', '').strip().upper() or 'KM'
                        
                        if dist_str:
                            qty = Decimal(dist_str.replace(',', ''))
                            unit = dist_unit
                            if unit in ['MI', 'MILES']:
                                distance_km = qty * Decimal('1.60934')
                            else:
                                distance_km = qty
                        elif origin and destination:
                            # Infer distance using airports.dat coordinates
                            if origin in self.airports and destination in self.airports:
                                lat1, lon1 = self.airports[origin]
                                lat2, lon2 = self.airports[destination]
                                calculated_dist = haversine(lat1, lon1, lat2, lon2)
                                qty = Decimal(f"{calculated_dist:.2f}")
                                unit = 'KM'
                                distance_km = qty
                                dist_inferred = True
                            else:
                                raise ValueError(f"IATA codes '{origin}' or '{destination}' not found in airport registry")
                        else:
                            raise ValueError("No distance or origin/destination provided for flight")

                    # HOTEL PROCESSING
                    elif activity_type == 'hotel_stay':
                        nights_str = raw_payload.get('Nights', '').strip()
                        if nights_str:
                            qty = Decimal(nights_str)
                        else:
                            qty = Decimal('1')  # Default fallback to 1 night
                        unit = 'night'

                    # CAR RENTAL PROCESSING
                    elif activity_type == 'car_rental':
                        dist_str = raw_payload.get('Distance', '').strip()
                        dist_unit = raw_payload.get('Distance Unit', '').strip().upper() or 'MI'
                        
                        if dist_str:
                            qty = Decimal(dist_str.replace(',', ''))
                            unit = dist_unit
                            if unit in ['MI', 'MILES']:
                                distance_km = qty * Decimal('1.60934')
                            else:
                                distance_km = qty
                        else:
                            # No distance given, use Rental Days if available
                            nights_str = raw_payload.get('Nights', '').strip()  # Concur often uses Nights or Days column
                            days_qty = Decimal(nights_str) if nights_str else Decimal('1')
                            qty = days_qty
                            unit = 'day'
                            # In normalization engine, this will trigger a DISTANCE_UNKNOWN flag

                    # OTHER / RAIL
                    else:
                        amount_str = raw_payload.get('Amount', '').strip()
                        qty = Decimal(amount_str.replace(',', '')) if amount_str else Decimal('1')
                        unit = raw_payload.get('Currency', '').strip() or 'USD'

                    # Clean ticket class
                    ticket_class = raw_payload.get('Ticket Class', '').strip()

                    # Yield structured record
                    yield {
                        "row_index": row_index,
                        "raw_payload": raw_payload,
                        "parse_status": "OK",
                        "error_message": "",
                        "activity_data": {
                            "source_type": "TRAVEL",
                            "activity_type": activity_type,
                            "scope": scope,
                            "quantity": qty,
                            "unit": unit,
                            "period_start": travel_date,
                            "period_end": travel_date,
                            "facility_id": "",
                            "facility_name": vendor or "Business Travel",
                            "country_code": "US",  # Default default country code for travel
                            "origin_iata": origin,
                            "destination_iata": destination,
                            "distance_km": distance_km,
                            "distance_inferred": dist_inferred,
                            "metadata": {
                                "employee": raw_payload.get('Employee', ''),
                                "department": raw_payload.get('Department', ''),
                                "report_id": raw_payload.get('Report ID', ''),
                                "ticket_class": ticket_class,
                                "nights": raw_payload.get('Nights', '')
                            }
                        }
                    }

                except Exception as e:
                    logger.warning("Row parsing error in Travel row %d: %s", row_index, str(e))
                    yield {
                        "row_index": row_index,
                        "raw_payload": raw_payload,
                        "parse_status": "PARSE_ERROR",
                        "error_message": str(e)
                    }
