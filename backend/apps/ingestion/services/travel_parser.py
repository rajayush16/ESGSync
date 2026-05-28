from typing import Dict

import structlog

from apps.ingestion.validation.anomaly import AnomalyDetector
from apps.ingestion.validation.rules import build_travel_engine
from apps.normalization.services.schema_mapper import TRAVEL_SCHEMA_MAPPER
from apps.normalization.services.transformer import TravelTransformer
from .base_parser import BaseCSVParser

logger = structlog.get_logger(__name__)


class CorporateTravelParser(BaseCSVParser):
    REQUIRED_FIELDS = ["employee_id", "trip_type", "departure_airport", "arrival_airport", "trip_date"]

    def __init__(self):
        super().__init__(engine=build_travel_engine())

    def map_row(self, raw_row: Dict) -> Dict:
        return TRAVEL_SCHEMA_MAPPER.map_row(raw_row)

    def normalize_row(self, mapped_row: Dict) -> Dict:
        return TravelTransformer.transform(mapped_row)

    def parse(self, file_content: bytes):
        for row in super().parse(file_content):
            if row.normalized_data:
                anomalies = AnomalyDetector.check_travel(row.normalized_data)
                if anomalies:
                    row.normalized_data["anomaly_reasons"] = anomalies
            yield row
