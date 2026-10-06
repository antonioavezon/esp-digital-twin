"""Contexto experimental y resumen derivado de 2-1. No altera RAW ni preprocess."""

import json
import os
from pathlib import Path

from app.research.manifest import sha256_file
from app.research.mapping import annotate_mapping, experimental_context, save_decision
from app.research.results import (
    build_stage_results,
    is_stale,
    refresh_stage_results,
    scientific_view,
    update_question,
)

RAW_MAPPING = "3b933ca84911484f5d912a44b025f5589abaf5ebc2b0426bf80c083869762bda"
RAW_SURGING = "acdcc6c5fc3d8969280c8712c45657fbb863f163a60829584fece5abf75f28cd"
PREPROCESS_SHA = "f89e38603c220bc7d3f65eff69c04f2862e43cdfd983bd2ad0ae6dea36a891a7"


def _stack_context(value):
    return experimental_context("Rotary Speed (rpm)", "rpm", ["Rotary Speed (rpm)", value])


def test_header_stack_1800_is_an_rpm_condition():
    context = _stack_context(1800)
    assert context == {"value": 1800, "unit": "rpm", "source": "header_stack"}


def test_header_stack_3500_is_an_rpm_condition():
    context = _stack_context(3500)
    assert context["value"] == 3500
    assert context["unit"] == "rpm"
    assert context["source"] == "header_stack"


def test_annotation_exposes_context_without_promoting_hints(tmp_path):
    document = {
        "variables": [
            {
                "status": "candidate",
                "confidence": "high",
                "canonical": {"id": "rotary_speed"},
                "quantity_family": "rotational_speed",
                "source": {
                    "raw_name": "Rotary Speed (rpm)",
                    "raw_unit": "rpm",
                    "group_labels": [],
                    "occurrences": [
                        {
                            "file": "surging.xlsx",
                            "sheet": "50psig",
                            "block_id": "B01",
                            "header_stack": ["Rotary Speed (rpm)", 1800],
                            "example": None,
                            "min": None,
                            "group_label": None,
                        }
                    ],
                },
            },
            {
                "status": "unmapped",
                "confidence": None,
                "canonical": None,
                "quantity_family": None,
                "source": {
                    "raw_name": "GVF0",
                    "raw_unit": None,
                    "group_labels": ["Qbep"],
                    "occurrences": [
                        {
                            "file": "surging.xlsx",
                            "sheet": "50psig",
                            "block_id": "B01",
                            "header_stack": ["Qbep", "GVF0"],
                            "example": 0.1,
                            "min": 0.0,
                            "group_label": "Qbep",
                        }
                    ],
                },
            },
            {
                "status": "unmapped",
                "confidence": None,
                "canonical": None,
                "quantity_family": None,
                "source": {
                    "raw_name": "DP2-3",
                    "raw_unit": None,
                    "group_labels": [],
                    "occurrences": [
                        {
                            "file": "surging.xlsx",
                            "sheet": "50psig",
                            "block_id": "B01",
                            "header_stack": ["DP2-3"],
                            "example": 4.2,
                            "min": 1.0,
                            "group_label": None,
                        }
                    ],
                },
            },
            {
                "status": "unmapped",
                "confidence": None,
                "canonical": None,
                "quantity_family": "flow",
                "source": {
                    "raw_name": "Flow rate",
                    "raw_unit": None,
                    "group_labels": [],
                    "occurrences": [
                        {
                            "file": "mapping.xlsx",
                            "sheet": "50psig",
                            "block_id": "B01",
                            "header_stack": ["Flow rate"],
                            "example": 10,
                            "min": 1,
                            "group_label": None,
                        }
                    ],
                },
            },
        ]
    }
    annotated = annotate_mapping(document)
    by_name = {item["source"]["raw_name"]: item for item in annotated["variables"]}
    speed = by_name["Rotary Speed (rpm)"]
    assert speed["semantic_role"] == "condition"
    assert speed["source"]["occurrences"][0]["experimental_context"]["value"] == 1800
    assert speed["status"] == "candidate"
    assert speed["canonical"]["id"] == "rotary_speed"
    gvf = by_name["GVF0"]
    assert gvf["canonical"] is None
    assert gvf["status"] == "unmapped"
    assert gvf["raw_hint"]["possible_target"] == "gas_volume_fraction"
    assert gvf["raw_hint"]["status"] == "needs_evidence"
    assert gvf["source"]["context_labels"] == ["1800 rpm"]
    assert by_name["DP2-3"]["canonical"] is None
    assert by_name["DP2-3"]["raw_hint"]["quantity_family_candidate"] == "pressure"
    flow = by_name["Flow rate"]
    assert flow["quantity_family"] == "flow"
    assert flow["canonical"] is None
    assert flow["status"] == "unmapped"
    coverage = {item["id"]: item for item in annotated["coverage"]["expected"]}
    assert coverage["gas_volume_fraction"]["raw_status"] == "possible"
    assert coverage["gas_volume_fraction"]["validated"] is False
    assert coverage["liquid_flow_rate"]["raw_evidence"] == ["Flow rate"]
    assert coverage["liquid_flow_rate"]["is_candidate"] is False
    assert coverage["pump_pressure_difference"]["raw_evidence"] == ["DP2-3"]
    assert coverage["pump_pressure_difference"]["validated"] is False
    assert coverage["intake_pressure"]["state"] == "not_found"


