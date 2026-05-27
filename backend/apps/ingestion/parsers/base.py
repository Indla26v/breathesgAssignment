import abc

class BaseParser(abc.ABC):
    """
    Abstract base parser for enterprise source files.
    Ensures memory efficiency and consistent parse-result structures.
    """
    def __init__(self, file_path, metadata=None):
        self.file_path = file_path
        self.metadata = metadata or {}

    @abc.abstractmethod
    def parse(self):
        """
        Iterates over rows of the source file.
        Yields dictionaries of the form:
        {
            'row_index': int,
            'raw_payload': dict,
            'parse_status': 'OK' | 'PARSE_ERROR' | 'SKIPPED',
            'error_message': str,
            
            # Fields for Normalization Pipeline (only if OK):
            'activity_data': {
                'activity_type': str,
                'quantity': Decimal,
                'unit': str,
                'period_start': date,
                'period_end': date,
                'facility_id': str,
                'facility_name': str,
                'country_code': str,
                'origin_iata': str,
                'destination_iata': str,
                'distance_km': Decimal,
                'ticket_class': str,     # flight class (Economy, Business, etc.)
                'nights': int,            # hotel stay duration
                'days': int,              # car rental duration
                ...
            }
        }
        """
        pass
