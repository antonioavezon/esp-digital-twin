"""Auditoría de columnas y mapeo. No altera RAW, preprocess ni la hidráulica."""

import json
import os
from pathlib import Path

from app.research.manifest import sha256_file
from app.research.mapping import (
    MappingError,
    apply_decision,
    build_mapping,
    coverage_of,
    ensure_mapping,
    save_decision,
    suggest,
)
from app.research.variables import canonical_by_id, canonical_catalog

RAW_MAPPING = "3b933ca84911484f5d912a44b025f5589abaf5ebc2b0426bf80c083869762bda"
RAW_SURGING = "acdcc6c5fc3d8969280c8712c45657fbb863f163a60829584fece5abf75f28cd"
PREPROCESS_SHA = "f89e38603c220bc7d3f65eff69c04f2862e43cdfd983bd2ad0ae6dea36a891a7"
MANIFEST_SHA = "262f3d86b849e20df8080be841848fb2d2356692f9728b29a931759dc192e618"


def _header(position, raw_name, unit=None, normalized=None):
    return {
        "position": position,
        "raw_name": raw_name,
        "unit": unit,
        "normalized_name": normalized,
        "primitive_type": "number",
        "empty": False,
    }


def _preprocess(headers):
    return {
        "schema_version": "1.0",
        "dataset_id": "009",
        "source": {
            "title": "Fixture",
            "doi": "10.0000/dataset",
            "article_doi": "10.0000/article",
        },
        "files": [
            {
                "file_id": "F01",
                "original_filename": "sample.xlsx",
                "sha256": "abc123",
                "relative_path": "009/sample.xlsx",
                "structure": {
                    "workbook": {
                        "merged_cells": [],
                        "sheets": [
                            {
                                "name": "50psig",
                                "blocks": [
                                    {
                                        "block_id": "B01",
                                        "header_row": 1,
                                        "start_row": 1,
                                        "headers": headers,
                                    }
                                ],
                            }
                        ],
                    }
                },
            }
        ],
    }


def test_canonical_registry_is_independent_of_dataset_001():
    catalog = canonical_catalog()
    identifiers = {item["id"] for item in catalog}
    assert "intake_pressure" in identifiers
    assert "rotary_speed" in identifiers
    assert "hydraulic_power" in identifiers
    assert "shaft_power" in identifiers
    assert "electrical_power" in identifiers
    assert canonical_by_id("rotary_speed")["si_unit"] == "rad/s"
    assert canonical_by_id("gas_volume_fraction")["expected_range"] == "0–1"
    assert all(item["id"] != "001" for item in catalog)


def test_pressure_header_does_not_become_intake_pressure():
    decision = suggest("Pressure", None, {"min": 10, "max": 80})
    assert decision["quantity_family"] == "pressure"
    assert decision["canonical_id"] is None
    assert decision["status"] == "unmapped"


def test_rotary_speed_with_explicit_rpm_is_only_a_candidate():
    decision = suggest("Rotary Speed (rpm)", "rpm")
    assert decision["status"] == "candidate"
    assert decision["canonical_id"] == "rotary_speed"
    assert decision["confidence"] == "high"
    assert {item["type"] for item in decision["evidence"]} == {"explicit_header", "explicit_unit"}


def test_values_between_zero_and_one_do_not_become_gvf():
    decision = suggest("series", None, {"min": 0.0, "max": 1.0})
    assert decision["canonical_id"] is None
    assert decision["status"] == "unmapped"
    assert decision["quantity_family"] is None


def test_power_header_does_not_choose_a_power():
    decision = suggest("Power", None)
    assert decision["quantity_family"] == "power"
    assert decision["canonical_id"] is None
    assert decision["canonical_id"] != "hydraulic_power"


def test_dp2_3_is_not_pump_pressure_difference():
    decision = suggest("DP2-3", None)
    assert decision["canonical_id"] is None
    assert decision["status"] == "unmapped"


def test_initial_mapping_is_not_validated_and_keeps_lineage():
    document = build_mapping(
        _preprocess(
            [
                _header(1, "Rotary Speed (rpm)", "rpm", "rotary_speed"),
                _header(2, "Flow rate", None, "flow_rate"),
                _header(3, None),
            ]
        ),
        {"dataset_id": "009", "files": [{"original_filename": "sample.xlsx", "sha256": "abc123"}]},
    )
    assert document["schema_version"] == "1.0"
    assert all(item["status"] != "validated" for item in document["variables"])
    rotary = next(item for item in document["variables"] if item["source"]["raw_name"] == "Rotary Speed (rpm)")
    assert rotary["status"] == "candidate"
    assert rotary["source"]["occurrences"][0]["source_sha256"] == "abc123"
    assert document["lineage"]["preprocess_schema_version"] == "1.0"
    assert document["lineage"]["mapping_schema_version"] == "1.0"
    blank = next(item for item in document["variables"] if item["source"]["raw_name"] is None)
    assert blank["status"] == "not_applicable"