def _write_dataset(root: Path, sheet_name="50psig", speed=1800):
    metadata = root / "datasets" / "009" / "metadata"
    metadata.mkdir(parents=True)
    manifest = {
        "schema_version": "1.0",
        "dataset_id": "009",
        "source": {"title": "Fixture", "doi": "10.0/d", "article_doi": "10.0/a"},
        "files": [
            {
                "original_filename": "sample.xlsx",
                "relative_path": "009/missing.xlsx",
                "sha256": "abc",
            }
        ],
    }
    preprocess = {
        "schema_version": "1.0",
        "dataset_id": "009",
        "generated_at": "2026-10-06T00:00:00+00:00",
        "files": [
            {
                "original_filename": "sample.xlsx",
                "sha256": "abc",
                "structure": {
                    "workbook": {
                        "sheet_names": [sheet_name],
                        "sheets": [{"name": sheet_name, "blocks": [{"block_id": "B01"}, {"block_id": "B02"}]}],
                    }
                },
            }
        ],
    }
    mapping = {
        "schema_version": "1.0",
        "dataset_id": "009",
        "updated_at": "2026-10-06T00:00:00+00:00",
        "lineage": {"source_sha256": {"sample.xlsx": "abc"}},
        "evidence_sources": [
            {"id": "E001", "kind": "dataset", "doi": "10.0/d", "used": True},
            {"id": "E002", "kind": "article", "doi": "10.0/a", "used": False},
        ],
        "variables": [
            {
                "mapping_id": "M001",
                "signature_id": "S-rotary",
                "status": "candidate",
                "confidence": "high",
                "canonical": {"id": "rotary_speed", "symbol": "N", "quantity": "rotational_speed", "si_unit": "rad/s"},
                "quantity_family": "rotational_speed",
                "evidence": [{"type": "explicit_header", "value": "Rotary Speed (rpm)"}],
                "revision": 1,
                "history": [{"revision": 1, "status": "candidate"}],
                "source": {
                    "raw_name": "Rotary Speed (rpm)",
                    "raw_unit": "rpm",
                    "group_labels": [],
                    "occurrences": [
                        {
                            "file": "sample.xlsx",
                            "sheet": sheet_name,
                            "block_id": "B01",
                            "header_stack": ["Rotary Speed (rpm)", speed],
                            "example": None,
                            "min": None,
                        }
                    ],
                },
            }
        ],
        "derivable_relations": [
            {
                "id": "gvf_from_phase_rates",
                "output": "gas_volume_fraction",
                "equation": "GVF = Q_G / (Q_G + Q_L)",
                "requires": ["gas_flow_rate", "liquid_flow_rate"],
                "inputs_available": False,
                "calculation_status": "not_executed",
            }
        ],
        "coverage": {},
    }
    (metadata / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (metadata / "preprocess.json").write_text(json.dumps(preprocess), encoding="utf-8")
    (metadata / "mapping.json").write_text(json.dumps(mapping), encoding="utf-8")
    return metadata


def test_results_round_trip_preserves_questions_and_detects_stale(tmp_path):
    metadata = _write_dataset(tmp_path)
    first = refresh_stage_results("009", tmp_path, now="2026-10-06T01:00:00+00:00")
    assert first["structural_summary"]["sheets"] == 1
    assert first["structural_summary"]["blocks"] == 2
    assert first["experimental_conditions"][0]["type"] == "sheet_pressure"
    assert first["experimental_conditions"][0]["canonical_variable"] is None
    assert first["experimental_conditions"][0]["unit"] == "psig"
    assert first["experimental_conditions"][1]["value"] == 1800
    assert first["status"] == "current"
    assert all(item["calculation_status"] == "not_executed" for item in first["derivable_relations"])
    assert all(item["model_trained"] is False for item in first["modeling_feasibility"])
    assert {item["id"] for item in first["open_questions"]} >= {"Q001", "Q002", "Q003", "Q004", "Q005", "Q006", "Q007"}
    update_question("009", "Q001", "answered", root=tmp_path, evidence_ids=["E003"])
    rebuilt = refresh_stage_results("009", tmp_path, now="2026-10-06T02:00:00+00:00")
    question = next(item for item in rebuilt["open_questions"] if item["id"] == "Q001")
    assert question["status"] == "answered"
    assert question["text"].startswith("¿Qué representa")
    assert len(rebuilt["open_questions"]) == 7
    path = metadata / "stage-2-1-results.json"
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["source_lineage"]["mapping_updated_at"] = "stale"
    path.write_text(json.dumps(stored), encoding="utf-8")
    assert is_stale("009", tmp_path) is True
    fresh = refresh_stage_results("009", tmp_path, now="2026-10-06T03:00:00+00:00")
    assert fresh["results_stale"] is False
    assert is_stale("009", tmp_path) is False
    path.unlink()
    again = build_stage_results("009", tmp_path, now="2026-10-06T04:00:00+00:00", previous=None)
    assert again["revision"] == 1
    assert again["experimental_conditions"][1]["value"] == 1800


def test_saving_a_mapping_refreshes_results_and_keeps_sources(tmp_path):
    metadata = _write_dataset(tmp_path)
    before_preprocess = (metadata / "preprocess.json").read_bytes()
    refresh_stage_results("009", tmp_path, now="2026-10-06T01:00:00+00:00")
    save_decision(
        "009",
        {
            "signature_id": "S-rotary",
            "canonical_id": "rotary_speed",
            "status": "reviewed",
            "confidence": "high",
            "location": "unknown",
            "evidence": [{"type": "explicit_header", "value": "Rotary Speed (rpm)"}],
            "notes": "Revisión de prueba.",
        },
        root=tmp_path,
    )
    stored = json.loads((metadata / "stage-2-1-results.json").read_text(encoding="utf-8"))
    mapping = json.loads((metadata / "mapping.json").read_text(encoding="utf-8"))
    assert stored["mapping_summary"]["reviewed"] == 1
    assert stored["source_lineage"]["mapping_updated_at"] == mapping["updated_at"]
    assert stored["coverage"]["expected"] == stored["canonical_coverage"]
    assert (metadata / "preprocess.json").read_bytes() == before_preprocess
    left = scientific_view(stored)
    right = scientific_view(build_stage_results("009", tmp_path, now="2026-10-06T09:00:00+00:00", previous=stored))
    left.pop("revision")
    right.pop("revision")
    assert left["canonical_coverage"] == right["canonical_coverage"]
    assert left["open_questions"] == right["open_questions"]
    assert left["modeling_feasibility"] == right["modeling_feasibility"]


def test_dataset_001_results_come_from_the_books_and_do_not_touch_them():
    root = Path(os.environ.get("ESP_DATA_ROOT", "/app/data"))
    raw_mapping = root / "001" / "Mapping Test Data_zero IPA.xlsx"
    raw_surging = root / "001" / "Surging Test Data_zero IPA.xlsx"
    preprocess = root / "datasets" / "001" / "metadata" / "preprocess.json"
    before = (raw_mapping.read_bytes(), raw_surging.read_bytes(), preprocess.read_bytes())
    document = build_stage_results("001", root, now="2026-10-06T19:20:00+00:00", previous=None)
    assert (raw_mapping.read_bytes(), raw_surging.read_bytes(), preprocess.read_bytes()) == before
    assert sha256_file(raw_mapping) == RAW_MAPPING
    assert sha256_file(raw_surging) == RAW_SURGING
    assert sha256_file(preprocess) == PREPROCESS_SHA
    summary = document["structural_summary"]
    assert summary == {"files": 2, "sheets": 6, "blocks": 12, "signatures": 6, "occurrences": 144}
    assert document["mapping_summary"]["candidate"] == 2
    assert document["mapping_summary"]["unmapped"] == 3
    assert document["mapping_summary"]["validated"] == 0
    assert document["mapping_summary"]["not_applicable"] == 1
    speeds = [item["value"] for item in document["experimental_conditions"] if item["type"] == "header_condition"]
    pressures = [item["value"] for item in document["experimental_conditions"] if item["type"] == "sheet_pressure"]
    assert speeds == [1800, 3500]
    assert pressures == [50, 100, 150]
    assert all(item["canonical_variable"] is None for item in document["experimental_conditions"])
    labels = [item["label"] for item in document["experimental_groups"]]
    assert "0.75Qbep" in labels and "Qbep" in labels and "1.25Qbep" in labels
    names = {item["raw_name"] for item in document["raw_evidence"]}
    assert {"rotary speed", "Rotary Speed (rpm)", "Flow rate", "DP2-3", "GVF0"} <= names
    by_name = {item["raw_name"]: item for item in document["raw_evidence"]}
    assert by_name["GVF0"]["canonical_id"] is None
    assert by_name["DP2-3"]["canonical_id"] is None
    assert by_name["Flow rate"]["canonical_id"] is None
    assert by_name["Rotary Speed (rpm)"]["status"] == "candidate"
    assert by_name["Rotary Speed (rpm)"]["confidence"] == "high"
    gaps = {item["id"]: item for item in document["data_gaps"]}
    assert gaps["gas_volume_fraction"]["raw_evidence_found"] is True
    assert gaps["gas_volume_fraction"]["validated"] is False
    assert gaps["intake_pressure"]["raw_evidence_found"] is False
    assert gaps["dynamic_fluid_level"]["missing"] is True
    assert all(item["derivable"] is False for item in document["data_gaps"])
    feasibility = {item["id"]: item["status"] for item in document["modeling_feasibility"]}
    assert feasibility["surging_regime"] == "potentially_feasible"
    assert feasibility["hydraulic_degradation_gassy"] == "needs_mapping"
    assert feasibility["flowing_bottomhole_pressure"] == "needs_additional_dataset"
    assert feasibility["dynamic_level"] == "needs_additional_dataset"
    assert document["evidence_sources"][1]["used"] is False
    assert document["versions"]["physics_model"] == "hydraulics-v0.1"
    assert document["versions"]["model_trained"] is False
    stored = json.loads((root / "datasets" / "001" / "metadata" / "stage-2-1-results.json").read_text())
    assert stored["structural_summary"] == document["structural_summary"]
    assert stored["canonical_coverage"] == document["canonical_coverage"]
    assert stored["coverage"]["expected"] == stored["canonical_coverage"]
