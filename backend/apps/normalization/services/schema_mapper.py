from typing import Dict, Optional

from apps.common.utils import normalize_column_name


# SAP column aliases: maps known variants (including German SAP exports) to canonical names
SAP_COLUMN_ALIASES: Dict[str, str] = {
    # English
    "invoice number": "invoice_number",
    "invoice no": "invoice_number",
    "invoice_number": "invoice_number",
    "invoice_no": "invoice_number",
    "beleg": "invoice_number",
    "belegnummer": "invoice_number",
    "vendor name": "vendor_name",
    "vendor": "vendor_name",
    "lieferant": "vendor_name",
    "lieferantenname": "vendor_name",
    "plant code": "plant_code",
    "plant": "plant_code",
    "werk": "plant_code",
    "werkscode": "plant_code",
    "material description": "material_description",
    "material": "material_description",
    "materialbeschreibung": "material_description",
    "bezeichnung": "material_description",
    "quantity": "quantity",
    "menge": "quantity",
    "qty": "quantity",
    "amount": "quantity",
    "unit": "unit",
    "einheit": "unit",
    "me": "unit",
    "mengeneinheit": "unit",
    "currency": "currency",
    "waehrung": "currency",
    "währung": "currency",
    "posting date": "posting_date",
    "buchungsdatum": "posting_date",
    "belegdatum": "posting_date",
    "date": "posting_date",
    "datum": "posting_date",
    "fuel type": "fuel_type",
    "kraftstoffart": "fuel_type",
    "kraftstoff": "fuel_type",
    "procurement category": "procurement_category",
    "beschaffungskategorie": "procurement_category",
    "kategorie": "procurement_category",
    "cost": "cost",
    "kosten": "cost",
    "betrag": "cost",
}

# Utility electricity column aliases
UTILITY_COLUMN_ALIASES: Dict[str, str] = {
    "meter id": "meter_id",
    "meter_id": "meter_id",
    "meter": "meter_id",
    "account number": "meter_id",
    "account_number": "meter_id",
    "facility": "facility",
    "facility name": "facility",
    "site": "facility",
    "location": "facility",
    "billing period start": "billing_period_start",
    "billing_period_start": "billing_period_start",
    "start date": "billing_period_start",
    "start_date": "billing_period_start",
    "period from": "billing_period_start",
    "billing period end": "billing_period_end",
    "billing_period_end": "billing_period_end",
    "end date": "billing_period_end",
    "end_date": "billing_period_end",
    "period to": "billing_period_end",
    "kwh usage": "kwh_usage",
    "kwh_usage": "kwh_usage",
    "kwh": "kwh_usage",
    "energy usage": "kwh_usage",
    "consumption": "kwh_usage",
    "usage": "kwh_usage",
    "mwh usage": "mwh_usage",
    "mwh_usage": "mwh_usage",
    "mwh": "mwh_usage",
    "tariff category": "tariff_category",
    "tariff": "tariff_category",
    "rate": "tariff_category",
    "utility provider": "utility_provider",
    "provider": "utility_provider",
    "supplier": "utility_provider",
    "utility": "utility_provider",
    "cost": "cost",
    "amount": "cost",
    "bill amount": "cost",
    "region": "region",
    "grid region": "region",
    "area": "region",
}

# Corporate travel column aliases
TRAVEL_COLUMN_ALIASES: Dict[str, str] = {
    "employee id": "employee_id",
    "employee_id": "employee_id",
    "emp id": "employee_id",
    "staff id": "employee_id",
    "user id": "employee_id",
    "trip type": "trip_type",
    "trip_type": "trip_type",
    "type": "trip_type",
    "journey type": "trip_type",
    "departure airport": "departure_airport",
    "departure_airport": "departure_airport",
    "origin": "departure_airport",
    "from airport": "departure_airport",
    "dep airport": "departure_airport",
    "arrival airport": "arrival_airport",
    "arrival_airport": "arrival_airport",
    "destination": "arrival_airport",
    "to airport": "arrival_airport",
    "arr airport": "arrival_airport",
    "travel class": "travel_class",
    "travel_class": "travel_class",
    "class": "travel_class",
    "cabin class": "travel_class",
    "booking class": "travel_class",
    "hotel nights": "hotel_nights",
    "hotel_nights": "hotel_nights",
    "nights": "hotel_nights",
    "accommodation nights": "hotel_nights",
    "transport mode": "transport_mode",
    "transport_mode": "transport_mode",
    "mode": "transport_mode",
    "travel mode": "transport_mode",
    "booking platform": "booking_platform",
    "booking_platform": "booking_platform",
    "platform": "booking_platform",
    "tool": "booking_platform",
    "trip date": "trip_date",
    "trip_date": "trip_date",
    "travel date": "trip_date",
    "date": "trip_date",
    "departure date": "trip_date",
}


class SchemaMapper:
    def __init__(self, alias_map: Dict[str, str]):
        self._alias_map = {normalize_column_name(k): v for k, v in alias_map.items()}

    def map_row(self, raw_row: Dict[str, str]) -> Dict[str, str]:
        mapped = {}
        for key, value in raw_row.items():
            canonical = self._alias_map.get(normalize_column_name(key))
            if canonical:
                mapped[canonical] = value
            else:
                mapped[normalize_column_name(key)] = value
        return mapped

    def map_headers(self, headers: list[str]) -> list[str]:
        return [
            self._alias_map.get(normalize_column_name(h), normalize_column_name(h))
            for h in headers
        ]


SAP_SCHEMA_MAPPER = SchemaMapper(SAP_COLUMN_ALIASES)
UTILITY_SCHEMA_MAPPER = SchemaMapper(UTILITY_COLUMN_ALIASES)
TRAVEL_SCHEMA_MAPPER = SchemaMapper(TRAVEL_COLUMN_ALIASES)
