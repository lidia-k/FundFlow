# Epic 2A — SALT Rules Ingestion & Publishing

> **Goal**: When a user uploads the EY SALT rule workbook (.xlsx/.xlsm), ingest, validate, stage, and publish a versioned Rule Set into the database, and generate a read‑only Resolved Rules table for fast/traceable calculations (to be used by Epic 2B).

---

## 0) Scope & Constraints

* **In-scope**

  * Upload of SALT rule workbook (`.xlsx`, `.xlsm`) and storage of the raw file.
  * Parsing → validation → staging preview → publish workflow.
  * Create authoritative tables: `withholding_rules`, `composite_rules` (kept separate).
  * Generate read‑only **Resolved Rules** table: `state_entity_tax_rules_resolved`.
  * Versioning: `salt_rule_sets` (status: `draft`, `active`, `archived`).
  * Admin-only UI/API.
* **Out-of-scope (Epic 2B)**

  * Applying rules to investor distributions (calculation engine).
* **Assumptions**

  * Timezone for timestamps: **America/Los\_Angeles**.
  * Upload size ≤ 20 MB (configurable), single workbook per rule set.
  * Rates are fractional decimals (e.g., 0.0575 for 5.75%).
  * Thresholds are currency amounts (USD), non-negative.
  * Each state code = 2-letter (50 states + DC).
  * Investor entity type matches Epic 1 enum (canonical codes).

---

## 1) User Stories

1. As **Tax Admin**, I can upload a SALT rule workbook, preview parsed rules, see validation issues, and **publish** a Rule Set for a target **Year/Quarter**.
2. As **Reviewer**, I can compare a draft Rule Set against the currently active one (diff) and confirm activation.
3. As **Engineer**, I can query a simple, read‑only table by `(rule_set_id, state, entity_type)` to retrieve all fields required for both withholding and composite calculations.

---

## 2) Data Model

### 2.1 Reference tables

* **`states`**: `code CHAR(2) PK`, `name TEXT` (51 rows inc. DC).
* **`entity_types`**: canonical set from Epic 1 (code PK, label).

### 2.2 Files & Rule Sets

* **`source_files`** (local path in prototype; S3 later)

  * `id BIGSERIAL PK`
  * `filename TEXT NOT NULL`
  * `filepath TEXT NOT NULL`
  * `sha256 CHAR(64) NOT NULL`
  * `uploaded_at TIMESTAMPTZ NOT NULL`
  * **Unique** on `sha256`
* **`salt_rule_sets`**

  * `id BIGSERIAL PK`
  * `source_file_id BIGINT FK -> source_files(id)`
  * `year INT NOT NULL` (e.g., 2025)
  * `quarter TEXT NOT NULL CHECK (quarter IN ('Q1','Q2','Q3','Q4'))`
  * `effective_from DATE GENERATED ALWAYS AS (CASE quarter WHEN 'Q1' THEN make_date(year,1,1) WHEN 'Q2' THEN make_date(year,4,1) WHEN 'Q3' THEN make_date(year,7,1) ELSE make_date(year,10,1) END) STORED`
  * `effective_to DATE NULL`
  * `status TEXT NOT NULL CHECK (status IN ('draft','active','archived'))`
  * `created_at TIMESTAMPTZ NOT NULL`
  * `updated_at TIMESTAMPTZ NOT NULL`
  * **Partial unique**: one active per period:

    * `UNIQUE (year, quarter) WHERE status = 'active'`

### 2.3 Authoritative rule tables (separate)

* **`withholding_rules`**

  * `id BIGSERIAL PK`
  * `rule_set_id BIGINT FK -> salt_rule_sets(id)`
  * `state_code CHAR(2) FK -> states(code)`
  * `entity_type_code TEXT FK -> entity_types(code)`
  * `rate NUMERIC(7,6) NULL CHECK (rate IS NULL OR rate >= 0)`
  * `income_threshold NUMERIC(18,2) NULL CHECK (income_threshold IS NULL OR income_threshold >= 0)`
  * `tax_threshold NUMERIC(18,2) NULL CHECK (tax_threshold IS NULL OR tax_threshold >= 0)`
  * `UNIQUE (rule_set_id, state_code, entity_type_code)`
