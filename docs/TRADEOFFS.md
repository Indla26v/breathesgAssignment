# Technical Tradeoffs & Omissions

This document details the intentional tradeoffs, scope boundaries, and architectural omissions in the Breathe ESG Ingestor platform.

---

## 1. No OAuth API Integration (CSV Upload Instead)
- **Tradeoff**: Users must manually drag and drop CSV files from portals rather than using direct API syncs.
- **Why**: Real-world OAuth integrations require complex tenant credentials management, key rotation, token refresh handles, and rate-limiting. For a robust core, manual CSV upload is highly auditable, requires zero IT integration configuration, and allows finance teams to control the data boundary before it enters the platform.

---

## 2. No Emission Factor Application (Stores Activity Data Only)
- **Tradeoff**: The platform does not calculate carbon emissions ($CO_2e$) and only normalizes activity metrics (kWh, Liters, Nights).
- **Why**: Emission factors change constantly based on region and reporting year (e.g. DEFRA, US eGRID, EPA). Combining activity ingestion with calculations leads to version lock. A correct ESG architecture separates **activity normalization** (this platform) from the **calculation engine**, ensuring audit logs contain raw activity data that can be re-calculated if emission factors change.

---

## 3. No Real-time SAP API (Flat File SE16 Instead)
- **Tradeoff**: Ingestion is batch-based rather than real-time via RFC/OData.
- **Why**: Real-time SAP integration requires significant ABAP transport configuration and VPN setups. In production deployments, ESG reporting is a monthly or quarterly retrospective process, meaning real-time sync adds cost and network security risks without business value.

---

## 4. In-Memory Calculations vs. Pandas
- **Tradeoff**: We parse files using Pandas chunking but run normalization row-by-row.
- **Why**: While fully vectorizing conversions in Pandas is faster, row-by-row normalization allows us to write detailed row-level parse logs, attach specific flags, and capture precise error messages. It also ensures the memory footprint remains small and bounded when streaming 50,000+ rows.
