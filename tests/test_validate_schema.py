"""Tests for the schema validator, using small generated files."""
import pandas as pd

from src.ingestion.validate_schema import load_contract, validate_file

CONTRACT = load_contract()
HEADERS = ["نوع البلاغ", "الموقع", "حالة البلاغ", "زمن الإغلاق بالساعات", "تاريخ الاستلام", "تكرار البلاغ"]
ROW_A = ["النظافة حاوية ممتلئة", "الملقا", "تم التنفيذ", "5", "2026-01-01 10:00:00", "مكرر"]
ROW_B = ["إنارة شارع مطفأ", "المنار", "3", "18:00 00:00", "2026-06-30", "غير مكرر"]


def make_file(tmp_path, headers, rows):
    """Build a small xlsx with a title row, a header row and data rows."""
    title = ["بلاغات 940"] + [None] * (len(headers) - 1)
    path = tmp_path / "test.xlsx"
    pd.DataFrame([title, headers] + rows).to_excel(path, header=False, index=False)
    return path


def test_layout_a_passes(tmp_path):
    r = validate_file(make_file(tmp_path, HEADERS, [ROW_A]), CONTRACT)
    assert r["status"] == "pass"
    assert r["layout_counts"] == {"A": 1, "B": 0}


def test_layout_b_is_detected(tmp_path):
    r = validate_file(make_file(tmp_path, HEADERS, [ROW_A, ROW_B]), CONTRACT)
    assert r["layout_counts"] == {"A": 1, "B": 1}


def test_location_alias_is_accepted(tmp_path):
    headers = HEADERS.copy()
    headers[1] = "اسم الموقع"
    r = validate_file(make_file(tmp_path, headers, [ROW_A]), CONTRACT)
    assert r["status"] == "pass"


def test_missing_column_fails(tmp_path):
    r = validate_file(make_file(tmp_path, HEADERS[:5], [ROW_A[:5]]), CONTRACT)
    assert r["status"] == "fail"
    assert any("repeat_flag_raw" in e for e in r["errors"])


def test_embedded_header_is_dropped(tmp_path):
    r = validate_file(make_file(tmp_path, HEADERS, [ROW_A, HEADERS, ROW_A]), CONTRACT)
    assert r["embedded_header_rows"] == 1
    assert r["data_rows"] == 2


def test_unknown_status_warns(tmp_path):
    bad = ROW_A.copy()
    bad[2] = "مغلق"
    r = validate_file(make_file(tmp_path, HEADERS, [bad]), CONTRACT)
    assert r["status"] == "pass_with_warnings"
    assert r["invalid_status_in_layout_A"] == 1
