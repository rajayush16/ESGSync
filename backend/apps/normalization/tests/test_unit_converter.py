from decimal import Decimal

import pytest

from apps.normalization.services.unit_converter import UnitConverter


class TestUnitConverter:
    def test_liters_to_liters(self):
        result = UnitConverter.to_liters(Decimal("100"), "liters")
        assert result == Decimal("100")

    def test_gallons_to_liters(self):
        result = UnitConverter.to_liters(Decimal("10"), "gallons")
        assert result is not None
        assert abs(result - Decimal("37.8541")) < Decimal("0.001")

    def test_kg_to_kg(self):
        result = UnitConverter.to_kg(Decimal("500"), "kg")
        assert result == Decimal("500")

    def test_metric_tons_to_kg(self):
        result = UnitConverter.to_kg(Decimal("2"), "metric tons")
        assert result == Decimal("2000")

    def test_short_tons_to_kg(self):
        result = UnitConverter.to_kg(Decimal("1"), "short tons")
        assert abs(result - Decimal("907.185")) < Decimal("0.001")

    def test_mwh_to_kwh(self):
        result = UnitConverter.to_kwh(Decimal("1"), "MWh")
        assert result == Decimal("1000")

    def test_kwh_to_kwh(self):
        result = UnitConverter.to_kwh(Decimal("500"), "kWh")
        assert result == Decimal("500")

    def test_gj_to_kwh(self):
        result = UnitConverter.to_kwh(Decimal("1"), "GJ")
        assert result is not None
        assert abs(result - Decimal("277.778")) < Decimal("0.01")

    def test_miles_to_km(self):
        result = UnitConverter.to_km(Decimal("1"), "miles")
        assert result is not None
        assert abs(result - Decimal("1.60934")) < Decimal("0.001")

    def test_km_to_km(self):
        result = UnitConverter.to_km(Decimal("100"), "km")
        assert result == Decimal("100")

    def test_unknown_unit_returns_none(self):
        result = UnitConverter.to_liters(Decimal("100"), "furlong")
        assert result is None

    def test_case_insensitive(self):
        assert UnitConverter.to_liters(Decimal("1"), "LITERS") == Decimal("1")
        assert UnitConverter.to_liters(Decimal("1"), "Litres") == Decimal("1")
        assert UnitConverter.to_kg(Decimal("1"), "KG") == Decimal("1")

    def test_volume_to_kg_diesel(self):
        result = UnitConverter.volume_to_kg(Decimal("1000"), "liters", "diesel")
        assert result is not None
        assert result == Decimal("845")  # 1000L * 0.845 kg/L

    def test_german_unit_names(self):
        # German SAP exports may use 'L' directly
        assert UnitConverter.to_liters(Decimal("100"), "l") == Decimal("100")
