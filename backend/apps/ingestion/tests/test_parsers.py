import io

import pytest

from apps.ingestion.services.sap_parser import SAPFuelParser
from apps.ingestion.services.utility_parser import UtilityElectricityParser
from apps.ingestion.services.travel_parser import CorporateTravelParser
from apps.common.enums import ValidationStatus


SAP_CSV = b"""Invoice Number,Vendor Name,Plant Code,Material Description,Quantity,Unit,Currency,Posting Date,Fuel Type,Procurement Category
INV-001,ACME Fuels GmbH,PLANT-DE-01,Diesel B7,500,liters,EUR,2024-01-15,diesel,fuel
INV-002,BrennstoffAG,PLANT-DE-02,Gasoline 95 E10,200,gallons,EUR,15.01.2024,petrol,fuel
INV-003,,PLANT-DE-01,Natural Gas,100,cubic meters,EUR,2024-01-16,natural gas,energy
INV-001,ACME Fuels GmbH,PLANT-DE-01,Diesel B7,800,liters,EUR,2024-01-20,diesel,fuel
"""

UTILITY_CSV = b"""Meter ID,Facility,Billing Period Start,Billing Period End,kWh Usage,Tariff Category,Utility Provider,Cost,Region
MTR-001,Berlin HQ,2024-01-01,2024-01-31,15000,industrial,Vattenfall,2500,de
MTR-002,Munich Office,2024-01-01,2024-01-31,8500,commercial,EON,1400,de
MTR-001,Berlin HQ,2024-02-01,2024-02-29,58000,industrial,Vattenfall,9200,de
"""

TRAVEL_CSV = b"""Employee ID,Trip Type,Departure Airport,Arrival Airport,Travel Class,Hotel Nights,Transport Mode,Booking Platform,Trip Date
EMP-001,business,LHR,JFK,business,3,air,Concur,2024-03-10
EMP-002,conference,CDG,SIN,economy,5,air,Navan,2024-03-12
EMP-003,client visit,LHR,LHR,economy,0,air,Concur,2024-03-15
EMP-004,project,FRA,MUC,economy,45,air,SAP Concur,2024-03-20
"""


class TestSAPParser:
    def test_parses_valid_rows(self):
        parser = SAPFuelParser()
        rows = list(parser.parse(SAP_CSV))
        assert len(rows) == 4

    def test_detects_missing_vendor(self):
        parser = SAPFuelParser()
        rows = list(parser.parse(SAP_CSV))
        # INV-003 has no vendor_name
        failed = [r for r in rows if r.validation_result.status == ValidationStatus.FAILED]
        assert any(True for r in failed)

    def test_detects_duplicate_invoice(self):
        parser = SAPFuelParser()
        rows = list(parser.parse(SAP_CSV))
        # INV-001 appears twice
        warnings_with_duplicate = [
            r for r in rows
            if any(w["code"] == "DUPLICATE_INVOICE" for w in r.validation_result.warnings)
        ]
        assert len(warnings_with_duplicate) >= 1

    def test_normalized_data_has_co2e(self):
        parser = SAPFuelParser()
        rows = list(parser.parse(SAP_CSV))
        valid = [r for r in rows if r.normalized_data and r.normalized_data.get("co2e_kg")]
        assert len(valid) > 0

    def test_german_date_format_parsed(self):
        parser = SAPFuelParser()
        rows = list(parser.parse(SAP_CSV))
        # Row 2 has date 15.01.2024
        row2 = rows[1]
        assert row2.normalized_data
        assert row2.normalized_data.get("posting_date") == "2024-01-15"


class TestUtilityParser:
    def test_parses_valid_rows(self):
        parser = UtilityElectricityParser()
        rows = list(parser.parse(UTILITY_CSV))
        assert len(rows) == 3

    def test_detects_electricity_spike(self):
        parser = UtilityElectricityParser()
        rows = list(parser.parse(UTILITY_CSV))
        # MTR-001 row 2 (58000 kWh) vs avg should be flagged
        spikes = [
            r for r in rows
            if r.normalized_data and "anomaly_reasons" in r.normalized_data
        ]
        assert len(spikes) >= 1

    def test_kwh_normalization(self):
        parser = UtilityElectricityParser()
        rows = list(parser.parse(UTILITY_CSV))
        first = rows[0]
        assert first.normalized_data
        assert first.normalized_data.get("kwh_usage_normalized") == "15000"


class TestTravelParser:
    def test_parses_valid_rows(self):
        parser = CorporateTravelParser()
        rows = list(parser.parse(TRAVEL_CSV))
        assert len(rows) == 4

    def test_detects_same_airport(self):
        parser = CorporateTravelParser()
        rows = list(parser.parse(TRAVEL_CSV))
        failed = [r for r in rows if r.validation_result.status == ValidationStatus.FAILED]
        assert len(failed) >= 1

    def test_detects_excessive_hotel_nights(self):
        parser = CorporateTravelParser()
        rows = list(parser.parse(TRAVEL_CSV))
        warnings = [
            r for r in rows
            if any(w["code"] == "EXCESSIVE_HOTEL_NIGHTS" for w in r.validation_result.warnings)
        ]
        assert len(warnings) >= 1

    def test_distance_calculated_for_known_airports(self):
        parser = CorporateTravelParser()
        rows = list(parser.parse(TRAVEL_CSV))
        first = rows[0]  # LHR → JFK
        assert first.normalized_data
        dist = first.normalized_data.get("distance_km")
        assert dist is not None
        assert float(dist) > 5000  # LHR-JFK is ~5500km
