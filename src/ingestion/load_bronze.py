"""Load a validated raw 940 file into the Bronze layer (BigQuery), unchanged.

Usage: python -m src.ingestion.load_bronze data/raw/940_2026Q1.xlsx 2026Q1
"""
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

from src.ingestion.validate_schema import load_contract, map_headers, read_raw, validate_file

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "balagh-510905")
DATASET = "balagh_bronze"
MANIFEST_DIR = Path("data/manifests")


def sha256_of(path):
    """Fingerprint of the file. Same file -> same hash."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_bronze_frame(path, quarter, contract, batch_id, ingested_at, file_hash):
    """Keep every row and every value as stored. Only add lineage metadata."""
    headers, body = read_raw(path, contract)
    mapped, _, _ = map_headers(headers, contract)
    keep = {i: n for i, n in mapped.items() if n}
    df = body[list(keep)].rename(columns=keep)

    first_data_row = contract["file"]["header_row"] + 2   # Excel row numbers start at 1
    df.insert(0, "source_row_number", range(first_data_row, first_data_row + len(df)))
    df["source_file"] = Path(path).name
    df["source_quarter"] = quarter
    df["file_sha256"] = file_hash
    df["batch_id"] = batch_id
    df["ingested_at"] = ingested_at
    return df


def bronze_schema(df):
    """Everything is text, except two metadata columns."""
    types = {"source_row_number": "INT64", "ingested_at": "TIMESTAMP"}
    return [bigquery.SchemaField(c, types.get(c, "STRING")) for c in df.columns]


def load_to_bigquery(df, quarter):
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.raw_940_{quarter.lower()}"
    job_config = bigquery.LoadJobConfig(
        schema=bronze_schema(df),
        write_disposition="WRITE_TRUNCATE",   # re-running replaces the table: idempotent
    )
    client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
    return table_id, client.get_table(table_id).num_rows


def main(path, quarter):
    contract = load_contract()
    report = validate_file(path, contract)
    if report["status"] == "fail":
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit("Validation failed. Nothing was loaded.")

    batch_id = uuid.uuid4().hex[:12]
    ingested_at = pd.Timestamp(datetime.now(timezone.utc))
    file_hash = sha256_of(path)

    df = build_bronze_frame(path, quarter, contract, batch_id, ingested_at, file_hash)
    table_id, rows_loaded = load_to_bigquery(df, quarter)
    if rows_loaded != len(df):
        sys.exit(f"Row count mismatch: file={len(df)} bigquery={rows_loaded}")

    manifest = {
        "batch_id": batch_id,
        "source_quarter": quarter,
        "source_file": Path(path).name,
        "file_sha256": file_hash,
        "ingested_at": ingested_at.isoformat(),
        "table_id": table_id,
        "rows_in_file": len(df),
        "rows_loaded": rows_loaded,
        "validation": {k: report[k] for k in
                       ["status", "embedded_header_rows", "data_rows", "layout_counts", "warnings"]},
    }
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    out = MANIFEST_DIR / f"940_{quarter}.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python -m src.ingestion.load_bronze <file.xlsx> <quarter e.g. 2026Q1>")
    main(sys.argv[1], sys.argv[2])
