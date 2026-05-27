# Data Formats & Reference Sources

This document details the documentation sources, real-world schemas, and real-world edge cases considered in the parser designs.

---

## 1. SAP SE16 Table Structures (MSEG & EKPO)
- **Consulted Specifications**:
  - `MSEG` (Material Document Segment): Key columns are `BWART` (Movement Type), `MENGE` (Quantity), `ERFME` (Unit of Entry), `BUDAT` (Posting Date), and `MATNR` (Material Number).
  - `EKPO` (Purchasing Document Item): Tracks purchase logs, including `WERKS` (Plant) and `NETPR` (Net Price).
- **Real-World Edge Cases**:
  - **German Headers**: SAP exports often use German headers depending on the user session locale (e.g. `Menge` for quantity, `Mengeneinheit` or `MEINS` for unit, `Werk` for plant).
  - **Leading Zeroes**: SAP pads material numbers with leading zeroes (e.g. `000000000050045`), which must be stripped before prefix matching.

---

## 2. Utility Bill Formats (PG&E & Duke Energy)
- **Consulted Specifications**:
  - PG&E and Duke Energy export billing logs using Green Button XML/CSV.
  - Invoices do **not** align to calendar months; billing periods (e.g. May 14 to June 13) must be parsed and split.
- **Real-World Edge Cases**:
  - **Overlapping Dates**: Due to manual meter corrections, utility CSV exports often repeat periods or contain overlapping corrections, requiring `DUPLICATE_PERIOD` detection.
  - **Unit Column Headings**: Headers often wrap units in parenthesis (e.g. `Usage (kWh)`), requiring regex extractions.

---

## 3. Concur Travel Reports
- **Consulted Specifications**:
  - Concur Standard Detail Report CSV exports.
  - Expense categories include: Airfare (flight), Hotel (nights), Car Rental (distance or days).
- **Real-World Edge Cases**:
  - **Missing Flight Distance**: Concur files regularly omit mileage. We resolve this by referencing origin/destination IATA codes against the OpenFlights dataset.
  - **Flight Multipliers**: Airline emissions are affected by cabin class (e.g. Business class has a larger physical footprint due to seat size). We extract ticket class for downstream multiplier calculations.

---

## 4. OpenFlights Dataset
- **Consulted Specifications**:
  - OpenFlights `airports.dat` contains latitude, longitude, and IATA codes for over 7,000 global airports.
  - Calculated using the Haversine formula:
    $$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
