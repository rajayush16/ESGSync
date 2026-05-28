"""
Transformation services: take a mapped raw record dict and produce a normalized dict
ready for EmissionRecord creation.
"""
import math
from decimal import Decimal
from typing import Any, Dict, Optional

import structlog

from apps.common.enums import EmissionScope, EmissionCategory, FuelType, TransportMode, TravelClass
from apps.common.utils import safe_date, safe_decimal
from .unit_converter import UnitConverter

logger = structlog.get_logger(__name__)

# GHG emission factors (kg CO2e per unit of fuel consumed, by fuel type)
# Source: IPCC AR5 GWPs, EPA emission factors
FUEL_EMISSION_FACTORS_KG_CO2E_PER_KG: Dict[str, Decimal] = {
    "diesel": Decimal("3.169"),
    "petrol": Decimal("3.156"),
    "gasoline": Decimal("3.156"),
    "natural gas": Decimal("2.720"),
    "lpg": Decimal("2.983"),
    "heating oil": Decimal("3.069"),
    "coal": Decimal("2.420"),
    "biomass": Decimal("0.0"),  # biogenic carbon neutral
    "kerosene": Decimal("3.160"),
    "jet fuel": Decimal("3.160"),
    "other": Decimal("3.000"),
}

# Grid emission factors (kg CO2e per kWh), regional/market averages
GRID_EMISSION_FACTORS_KG_CO2E_PER_KWH: Dict[str, Decimal] = {
    "default": Decimal("0.4330"),
    "eu": Decimal("0.2760"),
    "us": Decimal("0.3860"),
    "uk": Decimal("0.2330"),
    "de": Decimal("0.3850"),
    "fr": Decimal("0.0680"),
    "cn": Decimal("0.6810"),
    "in": Decimal("0.7080"),
    "au": Decimal("0.6600"),
    "ca": Decimal("0.1400"),
}

# Flight emission factors (kg CO2e per passenger-km) by cabin class and radiative forcing
FLIGHT_EMISSION_FACTORS: Dict[str, Decimal] = {
    "economy": Decimal("0.1530"),
    "premium_economy": Decimal("0.2295"),
    "business": Decimal("0.4285"),
    "first": Decimal("0.5711"),
    "unknown": Decimal("0.1530"),
}

