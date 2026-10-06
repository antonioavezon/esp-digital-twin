"""Ingesta y perfil estructural. No mapea variables ni entrena modelos."""

import json
import zipfile
from pathlib import Path

from openpyxl import Workbook

from app.research.ingest import bootstrap_dataset_001
from app.research.manifest import sha256_file
from app.research.registry import scan
from app.research.structure import neutralize_spreadsheet_formula

EXPECTED = (
    "Mapping Test Data_zero IPA.xlsx",
    "Surging Test Data_zero IPA.xlsx",
)


def _post_files(client, files):
    return client.post("/api/v1/research/intake", files=files)


def _file(name, content, content_type="text/csv"):
    return ("files", (name, content, content_type))


def _import(client, intake_id, **extra):
    payload = {"intake_id": intake_id, "acknowledge_duplicates": False}
    payload.update(extra)
    return client.post("/api/v1/research/datasets/import", json=payload)


def _workbook(path: Path, rows, merges=None, formula=None):
    book = Workbook()
    sheet = book.active
    sheet.title = "sample"
    for row in rows:
        sheet.append(list(row))
    if merges:
        for item in merges:
            sheet.merge_cells(item)
    if formula:
        sheet["A10"] = formula
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)
    book.close()


def test_csv_tsv_json_and_xlsx_import(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    csv_body = b"Flow rate ,Pressure (psi),\n1,10,\n,,\n2,3,\n"
    tsv_body = b"a\tb\n1\t2\n"
    json_body = b'[{"x": 1}, {"x": null}]'
    book = tmp_path / "blocks.xlsx"
    _workbook(
        book,
        [
            ("Speed", "Flow rate ", None, "Speed", "Flow rate "),
            (1, 2, None, 3, 4),
            (None, None, None, None, None),
            ("Speed", "Pressure (psi)", None, None, None),
            (5, 6, None, None, None),
        ],
        merges=["F1:G1"],
        formula="=1+1",
    )
    response = _post_files(
        client,
        [
            _file("medicion.csv", csv_body),
            _file("tabla.tsv", tsv_body, "text/tab-separated-values"),
            _file("notas.json", json_body, "application/json"),
            _file(
                "bloques.xlsx",
                book.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        ],
    )
    assert response.status_code == 200
    intake = response.json()
    assert intake["status"] == "validated"
    assert intake["schema_version"] == "1.0"
    imported = _import(client, intake["intake_id"], title="Prueba", author="Ada")
    assert imported.status_code == 200
    dataset_id = imported.json()["dataset_id"]
    assert dataset_id == "001"
    raw_dir = tmp_path / "datasets" / "001" / "raw"
    stored = {path.name: path.read_bytes() for path in raw_dir.iterdir()}
    assert stored["medicion.csv"] == csv_body
    assert stored["tabla.tsv"] == tsv_body
    assert stored["notas.json"] == json_body
    assert stored["bloques.xlsx"] == book.read_bytes()
    manifest = json.loads((tmp_path / "datasets" / "001" / "metadata" / "manifest.json").read_text())
    preprocess = json.loads((tmp_path / "datasets" / "001" / "metadata" / "preprocess.json").read_text())
    assert manifest["schema_version"] == "1.0"
    assert preprocess["schema_version"] == "1.0"
    assert manifest["distribution"] == "unknown"
    assert manifest["source"]["author"] == "Ada"
    assert manifest["source"]["license"] is None
    assert manifest["source"]["organization"] is None
    assert preprocess["semantic_mapping"]["status"] == "not_started"
    assert preprocess["profiler"]["name"] == "esp-structural-profiler"
    assert preprocess["profiler"]["version"] == "0.1"
    by_name = {item["original_filename"]: item for item in preprocess["files"]}
    csv_headers = by_name["medicion.csv"]["structure"]["tabular"]["headers"]
    flow = csv_headers[0]
    pressure = csv_headers[1]
    assert flow["raw_name"] == "Flow rate "
    assert flow["normalized_name"] == "flow_rate"
    assert flow["normalized_name"] != "liquid_flow_rate"
    assert flow["unit"] is None
    assert flow["canonical_variable"] is None
    assert flow["mapping_status"] == "pending"
    assert pressure["unit"] == "psi"
    assert by_name["medicion.csv"]["structure"]["tabular"]["empty_columns"]
    assert by_name["medicion.csv"]["structure"]["tabular"]["empty_row_count"] >= 1
    assert by_name["tabla.tsv"]["structure"]["tabular"]["delimiter"] == "\t"
    described = by_name["notas.json"]["structure"]["json"]
    assert described["root_type"] == "array"
    assert described["possible_tabular_records"] is True
    assert described["null_count"] >= 1
    assert "rows" not in described
    workbook = by_name["bloques.xlsx"]["structure"]["workbook"]
    assert workbook["formulas_evaluated"] is False
    assert workbook["formula_count"] >= 1
    sheet = workbook["sheets"][0]
    assert sheet["block_count"] >= 2
    assert sheet["repeated_headers"] is True
    assert sheet["empty_row_count"] >= 1
    assert any(block["empty_columns"] for block in sheet["blocks"])
    blob = json.dumps(preprocess)
    assert "Q_L" not in blob
    assert "liquid_flow_rate" not in blob
    listed = client.get("/api/v1/research/datasets")
    assert listed.status_code == 200
    assert listed.json()["datasets"][0]["dataset_id"] == "001"
    assert client.get("/api/v1/research/datasets/001/manifest").status_code == 200
    assert client.get("/api/v1/research/datasets/001/preprocess").status_code == 200


def test_reprofile_does_not_change_raw(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    body = b"a,b\n1,2\n"
    intake = _post_files(client, [_file("uno.csv", body)]).json()
    imported = _import(client, intake["intake_id"])
    dataset_id = imported.json()["dataset_id"]
    raw = tmp_path / "datasets" / dataset_id / "raw" / "uno.csv"
    before = raw.read_bytes()
    digest = sha256_file(raw)
    first = client.post(f"/api/v1/research/datasets/{dataset_id}/reprofile")
    assert first.status_code == 200
    second = client.post(f"/api/v1/research/datasets/{dataset_id}/reprofile")
    assert second.status_code == 200
    assert raw.read_bytes() == before
    assert sha256_file(raw) == digest
    assert second.json()["previous_profiler_version"] == "0.1"
    assert second.json()["files"][0]["generated_from_sha256"] == digest


def test_duplicate_sha_warns_and_does_not_copy(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    body = b"a,b\n1,2\n"
    first = _post_files(client, [_file("uno.csv", body)]).json()
    imported = _import(client, first["intake_id"])
    assert imported.status_code == 200
    second = _post_files(client, [_file("otro.csv", body)])
    assert second.status_code == 200
    assert second.json()["files"][0]["duplicates"][0]["dataset_id"] == "001"
    refused = _import(client, second.json()["intake_id"])
    assert refused.status_code == 409
    assert "Este archivo ya existe en Dataset 001" in refused.json()["message"]
    linked = _import(client, second.json()["intake_id"], acknowledge_duplicates=True)
    assert linked.status_code == 200
    assert linked.json()["dataset_id"] == "002"
    raws = list((tmp_path / "datasets").glob("*/raw/*"))
    assert len(raws) == 1
    manifest = json.loads((tmp_path / "datasets" / "002" / "metadata" / "manifest.json").read_text())
    assert manifest["files"][0]["linked_from"] == "001"


def test_multiple_controls_do_not_crash(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr("app.research.ingest.max_upload_bytes", lambda: 64)
    cases = [
        ("vacio.csv", b""),
        ("malo.exe", b"abc"),
        ("roto.xlsx", b"this is not a workbook"),
        ("zip-falso.csv", b"PK\x03\x04xxxx"),
        ("roto.json", b"{"),
        ("raro.csv", b"a,b\n\xff,1\n"),
        ("grande.csv", b"a" * 80),
    ]
    for name, content in cases:
        response = _post_files(client, [_file(name, content)])
        assert response.status_code == 200
        item = response.json()["files"][0]
        assert item["status"] == "error"
        assert item["errors"]
    broken = tmp_path / "datasets" / "999"
    (broken / "metadata").mkdir(parents=True)
    (broken / "metadata" / "manifest.json").write_text("{", encoding="utf-8")
    (tmp_path / "datasets" / ".oculto").mkdir()
    listed = client.get("/api/v1/research/datasets")
    assert listed.status_code == 200
    assert listed.json()["datasets"] == []
    assert listed.json()["errors"]
    missing = client.get("/api/v1/research/datasets/999")
    assert missing.status_code == 404
    records, errors = scan(tmp_path)
    assert records == []
    assert errors


def test_next_dataset_id_after_001(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    for name in EXPECTED:
        _workbook(tmp_path / "001" / name, [("h",), (1,)])
    intake = _post_files(client, [_file("nuevo.csv", b"a,b\n1,2\n")]).json()
    imported = _import(client, intake["intake_id"])
    assert imported.status_code == 200
    assert imported.json()["dataset_id"] == "002"


def test_bootstrap_keeps_dataset_001_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    paths = []
    for name in EXPECTED:
        path = tmp_path / "001" / name
        _workbook(path, [("Rotary Speed (rpm)", "Flow rate "), (1800, 1)])
        paths.append(path)
    before = [path.read_bytes() for path in paths]
    manifest = bootstrap_dataset_001(tmp_path)
    assert [path.read_bytes() for path in paths] == before
    assert manifest["dataset_id"] == "001"
    assert manifest["distribution"] == "public"
    assert manifest["source"]["doi"] == "10.17632/fk2b4r69bs.1"
    assert manifest["source"]["article_doi"] == "10.1016/j.petrol.2019.05.059"
    assert manifest["source"]["license"] is None
    assert manifest["imported_at"] is None
    preprocess = json.loads((tmp_path / "datasets" / "001" / "metadata" / "preprocess.json").read_text())
    assert preprocess["semantic_mapping"]["status"] == "not_started"
    assert preprocess["files"][0]["generated_from_sha256"] == sha256_file(paths[0])


def test_csv_formula_neutralizer_does_not_touch_source_bytes():
    assert neutralize_spreadsheet_formula("=1+1") == "'=1+1"
    assert neutralize_spreadsheet_formula("caudal") == "caudal"


def test_xlsm_warns_and_does_not_execute_macros(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ESP_DATA_ROOT", str(tmp_path))
    path = tmp_path / "libro.xlsm"
    _workbook(path, [("a",), (1,)])
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("xl/vbaProject.bin", b"not-executable")
    response = _post_files(
        client,
        [_file("libro.xlsm", path.read_bytes(), "application/vnd.ms-excel.sheet.macroEnabled.12")],
    )
    assert response.status_code == 200
    item = response.json()["files"][0]
    assert item["status"] == "validated"
    assert "macros_not_executed" in item["warnings"]
    assert item["structure"]["workbook"]["macros_executed"] is False
