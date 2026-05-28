from decimal import Decimal
from typing import Dict, List, Optional

import structlog

from apps.ingestion.validation.anomaly import AnomalyDetector
from apps.ingestion.validation.rules import build_utility_engine
from apps.normalization.services.schema_mapper import UTILITY_SCHEMA_MAPPER
from apps.normalization.services.transformer import UtilityTransformer
from .base_parser import BaseCSVParser, ParsedRow

logger = structlog.get_logger(__name__)


class UtilityElectricityParser(BaseCSVParser):
    REQUIRED_FIELDS = ["meter_id", "facility", "billing_period_start", "billing_period_end", "kwh_usage"]

    def __init__(self):
        super().__init__(engine=build_utility_engine())
        self._historical_averages: Dict[str, List[Decimal]] = {}

    def map_row(self, raw_row: Dict) -> Dict:
        return UTILITY_SCHEMA_MAPPER.map_row(raw_row)

    def normalize_row(self, mapped_row: Dict) -> Dict:
        return UtilityTransformer.transform(mapped_row)

    def parse(self, file_content: bytes):
        rows = list(super().parse(file_content))
        # Build historical averages per meter from this batch
        meter_kwh: Dict[str, List[Decimal]] = {}
        for row in rows:
            if row.normalized_data:
                meter = str(row.mapped_data.get("meter_id", ""))
                kwh_str = row.normalized_data.get("kwh_usage_normalized")
                if meter and kwh_str:
                    try:
                        meter_kwh.setdefault(meter, []).append(Decimal(kwh_str))
                    except Exception:
                        pass

        meter_avg: Dict[str, Decimal] = {
            m: sum(vals) / len(vals) for m, vals in meter_kwh.items() if vals
        }

        for row in rows:
            if row.normalized_data:
                meter = str(row.mapped_data.get("meter_id", ""))
                kwh_str = row.normalized_data.get("kwh_usage_normalized")
                historical_avg = meter_avg.get(meter)
                if kwh_str:
                    anomalies = AnomalyDetector.check_electricity(
                        {"kwh_usage_normalized": kwh_str}, historical_avg
                    )
                    if anomalies:
                        row.normalized_data["anomaly_reasons"] = anomalies
            yield row
