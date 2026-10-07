# Architecture Decisions

## ADR-001: BigQuery Sandbox instead of a billed GCP project

**Context**
Google Cloud billing for accounts in Saudi Arabia must go through a regional
reseller (CNTXT). A personal free-trial billing account was not available.
The me-central2 (Dammam) region was also blocked in the bootcamp project.

**Decision**
Use the BigQuery Sandbox (no billing account, no credit card).

**Consequences**
- No Cloud Storage. The Bronze layer is redesigned:
  - Raw source files are kept unchanged, with a SHA-256 hash in a manifest
    to prove they were not modified.
  - Files are loaded as-is (all columns as text) into a `balagh_bronze` dataset.
- Tables expire after 60 days. The full pipeline can rebuild every layer
  from Bronze with one command, so this is acceptable (and proves reproducibility).
- No DML (INSERT / UPDATE / MERGE). dbt models use `table` and `view`
  materializations only, never `incremental`.

**Datasets**
- balagh_bronze: raw, unchanged, all text + ingestion metadata
- balagh_silver: cleaned, standardized, validated
- balagh_gold: fact, dimensions, KPIs (the dashboard reads from here only)

## ADR-002: Run one Airflow task at a time

**Context**
WSL on this laptop has 3.7 GB of memory. In the first DAG run, two tasks
read large Excel files in parallel while Airflow was running. The scheduler
stopped, and `load_bronze_2026Q2` stayed in "No Status".
Found by checking the Airflow processes: only the dag-processor was running.

**Decision**
Set `AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=1` in `airflow/start_airflow.sh`.

**Consequences**
- The full pipeline runs in about 2 minutes, one task at a time, without failures.
- Re-running is safe because Bronze loads are idempotent (WRITE_TRUNCATE per quarter).
- On a server with more memory, parallel runs can be enabled by changing one line.
