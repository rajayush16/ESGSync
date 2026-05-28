# ESGSync — Research & Data Sources

## SAP Fuel & Procurement Data

SAP S/4HANA and SAP ECC export procurement data primarily via:
- **MM Module (Materials Management)**: Purchase orders, goods receipts, invoice verification
- **FI Module (Financial Accounting)**: Posting dates, vendor master data, document numbers
- **PM Module (Plant Maintenance)**: Plant codes, cost centers

Real SAP CSV exports typically include:
- `Buchungsdatum` (Posting Date) in German formats: `DD.MM.YYYY`
- `Belegnummer` (Document/Invoice Number): Internal reference
- `Lieferant` (Vendor): SAP vendor master number or name
- `Werk` (Plant): Plant code (4-character SAP plant identifier)
- `Menge` (Quantity) and `Mengeneinheit` (Unit of Measure): Often SAP internal units (L, KG, ST, M3)
- `Materialbeschreibung` (Material Description): Free-text

The `schema_mapper.py` covers the most common German → English column mappings observed in real SAP export configurations. SAP's standard PO line item report (ME2M/ME2N) is the typical source.

**Real-world limitations modeled in sample data**:
- Quantities with commas as decimal separators (German locale)
- Mixed date formats within a single export (different source users)
- Non-standard units (BARRELS appears in some configurations)
- Missing vendor names (invoice rows from automated procurement)
- Duplicate invoice numbers (SAP allows this across plants)
- Negative quantities (credit memos / returns)

---

## Utility Electricity Data

Utility billing data structure is based on formats from major European and UK energy suppliers:
- **Vattenfall Europe AG** (Germany): Monthly CSV exports with meter ID, facility, period, kWh, cost
- **E.ON SE** (Germany/UK): Similar structure with tariff category breakdowns
- **British Gas Business** (UK): Imperial period formatting (DD/MM/YYYY)
- **EDF Entreprises** (France): Standard EU billing format

Key data characteristics modeled:
- Different date format conventions per country (Germany: DD.MM.YYYY, UK: DD/MM/YYYY, ISO: YYYY-MM-DD)
- kWh vs MWh usage in the same file (large facilities often report in MWh)
- Billing periods that span month boundaries (cross-month billing cycles)
- Zero usage rows (facility shutdown, meter read issue)
- Missing usage values (data not yet available at export time)
- Electricity spikes (test anomaly: Hamburg Distribution Center row with 489,200 kWh — ~3.3x normal)

**Grid emission factors** sourced from:
- EU: IEA Electricity Information (2023 edition)
- Germany: Umweltbundesamt (Federal Environment Agency) 2023 report
- UK: DESNZ/BEIS UK Government GHG Conversion Factors 2023
- France: RTE (Réseau de Transport d'Électricité) 2023 CO₂ intensity

---

## Corporate Travel Data

Corporate travel data structure is based on export formats from:
- **SAP Concur Travel**: The dominant enterprise travel platform. Exports include trip type, routing, class, dates, booking metadata
- **Navan (formerly TripActions)**: JSON or CSV exports with similar fields
- **Egencia (Amex GBT)**: Standard IATA routing with traveler and class detail

Emission calculations follow:
- **GHG Protocol Corporate Value Chain Standard** — Scope 3, Category 6 (Business Travel)
- **DEFRA/BEIS UK Government GHG Conversion Factors 2023** — passenger aviation factors by cabin class
- **ICAO Carbon Emissions Calculator methodology** — radiative forcing multiplier (RF) applied to direct CO₂ to get CO₂e. Factors used include RF at 2.0x for aviation (simplified approach)

Airport distance uses Haversine formula with a curvature-corrected great-circle distance. The sample dataset includes 60+ major airports. Unknown airport pairs return `null` distance; the emission record is still created with a null CO₂e and flagged for review.

**Test anomalies in sample data**:
- `EMP-300412` row 21: Departure and arrival both set to `LHR` (same airport — validation FAILED)
- `EMP-500221` row 25: 45 hotel nights (anomaly flag: EXCESSIVE_HOTEL_NIGHTS warning)
- `EMP-300412` row 21: Employee ID and trip type fields are transposed (realistic data entry error)

---

## Emission Factors Used

| Source | Factor | Reference |
|--------|--------|-----------|
| Diesel (combustion) | 3.169 kg CO₂e/kg | IPCC AR5, EPA AP-42 |
| Petrol/Gasoline | 3.156 kg CO₂e/kg | IPCC AR5 |
| Natural Gas | 2.720 kg CO₂e/kg | IPCC AR5 |
| LPG | 2.983 kg CO₂e/kg | IPCC AR5 |
| Kerosene/Jet A-1 | 3.160 kg CO₂e/kg | IPCC AR5 |
| Germany grid (2023) | 0.385 kg CO₂e/kWh | UBA 2023 |
| UK grid (2023) | 0.233 kg CO₂e/kWh | DESNZ 2023 |
| France grid (2023) | 0.068 kg CO₂e/kWh | RTE 2023 |
| Aviation Economy | 0.153 kg CO₂e/pkm | DEFRA 2023 |
| Aviation Business | 0.429 kg CO₂e/pkm | DEFRA 2023 (×2.8 economy) |
| Aviation First | 0.571 kg CO₂e/pkm | DEFRA 2023 (×3.73 economy) |

All factors are approximations. Production deployment should use annually updated, auditor-certified factor databases (e.g., DEFRA conversion factors, ecoinvent, or customer-specific supplier declarations).
