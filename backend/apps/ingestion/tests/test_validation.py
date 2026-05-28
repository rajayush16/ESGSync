import pytest

from apps.common.enums import ValidationStatus
from apps.ingestion.validation.rules import (
    build_sap_engine,
    build_utility_engine,
    build_travel_engine,
)


class TestSAPValidation:
    def setup_method(self):
        self.engine = build_sap_engine()

    def test_valid_sap_record(self):
        record = {
            "invoice_number": "INV-001",
            "vendor_name": "ACME Fuels GmbH",
            "quantity": "500",
            "unit": "liters",
            "posting_date": "2024-01-15",
            "fuel_type": "diesel",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.PASSED

    def test_missing_invoice_number(self):
        record = {
            "invoice_number": "",
            "vendor_name": "ACME Fuels",
            "quantity": "500",
            "unit": "liters",
            "posting_date": "2024-01-15",
            "fuel_type": "diesel",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.FAILED
        assert any(e["code"] == "REQUIRED_FIELD_MISSING" for e in result.errors)

    def test_negative_quantity(self):
        record = {
            "invoice_number": "INV-001",
            "vendor_name": "ACME",
            "quantity": "-10",
            "unit": "liters",
            "posting_date": "2024-01-15",
            "fuel_type": "diesel",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.FAILED
        assert any(e["code"] == "NON_POSITIVE_VALUE" for e in result.errors)

    def test_invalid_date_format(self):
        record = {
            "invoice_number": "INV-001",
            "vendor_name": "ACME",
            "quantity": "100",
            "unit": "liters",
            "posting_date": "not-a-date",
            "fuel_type": "diesel",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.FAILED

    def test_unrecognized_unit_is_warning(self):
        record = {
            "invoice_number": "INV-001",
            "vendor_name": "ACME",
            "quantity": "100",
            "unit": "barrels",
            "posting_date": "2024-01-15",
            "fuel_type": "diesel",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.WARNING
        assert any(w["code"] == "UNRECOGNIZED_UNIT" for w in result.warnings)


class TestUtilityValidation:
    def setup_method(self):
        self.engine = build_utility_engine()

    def test_valid_utility_record(self):
        record = {
            "meter_id": "MTR-001",
            "facility": "Berlin HQ",
            "billing_period_start": "2024-01-01",
            "billing_period_end": "2024-01-31",
            "kwh_usage": "15000",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.PASSED

    def test_invalid_billing_period_order(self):
        record = {
            "meter_id": "MTR-001",
            "facility": "Berlin HQ",
            "billing_period_start": "2024-02-01",
            "billing_period_end": "2024-01-01",
            "kwh_usage": "15000",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.FAILED
        assert any(e["code"] == "INVALID_BILLING_PERIOD" for e in result.errors)

    def test_negative_kwh(self):
        record = {
            "meter_id": "MTR-001",
            "facility": "Berlin HQ",
            "billing_period_start": "2024-01-01",
            "billing_period_end": "2024-01-31",
            "kwh_usage": "-500",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.FAILED

    def test_unrealistic_kwh_is_warning(self):
        record = {
            "meter_id": "MTR-001",
            "facility": "Berlin HQ",
            "billing_period_start": "2024-01-01",
            "billing_period_end": "2024-01-31",
            "kwh_usage": "99999999",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.WARNING


class TestTravelValidation:
    def setup_method(self):
        self.engine = build_travel_engine()

    def test_valid_travel_record(self):
        record = {
            "employee_id": "EMP-001",
            "trip_type": "Business",
            "departure_airport": "LHR",
            "arrival_airport": "JFK",
            "trip_date": "2024-03-10",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.PASSED

    def test_same_origin_destination(self):
        record = {
            "employee_id": "EMP-001",
            "trip_type": "Business",
            "departure_airport": "LHR",
            "arrival_airport": "LHR",
            "trip_date": "2024-03-10",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.FAILED
        assert any(e["code"] == "SAME_ORIGIN_DESTINATION" for e in result.errors)

    def test_excessive_hotel_nights_warning(self):
        record = {
            "employee_id": "EMP-001",
            "trip_type": "Business",
            "departure_airport": "LHR",
            "arrival_airport": "JFK",
            "trip_date": "2024-03-10",
            "hotel_nights": "45",
        }
        result = self.engine.run(record)
        assert result.status == ValidationStatus.WARNING
        assert any(w["code"] == "EXCESSIVE_HOTEL_NIGHTS" for w in result.warnings)