def test_mapping_can_be_saved_revised_and_rejected(tmp_path):
    metadata = tmp_path / "datasets" / "009" / "metadata"
    metadata.mkdir(parents=True)
    preprocess = _preprocess([_header(1, "Rotary Speed (rpm)", "rpm", "rotary_speed")])
    (metadata / "preprocess.json").write_text(json.dumps(preprocess), encoding="utf-8")
    (metadata / "manifest.json").write_text(
        json.dumps({"dataset_id": "009", "files": [{"original_filename": "sample.xlsx", "sha256": "abc123"}]}),
        encoding="utf-8",
    )
    created = ensure_mapping("009", tmp_path)
    untouched = (metadata / "preprocess.json").read_bytes()
    signature = created["variables"][0]["signature_id"]
    mapping_id = created["variables"][0]["mapping_id"]
    saved = save_decision(
        "009",
        {
            "signature_id": signature,
            "canonical_id": "rotary_speed",
            "status": "validated",
            "confidence": "high",
            "location": "pump",
            "evidence": [
                {"type": "explicit_header", "value": "Rotary Speed (rpm)"},
                {"type": "explicit_unit", "value": "rpm"},
            ],
            "notes": "Nombre y unidad explícitos.",
        },
        root=tmp_path,
    )
    assert saved["status"] == "validated"
    assert saved["revision"] == 2
    assert len(saved["history"]) == 2
    rejected = save_decision(
        "009",
        {
            "canonical_id": "rotary_speed",
            "status": "rejected",
            "confidence": "low",
            "location": "unknown",
            "evidence": [{"type": "manual_research_review", "value": "La columna no es una serie medida."}],
            "notes": "Se descarta como serie.",
        },
        mapping_id=mapping_id,
        root=tmp_path,
    )
    assert rejected["status"] == "rejected"
    assert rejected["revision"] == 3
    assert rejected["history"][1]["status"] == "validated"
    stored = json.loads((metadata / "mapping.json").read_text(encoding="utf-8"))
    assert stored["variables"][0]["status"] == "rejected"
    assert (metadata / "preprocess.json").read_bytes() == untouched


def test_invalid_canonical_status_and_confidence_are_rejected(tmp_path):
    document = build_mapping(_preprocess([_header(1, "Flow rate")]))
    for payload in (
        {"signature_id": document["variables"][0]["signature_id"], "canonical_id": "not_a_variable", "status": "candidate", "confidence": "low", "evidence": [{"type": "explicit_header", "value": "Flow rate"}]},
        {"signature_id": document["variables"][0]["signature_id"], "status": "trained", "confidence": "low", "evidence": [{"type": "explicit_header", "value": "Flow rate"}]},
        {"signature_id": document["variables"][0]["signature_id"], "status": "candidate", "confidence": "certain", "evidence": [{"type": "explicit_header", "value": "Flow rate"}]},
    ):
        try:
            apply_decision(document, payload)
        except MappingError as exc:
            assert exc.status == 422
        else:
            raise AssertionError(payload)


def test_coverage_reports_missing_expected_variables():
    document = build_mapping(_preprocess([_header(1, "Rotary Speed (rpm)", "rpm", "rotary_speed")]))
    report = coverage_of(document)
    assert report["candidate"] == 1
    assert report["validated"] == 0
    assert "rotary_speed" in report["expected_present"]
    assert "intake_pressure" in report["expected_missing"]
    assert "flowing_bottomhole_pressure" in report["expected_missing"]
    assert "dynamic_fluid_level" in report["expected_missing"]
    assert all(item["calculation_status"] == "not_executed" for item in document["derivable_relations"])
    assert all(item["inputs_available"] is False for item in document["derivable_relations"])


def test_dataset_001_mapping_does_not_touch_raw_or_preprocess():
    root = Path(os.environ.get("ESP_DATA_ROOT", "/app/data"))
    mapping = root / "datasets" / "001" / "metadata" / "mapping.json"
    preprocess = root / "datasets" / "001" / "metadata" / "preprocess.json"
    manifest = root / "datasets" / "001" / "metadata" / "manifest.json"
    assert mapping.is_file()
    document = json.loads(mapping.read_text(encoding="utf-8"))
    assert document["dataset_id"] == "001"
    assert document["semantic_status"] == "mapping_in_progress"
    by_name = {item["source"]["raw_name"]: item for item in document["variables"]}
    assert by_name["DP2-3"]["canonical"] is None
    assert by_name["DP2-3"]["status"] == "unmapped"
    assert by_name["Flow rate"]["canonical"] is None
    assert by_name["GVF0"]["canonical"] is None
    assert by_name["Rotary Speed (rpm)"]["status"] == "candidate"
    assert by_name["Rotary Speed (rpm)"]["source"]["raw_unit"] == "rpm"
    assert by_name["rotary speed"]["source"]["raw_unit"] is None
    assert by_name["rotary speed"]["status"] == "candidate"
    assert document["coverage"]["validated"] == 0
    assert "intake_pressure" in document["missing_expected_variables"]
    assert sha256_file(root / "001" / "Mapping Test Data_zero IPA.xlsx") == RAW_MAPPING
    assert sha256_file(root / "001" / "Surging Test Data_zero IPA.xlsx") == RAW_SURGING
    assert sha256_file(preprocess) == PREPROCESS_SHA
    assert sha256_file(manifest) == MANIFEST_SHA
    assert json.loads(preprocess.read_text(encoding="utf-8"))["semantic_mapping"]["status"] == "not_started"