* **`composite_rules`**

  * `id BIGSERIAL PK`
  * `rule_set_id BIGINT FK -> salt_rule_sets(id)`
  * `state_code CHAR(2) FK -> states(code)`
  * `entity_type_code TEXT FK -> entity_types(code)`
  * `rate NUMERIC(7,6) NULL CHECK (rate IS NULL OR rate >= 0)`
  * `income_threshold NUMERIC(18,2) NULL CHECK (income_threshold IS NULL OR income_threshold >= 0)`
  * `mandatory BOOLEAN NULL`
  * `UNIQUE (rule_set_id, state_code, entity_type_code)`

### 2.4 Resolved Rules (derived, read‑only)

* **`state_entity_tax_rules_resolved`**

  * `rule_set_id BIGINT NOT NULL`
  * `state_code CHAR(2) NOT NULL`
  * `entity_type_code TEXT NOT NULL`
  * `withholding_rate NUMERIC(7,6) NULL`
  * `withholding_income_threshold NUMERIC(18,2) NULL`
  * `withholding_tax_threshold NUMERIC(18,2) NULL`
  * `composite_rate NUMERIC(7,6) NULL`
  * `composite_income_threshold NUMERIC(18,2) NULL`
  * `composite_mandatory BOOLEAN NULL`
  * `source_withholding_id BIGINT NULL`
  * `source_composite_id BIGINT NULL`
  * **PK** `(rule_set_id, state_code, entity_type_code)`
  * **Index** `(rule_set_id, state_code, entity_type_code)`

---

## 3) Workbook Expectations & Parsing

### 3.1 Accepted formats

* `.xlsx`, `.xlsm` only; reject others.

### 3.2 Sheet layout (flexible headers with normalization)

* **Withholding sheet** (example expected columns):

  * `State`, `Entity Type`, `Rate`, `Income Threshold`, `Tax Threshold`
* **Composite sheet** (example expected columns):

  * `State`, `Entity Type`, `Rate`, `Income Threshold`, `Mandatory` (TRUE/FALSE/blank)

**Header normalization**

* Trim, case-insensitive, collapse internal whitespace; convert newlines to single spaces.
* Map synonyms (e.g., `Entity`, `Entity Type` → `Entity Type`; `Income Thresh.` → `Income Threshold`).

### 3.3 Value parsing

* **State**: 2-letter code; map full names to codes (e.g., "Colorado" → `CO`).
* **Entity Type**: must match canonical codes (Epic 1 enum); allow label→code mapping table.
* **Numbers**: allow thousands separators, leading/trailing spaces; parentheses mean negative → **reject** (rates/thresholds must be ≥ 0). Blank ⇒ `NULL`.
* **Booleans**: `TRUE/FALSE/Yes/No/1/0` → boolean; blank ⇒ `NULL`.

---

## 4) Validation Rules

* **File-level**

  * Idempotency: compute `sha256`; if identical file already imported for same Year/Quarter → **no-op** with info banner.
  * Required sheets present; otherwise `MISSING_SHEET` error.
* **Row-level** (both sheets)

  * `state_code` in `states`.
  * `entity_type_code` in `entity_types`.
  * No duplicates within a sheet for `(state, entity_type)`; otherwise `DUPLICATE_RULE`.
  * Rate/thresholds must be non-negative numbers; otherwise `INVALID_NUMBER`.
* **Cross-table**

  * Optional policy: enforce full coverage (e.g., each state×entity present in at least one regime). Gaps → `COVERAGE_GAP` warning/error per policy.

**Issues output format**

* `{row, sheet, state_code?, entity_type_code?, code, message, severity}`; downloadable as CSV.

---

## 5) Workflow (States)

