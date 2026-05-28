import io
from typing import Dict, Generator, List, Optional, Tuple

import pandas as pd
import structlog

from apps.common.enums import ValidationStatus
from apps.ingestion.validation.engine import ValidationEngine, ValidationResult

logger = structlog.get_logger(__name__)


class ParsedRow:
    __slots__ = ("row_number", "raw_data", "mapped_data", "normalized_data", "validation_result")

    def __init__(
        self,
        row_number: int,
        raw_data: Dict,
        mapped_data: Dict,
        normalized_data: Optional[Dict] = None,
        validation_result: Optional[ValidationResult] = None,
    ):
        self.row_number = row_number
        self.raw_data = raw_data
        self.mapped_data = mapped_data
        self.normalized_data = normalized_data
        self.validation_result = validation_result or ValidationResult()


class BaseCSVParser:
    REQUIRED_FIELDS: List[str] = []
    MAX_ROWS = 50_000

    def __init__(self, engine: ValidationEngine):
        self.engine = engine

    def read_csv(self, file_content: bytes) -> pd.DataFrame:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding=enc, dtype=str, keep_default_na=False)
                df.columns = df.columns.str.strip()
                return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        raise ValueError("Could not decode CSV file with any supported encoding.")

    def map_row(self, raw_row: Dict) -> Dict:
        raise NotImplementedError

    def normalize_row(self, mapped_row: Dict) -> Dict:
        raise NotImplementedError

    def parse(self, file_content: bytes) -> Generator[ParsedRow, None, None]:
        df = self.read_csv(file_content)
        if len(df) > self.MAX_ROWS:
            raise ValueError(f"File contains {len(df)} rows, exceeding the maximum of {self.MAX_ROWS}.")

        logger.info("csv_parse_start", total_rows=len(df))

        for idx, row_series in df.iterrows():
            row_number = int(idx) + 2  # 1-indexed + header row
            raw_data = row_series.to_dict()

            # Skip entirely blank rows
            if all(str(v).strip() == "" for v in raw_data.values()):
                continue

            try:
                mapped = self.map_row(raw_data)
                normalized = self.normalize_row(mapped)
                validation_result = self.engine.run(mapped)

                yield ParsedRow(
                    row_number=row_number,
                    raw_data=raw_data,
                    mapped_data=mapped,
                    normalized_data=normalized,
                    validation_result=validation_result,
                )
            except Exception as exc:
                logger.warning("row_parse_error", row=row_number, error=str(exc))
                result = ValidationResult()
                result.add_error("__row__", "PARSE_ERROR", f"Row could not be processed: {exc}")
                yield ParsedRow(
                    row_number=row_number,
                    raw_data=raw_data,
                    mapped_data={},
                    normalized_data=None,
                    validation_result=result,
                )
