"""Validate a raw 940 file against the data contract.

Structure checks only: no cleaning, no type conversion.
Usage: python -m src.ingestion.validate_schema data/raw/940_2026Q1.xlsx
"""
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

DEFAULT_CONTRACT = Path("config/contract_940.yml")


def load_contract(path=DEFAULT_CONTRACT):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_raw(path, contract):
    """Read the first sheet as text, exactly as stored in the file."""
    raw = pd.read_excel(path, sheet_name=0, header=None, dtype=str)
    header_row = contract["file"]["header_row"]
    headers = [str(h).strip() for h in raw.iloc[header_row]]
    body = raw.iloc[header_row + 1:].reset_index(drop=True)
    return headers, body


def map_headers(headers, contract):
    """Match source headers to internal names using the contract aliases."""
    alias_to_name = {
        alias: name
        for name, spec in contract["columns"].items()
        for alias in spec["aliases"]
    }
    mapped = {i: alias_to_name.get(h) for i, h in enumerate(headers)}
    found = {n for n in mapped.values() if n}
    missing = [n for n, s in contract["columns"].items() if s["required"] and n not in found]
    unexpected = [headers[i] for i, n in mapped.items() if n is None]
    return mapped, missing, unexpected


def validate_file(path, contract):
    report = {"file": str(path), "status": "pass", "errors": [], "warnings": []}
    headers, body = read_raw(path, contract)
    report["headers_found"] = headers

    # 1) Structure
    expected = contract["file"]["expected_column_count"]
    if len(headers) != expected:
        report["errors"].append(f"column count {len(headers)} != expected {expected}")

    mapped, missing, unexpected = map_headers(headers, contract)
    if missing:
        report["errors"].append(f"missing required columns: {missing}")
    if unexpected:
        report["warnings"].append(f"unexpected columns (not loaded): {unexpected}")
    if report["errors"]:
        report["status"] = "fail"
        return report

    keep = {i: n for i, n in mapped.items() if n}
    df = body[list(keep)].rename(columns=keep)
    df = df.apply(lambda s: s.str.strip())

    # 2) Embedded header rows and empty rows
    issue_aliases = contract["columns"]["issue_type_raw"]["aliases"]
    embedded = df["issue_type_raw"].isin(issue_aliases)
    empty = df.isna().all(axis=1)
    report["embedded_header_rows"] = int(embedded.sum())
    report["empty_rows"] = int(empty.sum())
    df = df[~embedded & ~empty]
    report["data_rows"] = len(df)

    # 3) Row layouts (detected from content, not from headers)
    b = contract["layouts"]["B"]
    is_b = df[b["detect_column"]].str.match(b["detect_pattern"], na=False)
    report["layout_counts"] = {"A": int((~is_b).sum()), "B": int(is_b.sum())}

    # 4) Accepted values
    acc = contract["accepted_values"]
    status_a = df.loc[~is_b, "status_slot_raw"].dropna()
    bad_status = status_a[~status_a.isin(acc["status_ar"])]
    bad_repeat = df["repeat_flag_raw"][~df["repeat_flag_raw"].isin(acc["repeat_flag_ar"])]
    report["invalid_status_in_layout_A"] = int(len(bad_status))
    report["invalid_repeat_flag"] = int(len(bad_repeat))
    if len(bad_status):
        report["warnings"].append(
            f"{len(bad_status)} layout-A rows with unknown status, e.g. {bad_status.unique()[:5].tolist()}")
    if len(bad_repeat):
        report["warnings"].append(
            f"{len(bad_repeat)} rows with unknown repeat flag, e.g. {bad_repeat.unique()[:5].tolist()}")

    if report["warnings"]:
        report["status"] = "pass_with_warnings"
    return report


if __name__ == "__main__":
    contract = load_contract()
    exit_code = 0
    for p in sys.argv[1:]:
        r = validate_file(p, contract)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if r["status"] == "fail":
            exit_code = 1
    sys.exit(exit_code)
