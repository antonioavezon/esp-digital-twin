"""Gobernanza y perfil del dataset 001. No entrena modelos."""

import os
from pathlib import Path

import pytest
from openpyxl import Workbook

from app.research.datasets import dataset_detail, research_status
from app.research.manifest import sha256_file
from app.research.profiling import WorkbookError, profile_sheet, read_workbook


EXPECTED = (
    "Mapping Test Data_zero IPA.xlsx",
    "Surging Test Data_zero IPA.xlsx",
)


def _root() -> Path:
    return Path(os.environ.get("ESP_DATA_ROOT", "/app/data"))


def _write_sheet(path: Path, rows):
    book = Workbook()
    sheet = book.active
    sheet.title = "sample"
    for row in rows:
        sheet.append(list(row))
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)
    book.close()


def test_health_stays_up_when_data_root_is_missing(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path / "missing"))
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert health.json()["stage"] == "2-0"
    status = client.get("/api/v1/research/status")
    assert status.status_code == 200
    body = status.json()
    assert body["availability"] == "dataset_unavailable"
    assert body["ai_model"] is False
    assert body["physics_ai"] is False
    assert body["anomaly_detection"] is False
    assert body["datasets"] == []
    missing = client.get("/api/v1/research/datasets/001")
    assert missing.status_code == 404
    assert missing.json()["error"] == "dataset_unavailable"


def test_missing_workbook_is_controlled(client, monkeypatch, tmp_path):
    folder = tmp_path / "001"
    folder.mkdir()
    _write_sheet(folder / EXPECTED[0], [("a",), (1,)])
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    status = client.get("/api/v1/research/status")
    assert status.json()["availability"] == "dataset_unavailable"
    detail = client.get("/api/v1/research/datasets/001")
    assert detail.status_code == 404
    assert detail.json()["error"] == "dataset_unavailable"


def test_corrupt_workbook_is_controlled(client, monkeypatch, tmp_path):
    folder = tmp_path / "001"
    folder.mkdir()
    _write_sheet(folder / EXPECTED[0], [("a",), (1,)])
    (folder / EXPECTED[1]).write_bytes(b"this is not a workbook")
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    profile = client.get("/api/v1/research/datasets/001/profile")
    assert profile.status_code == 422
    assert profile.json()["error"] == "unreadable_workbook"
    with pytest.raises(WorkbookError):
        read_workbook(folder / EXPECTED[1])


def test_unknown_file_does_not_escape_the_dataset(client, monkeypatch, tmp_path):
    folder = tmp_path / "001"
    folder.mkdir()
    for name in EXPECTED:
        _write_sheet(folder / name, [("h",), (1,)])
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    escaped = client.get(
        "/api/v1/research/datasets/001/preview",
        params={"file": "../secret.xlsx", "sheet": "sample"},
    )
    assert escaped.status_code == 404
    assert escaped.json()["error"] == "unknown_file"


def test_profile_handles_empty_columns_and_odd_values():
    sheet = profile_sheet(
        "sample",
        [
            ("label", "label", None, "note"),
            ("a", "a", None, "b"),
            (1, "text", None, True),
            (3, 4, None, None),
            (None, None, None, None),
        ],
    )
    assert sheet["empty_row_count"] == 1
    block = sheet["blocks"][0]
    assert 3 in block["empty_columns"]
    kinds = {column["index"]: column["inferred_type"] for column in block["columns"]}
    assert kinds[1] == "number"
    assert kinds[2] == "mixed"
    assert kinds[3] == "empty"
    assert "mean" not in block["columns"][1]
    assert block["columns"][0]["mean"] == 2
    assert block["duplicate_headers"]


def test_dataset_001_profile_is_reproducible(client):
    root = _root()
    folder = root / "001"
    paths = [folder / name for name in EXPECTED]
    assert all(path.is_file() for path in paths)
    before = [sha256_file(path) for path in paths]
    status = client.get("/api/v1/research/status")
    assert status.status_code == 200
    assert status.json()["availability"] == "ready"
    assert status.json()["datasets"] == ["001"]
    index = client.get("/api/v1/research/datasets")
    assert index.status_code == 200
    assert index.json()["datasets"][0]["dataset_id"] == "001"
    detail = client.get("/api/v1/research/datasets/001")
    assert detail.status_code == 200
    body = detail.json()
    assert body["source_type"] == "experimental"
    assert body["processing_status"] == "raw"
    assert body["dataset_doi"] == "10.17632/fk2b4r69bs.1"
    assert [item["filename"] for item in body["files"]] == list(EXPECTED)
    for item, digest in zip(body["files"], before, strict=True):
        assert item["sha256"] == digest
        assert item["sha256"] == sha256_file(folder / item["filename"])
        assert [sheet["name"] for sheet in item["sheets"]] == ["50psig", "100psig", "150psig"]
        for sheet in item["sheets"]:
            assert sheet["row_count"] > 0
            assert sheet["column_count"] > 0
            names = [
                column["name"]
                for block in sheet["blocks"]
                for column in block["columns"]
                if column["name"]
            ]
            assert names
            for block in sheet["blocks"]:
                for column in block["columns"]:
                    if column["name"] != "Rotary Speed (rpm)":
                        assert column["unit"] is None
                    else:
                        assert column["unit"] == "rpm"
    profile = client.get("/api/v1/research/datasets/001/profile")
    assert profile.status_code == 200
    assert profile.json()["files"][0]["source_sha256"] == before[0]
    preview = client.get(
        "/api/v1/research/datasets/001/preview",
        params={"file": EXPECTED[0], "sheet": "50psig", "block": 1, "limit": 30},
    )
    assert preview.status_code == 200
    sample = preview.json()
    assert sample["shown"] <= 30
    assert sample["rows"]
    assert [sha256_file(path) for path in paths] == before
    manifest = folder / "manifest.json"
    if manifest.is_file():
        import json

        recorded = json.loads(manifest.read_text(encoding="utf-8"))
        assert [item["sha256"] for item in recorded["files"]] == before


def test_direct_detail_matches_the_mounted_files():
    detail = dataset_detail("001")
    assert detail["processing_status"] == "raw"
    assert research_status()["availability"] == "ready"
