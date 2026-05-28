from django.db import models


class IngestionStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    VALIDATING = "VALIDATING", "Validating"
    NORMALIZED = "NORMALIZED", "Normalized"
    REVIEW_PENDING = "REVIEW_PENDING", "Review Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    LOCKED_FOR_AUDIT = "LOCKED_FOR_AUDIT", "Locked for Audit"
    FAILED = "FAILED", "Failed"


class DataSourceType(models.TextChoices):
    SAP_FUEL = "SAP_FUEL", "SAP Fuel & Procurement"
    UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility Electricity"
    CORPORATE_TRAVEL = "CORPORATE_TRAVEL", "Corporate Travel"


class EmissionScope(models.TextChoices):
    SCOPE_1 = "SCOPE_1", "Scope 1 — Direct Emissions"
    SCOPE_2 = "SCOPE_2", "Scope 2 — Indirect (Purchased Energy)"
    SCOPE_3 = "SCOPE_3", "Scope 3 — Value Chain"


class EmissionCategory(models.TextChoices):
    STATIONARY_COMBUSTION = "STATIONARY_COMBUSTION", "Stationary Combustion"
    MOBILE_COMBUSTION = "MOBILE_COMBUSTION", "Mobile Combustion"
    FUGITIVE_EMISSIONS = "FUGITIVE_EMISSIONS", "Fugitive Emissions"
    PURCHASED_ELECTRICITY = "PURCHASED_ELECTRICITY", "Purchased Electricity"
    PURCHASED_HEAT = "PURCHASED_HEAT", "Purchased Heat & Steam"
    BUSINESS_TRAVEL = "BUSINESS_TRAVEL", "Business Travel"
    EMPLOYEE_COMMUTING = "EMPLOYEE_COMMUTING", "Employee Commuting"
    UPSTREAM_TRANSPORT = "UPSTREAM_TRANSPORT", "Upstream Transportation"
    WASTE_OPERATIONS = "WASTE_OPERATIONS", "Waste in Operations"
    FUEL_ENERGY = "FUEL_ENERGY", "Fuel- and Energy-Related"


class ValidationStatus(models.TextChoices):
    PASSED = "PASSED", "Passed"
    WARNING = "WARNING", "Warning"
    FAILED = "FAILED", "Failed"
    PENDING = "PENDING", "Pending"


class ReviewDecision(models.TextChoices):
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ESCALATED = "ESCALATED", "Escalated"
    PENDING = "PENDING", "Pending"


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Organization Administrator"
    DATA_MANAGER = "DATA_MANAGER", "Data Manager"
    ANALYST = "ANALYST", "ESG Analyst"
    AUDITOR = "AUDITOR", "Auditor"
    VIEWER = "VIEWER", "Viewer"


class AuditAction(models.TextChoices):
    UPLOAD_CREATED = "UPLOAD_CREATED", "Upload Created"
    RECORD_CREATED = "RECORD_CREATED", "Record Created"
    RECORD_UPDATED = "RECORD_UPDATED", "Record Updated"
    VALIDATION_RUN = "VALIDATION_RUN", "Validation Run"
    NORMALIZATION_RUN = "NORMALIZATION_RUN", "Normalization Run"
    REVIEW_ASSIGNED = "REVIEW_ASSIGNED", "Review Assigned"
    RECORD_APPROVED = "RECORD_APPROVED", "Record Approved"
    RECORD_REJECTED = "RECORD_REJECTED", "Record Rejected"
    RECORD_ESCALATED = "RECORD_ESCALATED", "Record Escalated"
    RECORD_LOCKED = "RECORD_LOCKED", "Record Locked for Audit"
    ANOMALY_FLAGGED = "ANOMALY_FLAGGED", "Anomaly Flagged"
    USER_LOGIN = "USER_LOGIN", "User Login"
    USER_LOGOUT = "USER_LOGOUT", "User Logout"
    EXPORT_CREATED = "EXPORT_CREATED", "Export Created"


class UnitType(models.TextChoices):
    VOLUME_LITERS = "L", "Liters"
    VOLUME_GALLONS = "GAL", "Gallons (US)"
    VOLUME_CUBIC_METERS = "M3", "Cubic Meters"
    MASS_KG = "KG", "Kilograms"
    MASS_METRIC_TONS = "MT", "Metric Tons"
    MASS_SHORT_TONS = "ST", "Short Tons"
    MASS_LBS = "LBS", "Pounds"
    ENERGY_KWH = "KWH", "Kilowatt-Hours"
    ENERGY_MWH = "MWH", "Megawatt-Hours"
    ENERGY_GJ = "GJ", "Gigajoules"
    ENERGY_MMBTU = "MMBTU", "MMBtu"
    DISTANCE_KM = "KM", "Kilometers"
    DISTANCE_MILES = "MILES", "Miles"
    EMISSIONS_KG_CO2E = "KG_CO2E", "kg CO₂e"
    EMISSIONS_MT_CO2E = "MT_CO2E", "Metric Tons CO₂e"


class TransportMode(models.TextChoices):
    AIR = "AIR", "Air"
    RAIL = "RAIL", "Rail"
    CAR = "CAR", "Car / Road"
    BUS = "BUS", "Bus / Coach"
    FERRY = "FERRY", "Ferry"
    TAXI = "TAXI", "Taxi / Rideshare"


class TravelClass(models.TextChoices):
    ECONOMY = "ECONOMY", "Economy"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY", "Premium Economy"
    BUSINESS = "BUSINESS", "Business"
    FIRST = "FIRST", "First Class"
    UNKNOWN = "UNKNOWN", "Unknown"


class FuelType(models.TextChoices):
    DIESEL = "DIESEL", "Diesel"
    PETROL = "PETROL", "Petrol / Gasoline"
    NATURAL_GAS = "NATURAL_GAS", "Natural Gas"
    LPG = "LPG", "Liquefied Petroleum Gas"
    HEATING_OIL = "HEATING_OIL", "Heating Oil"
    COAL = "COAL", "Coal"
    BIOMASS = "BIOMASS", "Biomass"
    KEROSENE = "KEROSENE", "Kerosene / Jet Fuel"
    OTHER = "OTHER", "Other"