# IATA airport coordinates (representative subset for distance calculations)
AIRPORT_COORDS: Dict[str, tuple[float, float]] = {
    "LHR": (51.4775, -0.4614),
    "JFK": (40.6413, -73.7781),
    "CDG": (49.0097, 2.5479),
    "FRA": (50.0379, 8.5622),
    "AMS": (52.3105, 4.7683),
    "ORD": (41.9742, -87.9073),
    "SIN": (1.3644, 103.9915),
    "DXB": (25.2532, 55.3657),
    "HKG": (22.3080, 113.9185),
    "NRT": (35.7720, 140.3929),
    "SYD": (-33.9461, 151.1772),
    "LAX": (33.9425, -118.4081),
    "MUC": (48.3538, 11.7861),
    "ZRH": (47.4647, 8.5492),
    "BOM": (19.0887, 72.8679),
    "DEL": (28.5562, 77.1000),
    "PEK": (40.0799, 116.6031),
    "GRU": (-23.4356, -46.4731),
    "DFW": (32.8969, -97.0381),
    "ATL": (33.6407, -84.4277),
    "SFO": (37.6189, -122.3750),
    "BOS": (42.3656, -71.0096),
    "MIA": (25.7959, -80.2870),
    "SEA": (47.4502, -122.3088),
    "IAD": (38.9445, -77.4558),
    "EWR": (40.6895, -74.1745),
    "MSP": (44.8848, -93.2223),
    "DTW": (42.2124, -83.3534),
    "BRU": (50.9010, 4.4844),
    "VIE": (48.1102, 16.5697),
    "MAD": (40.4936, -3.5668),
    "BCN": (41.2971, 2.0785),
    "FCO": (41.8003, 12.2389),
    "MXP": (45.6306, 8.7281),
    "CPH": (55.6180, 12.6508),
    "OSL": (60.1976, 11.1004),
    "ARN": (59.6519, 17.9186),
    "HEL": (60.3183, 24.9630),
    "WAW": (52.1657, 20.9671),
    "PRG": (50.1008, 14.2600),
    "BUD": (47.4298, 19.2610),
    "IST": (41.2753, 28.7519),
    "CAI": (30.1219, 31.4056),
    "JNB": (-26.1392, 28.2460),
    "NBO": (-1.3192, 36.9275),
    "CMN": (33.3675, -7.5898),
    "DOH": (25.2607, 51.6138),
    "KUL": (2.7456, 101.7099),
    "BKK": (13.9132, 100.6060),
    "ICN": (37.4602, 126.4407),
    "CGK": (-6.1255, 106.6558),
    "MEL": (-37.6733, 144.8430),
    "AKL": (-37.0082, 174.7850),
    "SCL": (-33.3930, -70.7858),
    "BOG": (4.7016, -74.1469),
    "LIM": (-12.0219, -77.1143),
    "MEX": (19.4363, -99.0721),
    "YYZ": (43.6777, -79.6248),
    "YVR": (49.1939, -123.1844),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def airport_distance_km(iata_a: str, iata_b: str) -> Optional[float]:
    coords_a = AIRPORT_COORDS.get(iata_a.upper())
    coords_b = AIRPORT_COORDS.get(iata_b.upper())
    if coords_a and coords_b:
        return haversine_km(*coords_a, *coords_b)
    return None


class SAPTransformer:
    @staticmethod
    def transform(mapped: Dict[str, Any]) -> Dict[str, Any]:
        quantity_raw = safe_decimal(mapped.get("quantity"))
        unit = str(mapped.get("unit", "")).strip()
        fuel_type = str(mapped.get("fuel_type", "other")).strip().lower()

        quantity_kg: Optional[Decimal] = None
        quantity_liters: Optional[Decimal] = None

        if quantity_raw:
            kg = UnitConverter.to_kg(quantity_raw, unit)
            if kg is not None:
                quantity_kg = kg
            else:
                liters = UnitConverter.to_liters(quantity_raw, unit)
                if liters is not None:
                    quantity_liters = liters
                    quantity_kg = UnitConverter.volume_to_kg(quantity_raw, unit, fuel_type)

        emission_factor = FUEL_EMISSION_FACTORS_KG_CO2E_PER_KG.get(
            fuel_type, FUEL_EMISSION_FACTORS_KG_CO2E_PER_KG["other"]
        )
        co2e_kg: Optional[Decimal] = None
        if quantity_kg:
            co2e_kg = (quantity_kg * emission_factor).quantize(Decimal("0.001"))

        return {
            "invoice_number": str(mapped.get("invoice_number", "")).strip(),
            "vendor_name": str(mapped.get("vendor_name", "")).strip(),
            "plant_code": str(mapped.get("plant_code", "")).strip(),
            "material_description": str(mapped.get("material_description", "")).strip(),
            "quantity_raw": str(quantity_raw) if quantity_raw else None,
            "unit_raw": unit,
            "quantity_normalized_kg": str(quantity_kg) if quantity_kg else None,
            "quantity_liters": str(quantity_liters) if quantity_liters else None,
            "currency": str(mapped.get("currency", "")).strip(),
            "posting_date": str(safe_date(mapped.get("posting_date"))) if mapped.get("posting_date") else None,
            "fuel_type": fuel_type,
            "procurement_category": str(mapped.get("procurement_category", "")).strip(),
            "cost": str(safe_decimal(mapped.get("cost"))) if mapped.get("cost") else None,
            "co2e_kg": str(co2e_kg) if co2e_kg else None,
            "emission_scope": EmissionScope.SCOPE_1,
            "emission_category": EmissionCategory.STATIONARY_COMBUSTION,
        }


class UtilityTransformer:
    @staticmethod
    def transform(mapped: Dict[str, Any]) -> Dict[str, Any]:
        kwh_raw = safe_decimal(mapped.get("kwh_usage"))
        mwh_raw = safe_decimal(mapped.get("mwh_usage"))

        kwh_normalized: Optional[Decimal] = None
        if kwh_raw is not None:
            kwh_normalized = kwh_raw
        elif mwh_raw is not None:
            kwh_normalized = mwh_raw * Decimal("1000")

        region = str(mapped.get("region", "")).strip().lower()
        factor = GRID_EMISSION_FACTORS_KG_CO2E_PER_KWH.get(
            region, GRID_EMISSION_FACTORS_KG_CO2E_PER_KWH["default"]
        )
        co2e_kg: Optional[Decimal] = None
        if kwh_normalized:
            co2e_kg = (kwh_normalized * factor).quantize(Decimal("0.001"))

        return {
            "meter_id": str(mapped.get("meter_id", "")).strip(),
            "facility": str(mapped.get("facility", "")).strip(),
            "billing_period_start": str(safe_date(mapped.get("billing_period_start"))) if mapped.get("billing_period_start") else None,
            "billing_period_end": str(safe_date(mapped.get("billing_period_end"))) if mapped.get("billing_period_end") else None,
            "kwh_usage_normalized": str(kwh_normalized) if kwh_normalized else None,
            "tariff_category": str(mapped.get("tariff_category", "")).strip(),
            "utility_provider": str(mapped.get("utility_provider", "")).strip(),
            "cost": str(safe_decimal(mapped.get("cost"))) if mapped.get("cost") else None,
            "region": region,
            "grid_emission_factor_kg_co2e_per_kwh": str(factor),
            "co2e_kg": str(co2e_kg) if co2e_kg else None,
            "emission_scope": EmissionScope.SCOPE_2,
            "emission_category": EmissionCategory.PURCHASED_ELECTRICITY,
        }


class TravelTransformer:
    @staticmethod
    def transform(mapped: Dict[str, Any]) -> Dict[str, Any]:
        dep = str(mapped.get("departure_airport", "")).strip().upper()
        arr = str(mapped.get("arrival_airport", "")).strip().upper()
        travel_class = str(mapped.get("travel_class", "unknown")).strip().lower().replace(" ", "_")
        transport_mode = str(mapped.get("transport_mode", "air")).strip().upper()

        distance_km = airport_distance_km(dep, arr)

        emission_factor = FLIGHT_EMISSION_FACTORS.get(travel_class, FLIGHT_EMISSION_FACTORS["unknown"])
        co2e_kg: Optional[Decimal] = None
        if distance_km and transport_mode == "AIR":
            co2e_kg = (Decimal(str(distance_km)) * emission_factor).quantize(Decimal("0.001"))

        return {
            "employee_id": str(mapped.get("employee_id", "")).strip(),
            "trip_type": str(mapped.get("trip_type", "")).strip(),
            "departure_airport": dep,
            "arrival_airport": arr,
            "travel_class": travel_class.upper() if travel_class else "UNKNOWN",
            "hotel_nights": str(safe_decimal(mapped.get("hotel_nights"), Decimal("0"))),
            "transport_mode": transport_mode,
            "booking_platform": str(mapped.get("booking_platform", "")).strip(),
            "trip_date": str(safe_date(mapped.get("trip_date"))) if mapped.get("trip_date") else None,
            "distance_km": str(round(distance_km, 2)) if distance_km else None,
            "emission_factor_kg_co2e_per_pkm": str(emission_factor),
            "co2e_kg": str(co2e_kg) if co2e_kg else None,
            "emission_scope": EmissionScope.SCOPE_3,
            "emission_category": EmissionCategory.BUSINESS_TRAVEL,
        }
