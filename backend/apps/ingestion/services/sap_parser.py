from typing import Dict, Set

import structlog

from apps.ingestion.validation.anomaly import AnomalyDetector
from apps.ingestion.validation.rules import build_sap_engine
from apps.normalization.services.schema_mapper import SAP_SCHEMA_MAPPER
from apps.normalization.services.transformer import SAPTransformer
from .base_parser import BaseCSVParser, ParsedRow

logger = structlog.get_logger(__name__)


class SAPFuelParser(BaseCSVParser):
    REQUIRED_FIELDS = ["invoice_number", "vendor_name", "quantity", "unit", "posting_date", "fuel_type"]

    def __init__(self):
        super().__init__(engine=build_sap_engine())
        self._seen_invoices: Set[str] = set()

    def map_row(self, raw_row: Dict) -> Dict:
        return SAP_SCHEMA_MAPPER.map_row(raw_row)

    def normalize_row(self, mapped_row: Dict) -> Dict:
        return SAPTransformer.transform(mapped_row)

    def parse(self, file_content: bytes):
        self._seen_invoices = set()
        for parsed_row in super().parse(file_content):
            yield self._apply_duplicate_check(parsed_row)

    def _apply_duplicate_check(self, parsed_row: ParsedRow) -> ParsedRow:
        invoice = str(parsed_row.mapped_data.get("invoice_number", "")).strip()
        vendor = str(parsed_row.mapped_data.get("vendor_name", "")).strip()
        if invoice:
            duplicate_reasons = AnomalyDetector.check_duplicate_invoice(
                invoice, vendor, self._seen_invoices
            )
            if duplicate_reasons:
                parsed_row.validation_result.add_warning(
                    "invoice_number", "DUPLICATE_INVOICE", duplicate_reasons[0]
                )
        return parsed_row