1. **Upload** (Admin)

   * Inputs: file, Year, Quarter.
   * Persist `source_files` row; create `salt_rule_sets` with `status='draft'`.
2. **Parse & Validate**

   * Parse sheets into memory; normalize headers/values.
   * Emit issues; block publish if there are any `error` severity items.
3. **Stage**

   * Write parsed rows into `withholding_rules` & `composite_rules` (under the **draft** rule\_set).
   * Show **diff** vs current active (added/changed/removed by `(state, entity)`), field-level.
4. **Publish** (Admin-confirm)

   * If an active Rule Set exists for the same period, either reject or auto-archive it (configurable).
   * Mark previous active `effective_to = (new.effective_from - 1 day)`.
   * Mark new Rule Set `status='active'`.
   * **Build Resolved Rules** (see §6) atomically in the same transaction.
5. **Archive** (optional)

   * Ability to archive an active Rule Set (with guardrails—must first activate a replacement).

---

## 6) Admin UI

* **Upload panel**: file chooser (accept .xlsx/.xlsm), Year, Quarter; progress bar (queued→uploading→parsing→validating→staging→published/error).
* **Validation results**: issue grid with filters (severity/code), CSV export.
* **Draft preview**: table view of parsed rules; search by state/entity.
* **Diff vs active**: chips for Added/Changed/Removed at `(state, entity)` granularity; field-level change highlights.
* **Publish button** (guarded): disabled if any `error` issues exist.
* **History**: list of Rule Sets with status and period; ability to view resolved snapshot.

---

## 7) Acceptance Criteria

### AC 1 — File Upload & Storage

* Accept only `.xlsx`/`.xlsm`. Other types → `UNSUPPORTED_FILE_TYPE` (error).
* Compute `sha256`; if an identical file already exists for the same Year/Quarter, return `IDEMPOTENT_NOOP` and do not create a new draft.
* Persist `source_files` and `salt_rule_sets(status='draft')`.

### AC 2 — Parsing & Normalization

* Header normalization handles case/whitespace/newlines and known synonyms.
* Map state names↔codes; map entity labels→canonical codes.
* Number parsing accepts commas/spaces; parentheses (negatives) rejected with `INVALID_NUMBER`.

### AC 3 — Validation

* Duplicate `(state, entity)` within a sheet is rejected with `DUPLICATE_RULE`.
* Unknown `state` or `entity` → `UNKNOWN_REFERENCE` (error).
* Negative rates/thresholds → `INVALID_NUMBER` (error).
* Missing required sheets → `MISSING_SHEET` (error).
* Issues available as downloadable CSV; publish blocked while any `error` exists.

### AC 4 — Staging & Diff

* On successful validation, rules are saved under the **draft** rule\_set.
* The system shows a diff vs the **active** rule\_set at `(state, entity)` with field-level changes.

### AC 5 — Publish & Versioning

* Publish flips the new Rule Set to `active` and (optionally) sets the prior active's `effective_to` to the day before the new `effective_from`.
* Activation builds **Resolved Rules** in the same transaction.
* Exactly **one active** rule\_set per `(year, quarter)` is enforced by constraint.

### AC 6 — Resolved Rules Table

* After publish, `state_entity_tax_rules_resolved` contains exactly the union of keys from both regimes.
* Each row includes provenance: `source_withholding_id` and/or `source_composite_id`.
* PK/Index `(rule_set_id, state_code, entity_type_code)` exists.

### AC 7 — Observability & Audit

* Store an audit event for import and publish (who/when/file/rule\_set).
* Metrics for import durations, row counts, and issue counts are emitted.

---

## 14) Definition of Done

* Admin can import a workbook, see/resolve validation issues, stage a draft, and publish it.
* DB contains authoritative tables (separate) and a built **Resolved Rules** snapshot for the active set.
* Diff vs active works; audit trail and error codes function as specified.
* API surfaces the active rule\_set and Resolved Rules for Epic 2B.