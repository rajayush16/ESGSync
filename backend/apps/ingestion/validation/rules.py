from decimal import Decimal
from typing import Any, Dict, Optional

from apps.common.enums import ValidationStatus
from apps.common.utils import safe_date, safe_decimal
from .engine import ValidationEngine, ValidationRule


def _require_field(field_name: str) -> ValidationRule:
    def check(record: Dict[str, Any]) -> Optional[str]:
        val = record.get(field_name)
        if val is None or str(val).strip() == "":
            return f"Field '{field_name}' is required but missing or empty."
        return None

    return ValidationRule(
        name=f"required_{field_name}",
        check=check,
        field=field_name,
        severity=ValidationStatus.FAILED,
        code="REQUIRED_FIELD_MISSING",
    )


def _non_negative(field_name: str) -> ValidationRule:
    def check(record: Dict[str, Any]) -> Optional[str]:
        val = safe_decimal(record.get(field_name))
        if val is not None and val < Decimal("0"):
            return f"Field '{field_name}' cannot be negative (got {val})."
        return None

    return ValidationRule(
        name=f"non_negative_{field_name}",
        check=check,
        field=field_name,
        severity=ValidationStatus.FAILED,
        code="NEGATIVE_VALUE",
    )


def _positive(field_name: str) -> ValidationRule:
    def check(record: Dict[str, Any]) -> Optional[str]:
        val = safe_decimal(record.get(field_name))
        if val is None or val <= Decimal("0"):
            return f"Field '{field_name}' must be a positive number."
        return None

    return ValidationRule(
        name=f"positive_{field_name}",
        check=check,
        field=field_name,
        severity=ValidationStatus.FAILED,
        code="NON_POSITIVE_VALUE",
    )


def _valid_date(field_name: str) -> ValidationRule:
    def check(record: Dict[str, Any]) -> Optional[str]:
        val = record.get(field_name)
        if val and safe_date(val) is None:
            return f"Field '{field_name}' has an unrecognized date format: '{val}'."
        return None

    return ValidationRule(
        name=f"valid_date_{field_name}",
        check=check,
        field=field_name,
        severity=ValidationStatus.FAILED,
        code="INVALID_DATE_FORMAT",
    )


def build_sap_engine() -> ValidationEngine:
    engine = ValidationEngine()
    required = ["invoice_number", "vendor_name", "quantity", "unit", "posting_date", "fuel_type"]
    for f in required:
        engine.register(_require_field(f))
    engine.register(_positive("quantity"))
    engine.register(_valid_date("posting_date"))

    def check_unit(record):
        unit = str(record.get("unit", "")).strip().lower()
        allowed = {"l", "liters", "litres", "gal", "gallons", "kg", "kilograms", "mt", "metric tons", "t", "ton", "tons"}
        if unit and unit not in allowed:
            return f"Unrecognized unit '{unit}'. Expected: liters, gallons, kg, metric tons."
        return None

    engine.register(ValidationRule(
        name="valid_unit_sap",
        check=check_unit,
        field="unit",
        severity=ValidationStatus.WARNING,
        code="UNRECOGNIZED_UNIT",
    ))

    def check_duplicate_invoice(record):
        # Duplicate detection is done at the batch level in the parser service
        return None

    return engine


def build_utility_engine() -> ValidationEngine:
    engine = ValidationEngine()
    required = ["meter_id", "facility", "billing_period_start", "billing_period_end", "kwh_usage"]
    for f in required:
        engine.register(_require_field(f))
    engine.register(_non_negative("kwh_usage"))
    engine.register(_valid_date("billing_period_start"))
    engine.register(_valid_date("billing_period_end"))

    def check_billing_period_order(record):
        start = safe_date(record.get("billing_period_start"))
        end = safe_date(record.get("billing_period_end"))
        if start and end and start > end:
            return "billing_period_start must be before billing_period_end."
        return None

    engine.register(ValidationRule(
        name="billing_period_order",
        check=check_billing_period_order,
        field="billing_period_start",
        severity=ValidationStatus.FAILED,
        code="INVALID_BILLING_PERIOD",
    ))

    def check_kwh_realistic(record):
        kwh = safe_decimal(record.get("kwh_usage"))
        if kwh and kwh > Decimal("10000000"):
            return f"kWh usage {kwh} exceeds 10,000,000 — likely a data entry error."
        return None

    engine.register(ValidationRule(
        name="kwh_realistic",
        check=check_kwh_realistic,
        field="kwh_usage",
        severity=ValidationStatus.WARNING,
        code="UNREALISTIC_KWH",
    ))

    return engine


def build_travel_engine() -> ValidationEngine:
    engine = ValidationEngine()
    required = ["employee_id", "trip_type", "departure_airport", "arrival_airport", "trip_date"]
    for f in required:
        engine.register(_require_field(f))
    engine.register(_valid_date("trip_date"))

    def check_airport_codes(record):
        for field in ("departure_airport", "arrival_airport"):
            code = str(record.get(field, "")).strip().upper()
            if code and len(code) not in (3, 4):
                return f"Airport code '{code}' in '{field}' does not look like an IATA/ICAO code."
        return None

    engine.register(ValidationRule(
        name="airport_code_format",
        check=check_airport_codes,
        field="departure_airport",
        severity=ValidationStatus.WARNING,
        code="SUSPECT_AIRPORT_CODE",
    ))

    def check_same_airport(record):
        dep = str(record.get("departure_airport", "")).strip().upper()
        arr = str(record.get("arrival_airport", "")).strip().upper()
        if dep and arr and dep == arr:
            return "Departure and arrival airports are the same."
        return None

    engine.register(ValidationRule(
        name="same_airport",
        check=check_same_airport,
        field="arrival_airport",
        severity=ValidationStatus.FAILED,
        code="SAME_ORIGIN_DESTINATION",
    ))

    def check_hotel_nights(record):
        nights = safe_decimal(record.get("hotel_nights"))
        if nights is not None and nights < Decimal("0"):
            return "Hotel nights cannot be negative."
        if nights is not None and nights > Decimal("30"):
            return f"Hotel nights ({int(nights)}) exceeds 30 — suspicious."
        return None

    engine.register(ValidationRule(
        name="hotel_nights",
        check=check_hotel_nights,
        field="hotel_nights",
        severity=ValidationStatus.WARNING,
        code="EXCESSIVE_HOTEL_NIGHTS",
    ))

    return engine
