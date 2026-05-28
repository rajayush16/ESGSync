from decimal import Decimal
from typing import Optional


class UnitConverter:
    """
    Centralized unit conversion for ESG data normalization.
    All conversions target canonical units:
      - Volume  → Liters
      - Mass    → Kilograms
      - Energy  → kWh
      - Distance → Kilometers
      - Emissions → kg CO2e
    """

    # Volume → Liters
    VOLUME_TO_LITERS: dict[str, Decimal] = {
        "l": Decimal("1"),
        "liter": Decimal("1"),
        "liters": Decimal("1"),
        "litre": Decimal("1"),
        "litres": Decimal("1"),
        "gal": Decimal("3.78541"),
        "gallon": Decimal("3.78541"),
        "gallons": Decimal("3.78541"),
        "us gal": Decimal("3.78541"),
        "imperial gal": Decimal("4.54609"),
        "m3": Decimal("1000"),
        "cubic meter": Decimal("1000"),
        "cubic meters": Decimal("1000"),
        "cubic metre": Decimal("1000"),
        "cubic metres": Decimal("1000"),
        "cm3": Decimal("0.001"),
        "ml": Decimal("0.001"),
    }

    # Mass → Kilograms
    MASS_TO_KG: dict[str, Decimal] = {
        "kg": Decimal("1"),
        "kilogram": Decimal("1"),
        "kilograms": Decimal("1"),
        "g": Decimal("0.001"),
        "gram": Decimal("0.001"),
        "grams": Decimal("0.001"),
        "t": Decimal("1000"),
        "mt": Decimal("1000"),
        "metric ton": Decimal("1000"),
        "metric tons": Decimal("1000"),
        "tonne": Decimal("1000"),
        "tonnes": Decimal("1000"),
        "ton": Decimal("1000"),
        "tons": Decimal("1000"),
        "st": Decimal("907.185"),
        "short ton": Decimal("907.185"),
        "short tons": Decimal("907.185"),
        "lb": Decimal("0.453592"),
        "lbs": Decimal("0.453592"),
        "pound": Decimal("0.453592"),
        "pounds": Decimal("0.453592"),
    }

    # Energy → kWh
    ENERGY_TO_KWH: dict[str, Decimal] = {
        "kwh": Decimal("1"),
        "kilowatt-hour": Decimal("1"),
        "kilowatt hours": Decimal("1"),
        "kw h": Decimal("1"),
        "mwh": Decimal("1000"),
        "megawatt-hour": Decimal("1000"),
        "megawatt hours": Decimal("1000"),
        "gwh": Decimal("1000000"),
        "gj": Decimal("277.778"),
        "gigajoule": Decimal("277.778"),
        "gigajoules": Decimal("277.778"),
        "mj": Decimal("0.277778"),
        "j": Decimal("0.000000277778"),
        "mmbtu": Decimal("293.071"),
        "btu": Decimal("0.000293071"),
        "therm": Decimal("29.3071"),
        "therms": Decimal("29.3071"),
    }

    # Distance → Kilometers
    DISTANCE_TO_KM: dict[str, Decimal] = {
        "km": Decimal("1"),
        "kilometer": Decimal("1"),
        "kilometers": Decimal("1"),
        "kilometre": Decimal("1"),
        "kilometres": Decimal("1"),
        "mi": Decimal("1.60934"),
        "mile": Decimal("1.60934"),
        "miles": Decimal("1.60934"),
        "nm": Decimal("1.852"),
        "nautical mile": Decimal("1.852"),
        "nautical miles": Decimal("1.852"),
        "m": Decimal("0.001"),
        "meter": Decimal("0.001"),
        "meters": Decimal("0.001"),
        "ft": Decimal("0.0003048"),
        "feet": Decimal("0.0003048"),
    }

    @classmethod
    def _normalize_unit(cls, unit: str) -> str:
        return unit.strip().lower().replace("-", " ").replace("_", " ")

    @classmethod
    def to_liters(cls, value: Decimal, unit: str) -> Optional[Decimal]:
        factor = cls.VOLUME_TO_LITERS.get(cls._normalize_unit(unit))
        return value * factor if factor is not None else None

    @classmethod
    def to_kg(cls, value: Decimal, unit: str) -> Optional[Decimal]:
        factor = cls.MASS_TO_KG.get(cls._normalize_unit(unit))
        return value * factor if factor is not None else None

    @classmethod
    def to_kwh(cls, value: Decimal, unit: str) -> Optional[Decimal]:
        factor = cls.ENERGY_TO_KWH.get(cls._normalize_unit(unit))
        return value * factor if factor is not None else None

    @classmethod
    def to_km(cls, value: Decimal, unit: str) -> Optional[Decimal]:
        factor = cls.DISTANCE_TO_KM.get(cls._normalize_unit(unit))
        return value * factor if factor is not None else None

    @classmethod
    def volume_to_kg(cls, value: Decimal, unit: str, fuel_type: str) -> Optional[Decimal]:
        """Convert volumetric fuel measurement to kilograms using density factors."""
        liters = cls.to_liters(value, unit)
        if liters is None:
            return None
        density = cls._fuel_density_kg_per_liter(fuel_type)
        return liters * density

    # Approximate fuel densities (kg/L)
    FUEL_DENSITIES: dict[str, Decimal] = {
        "diesel": Decimal("0.845"),
        "petrol": Decimal("0.745"),
        "gasoline": Decimal("0.745"),
        "kerosene": Decimal("0.800"),
        "jet fuel": Decimal("0.800"),
        "lpg": Decimal("0.540"),
        "natural gas": Decimal("0.000717"),  # at standard conditions (kg/L gas)
        "heating oil": Decimal("0.850"),
        "coal": Decimal("0.850"),
        "biomass": Decimal("0.600"),
    }

    @classmethod
    def _fuel_density_kg_per_liter(cls, fuel_type: str) -> Decimal:
        return cls.FUEL_DENSITIES.get(fuel_type.lower().strip(), Decimal("0.845"))
