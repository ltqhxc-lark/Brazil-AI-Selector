# Changelog

All notable changes to the **Brazil-AI-Selector** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-10

This is the initial stable release of **Brazil-AI-Selector**, delivering a highly professional, enterprise-grade, and SOLID-compliant financial math and tax auditing engine specifically tailored for Brazilian e-commerce operations.

### Added

- **Configuration Layer (Phase 1)**:
  - Robust `settings.yaml` containing localization (BRL currency, pt-BR, America/Sao_Paulo timezone), SQLite configurations, and file directories.
  - Complete, rule-based, zero-hardcoded platform rule registries in `platform_rules.yaml` (Mercado Livre, Shopee, and TikTok Shop).
  - Detailed Brazilian government tax brackets and rules in `taxes_brazil.yaml` (Simples Nacional 6-brackets Anexo I, state and inter-state ICMS matrices, PIS, COFINS, IPI, and Remessa Conforme cross-border import tax guidelines).
- **Database Infrastructure (Phase 2)**:
  - Implemented standard DeclarativeBase on SQLAlchemy 2.x inside `src/database/base.py`.
  - Added robust dynamic absolute path resolution inside `src/database/connection.py` to prevent multiple `.db` duplications.
- **Domain Data Models (Phase 3)**:
  - Created pure data objects (Product, Platform, Fee) as Python `@dataclasses` with comprehensive type-hints, comments, and docstrings.
- **Mathematical and Formatting Utilities (Phase 4)**:
  - Built high-precision financial rounding helpers inside `src/utils/rounding.py` (Banker's, standard half-up, ceiling, floor) using the `decimal` module.
  - Formulated safe currency additions, subtracts, and percentage multiplies in `src/utils/money.py`.
  - Crafted precise metric conversions for weights (`g`, `kg`, `lb`, `oz`) inside `src/utils/weight.py`.
  - Implemented environment-independent localized text formatters (Brazilian Portuguese Dot-Thousand Comma-Decimal style `R$ 1.234,56`) in `src/utils/formatter.py`.
- **Validation and Boundary Guard Rails (Phase 5)**:
  - Designed safe, no-throw validation structures returning `ValidationResult` in `src/validators/`.
  - Implemented input boundary validators for Product fields (SKU/name presence, positive weight/dimensions, non-negative costs) and Platform parameters.
  - Built static configurations file-integrity verifier checking YAML formats and required fields.
- **Core Precision Calculation Engines (Phase 6)**:
  - Implemented detailed `FeeCalculator`, `TaxCalculator`, and `ShippingCalculator` to resolve complex platform commissions, state flow taxes (ICMS), and postal package tiers.
  - Implemented legal "cálculo por dentro" (internal tax base loop) for cross-border Remessa Conforme calculations.
  - Constructed the aggregate `ProfitCalculator` summing up expenses into standard `ProfitResult`.
- **Orchestrated Business Services Layer (Phase 7)**:
  - Encapsulated calculated metrics into localized, high-signal results (`FeeResult`, `TaxResult`).
  - Developed a unified facade `ProfitService` to drive end-to-end profit simulations.
  - Created a rule-based cost heuristic diagnosis engine `AnalysisService` providing operational tips to sellers.
- **Platform Configuration Adapters (Phase 8)**:
  - Designed clean adapters translating raw platform configurations into structured business policies (`FeePolicy`, `ShippingPolicy`, `AffiliatePolicy`, `PromotionPolicy`, etc.).
- **Strategy & Operational Decision Layer (Phase 9)**:
  - Crafted specialized optimization engines for marketplaces comparison, pricing margins, marketing ads, packaging weight-reductions, and supply chain MOQ buffers.
  - Unified decisions inside `RecommendationStrategy` returning `IntegratedBusinessProposal`.
- **Reports Domain Layer (Phase 10)**:
  - Configured 10 distinct, read-only nested Report DTOs (Summary, Tax, Platform, Financial, Pricing, Marketing, Inventory, Warning, Recommendation, and BusinessReport).
  - Built `ReportBuilder`, timezone-safe `ReportFormatter`, and recursive dictionary/JSON `ReportSerializer`.
- **Multi-format Physical Document Exporters (Phase 11)**:
  - Engineered clean JSON and tabular CSV exporters.
  - Designed beautiful Audit-grade spreadsheets using `openpyxl` with styled title blocks, grid lines, and column-width wraps.
  - Implemented elegant PDF whitepaper compiles using `reportlab` (fully localized to Portuguese).
- **FastAPI REST API Layer (Phase 12)**:
  - Provided REST endpoints (`GET /health`, `POST /api/v1/analysis`, `POST /api/v1/reports`, `GET /api/v1/reports/{filename}`).
  - Built global error handling middleware translating validation and business faults.
  - Locked down security with Pydantic boundary bounds and strict anti-path-traversal file download filters.

### Fixed

- **Static Syntax Resolution**:
  - Surgically resolved a critical `SyntaxError` on line 31 in `src/ai/base_llm.py` where conditional inheritance was improperly declared, restoring 100% compilation integrity.
