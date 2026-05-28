from decimal import Decimal
from typing import Dict, List, Any, Optional

import structlog

logger = structlog.get_logger(__name__)

ELECTRICITY_SPIKE_THRESHOLD = Decimal("2.0")
FUEL_SPIKE_THRESHOLD = Decimal("2.5")
MAX_HOTEL_NIGHTS = 30


class AnomalyDetector:
    """
    Rule-based anomaly detector for ingested records.
    Returns a list of suspicion reason strings.
    """

    @staticmethod
    def check_electricity(record: Dict[str, Any], historical_avg_kwh: Optional[Decimal] = None) -> List[str]:
        reasons = []
        kwh = record.get("kwh_usage_normalized")
        if kwh is None:
            return reasons

        kwh = Decimal(str(kwh))
        if kwh <= 0:
            reasons.append("Zero or negative electricity usage is anomalous.")

        if historical_avg_kwh and historical_avg_kwh > 0:
            ratio = kwh / historical_avg_kwh
            if ratio > ELECTRICITY_SPIKE_THRESHOLD:
                reasons.append(
                    f"Electricity usage ({kwh:.0f} kWh) is {ratio:.1f}x the historical average "
                    f"({historical_avg_kwh:.0f} kWh). Possible data spike."
                )

        if kwh > Decimal("5000000"):
            reasons.append(f"Single-period electricity usage ({kwh:,.0f} kWh) exceeds 5,000,000 kWh threshold.")

        return reasons

    @staticmethod
    def check_fuel(record: Dict[str, Any], historical_avg: Optional[Decimal] = None) -> List[str]:
        reasons = []
        qty = record.get("quantity_normalized")
        if qty is None:
            return reasons

        qty = Decimal(str(qty))
        if qty <= 0:
            reasons.append("Non-positive fuel quantity.")

        if historical_avg and historical_avg > 0:
            ratio = qty / historical_avg
            if ratio > FUEL_SPIKE_THRESHOLD:
                reasons.append(
                    f"Fuel quantity ({qty:.2f}) is {ratio:.1f}x the historical average. Possible spike."
                )

        return reasons

    @staticmethod
    def check_travel(record: Dict[str, Any]) -> List[str]:
        reasons = []

        hotel_nights = record.get("hotel_nights")
        if hotel_nights is not None:
            try:
                nights = int(hotel_nights)
                if nights > MAX_HOTEL_NIGHTS:
                    reasons.append(f"Hotel nights ({nights}) exceeds maximum threshold of {MAX_HOTEL_NIGHTS}.")
            except (ValueError, TypeError):
                pass

        distance_km = record.get("distance_km")
        if distance_km is not None:
            try:
                dist = Decimal(str(distance_km))
                if dist > Decimal("20000"):
                    reasons.append(f"Travel distance ({dist:.0f} km) exceeds 20,000 km — possible data error.")
                if dist < Decimal("10"):
                    reasons.append(f"Travel distance ({dist:.1f} km) is implausibly short for a flight.")
            except Exception:
                pass

        transport_mode = str(record.get("transport_mode", "")).upper()
        travel_class = str(record.get("travel_class", "")).upper()
        if transport_mode != "AIR" and travel_class in ("BUSINESS", "FIRST"):
            reasons.append(
                f"Business/First class booking on non-air transport ({transport_mode}) — verify correctness."
            )

        return reasons

    @staticmethod
    def check_duplicate_invoice(invoice_number: str, vendor_name: str, seen_invoices: set) -> List[str]:
        key = f"{invoice_number}::{vendor_name}".lower()
        if key in seen_invoices:
            return [f"Duplicate invoice number '{invoice_number}' for vendor '{vendor_name}'."]
        seen_invoices.add(key)
        return []
