"""Resumen derivado de la etapa 2-1.

Se reconstruye desde manifest, preprocess y mapping. No sustituye a ninguno
de esos archivos y no modifica el RAW.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.physics.constants import PHYSICS_MODE, PHYSICS_MODEL
from app.research.manifest import sha256_file
from app.research.mapping import annotate_mapping, mapping_path
from app.research.variables import canonical_by_id, expected_variable_ids

RESULTS_SCHEMA = "1.0"
QUESTION_STATUSES = ("open", "answered", "partially_answered", "not_applicable")
_SHEET_PRESSURE = re.compile(r"^(\d+(?:\.\d+)?)psig$", re.IGNORECASE)
_QBEP = re.compile(r"^(?:(\d+(?:\.\d+)?)Qbep|Qbep)$", re.IGNORECASE)

OPEN_QUESTIONS = (
    {
        "id": "Q001",
        "text": "¿Qué representa físicamente DP2-3?",
        "related_raw": ["DP2-3"],
        "requires_external_evidence": True,
    },
    {
        "id": "Q002",
        "text": "¿Qué significa exactamente GVF0 y su subíndice 0?",
        "related_raw": ["GVF0"],
        "requires_external_evidence": True,
    },
    {
        "id": "Q003",
        "text": "¿Cuál es la unidad de Flow rate?",
        "related_raw": ["Flow rate"],
        "requires_external_evidence": True,
    },
    {
        "id": "Q004",
        "text": "¿Flow rate corresponde a líquido, gas o mezcla?",
        "related_raw": ["Flow rate"],
        "requires_external_evidence": True,
    },
    {
        "id": "Q005",
        "text": "¿Qué presión representan las hojas 50/100/150 psig?",
        "related_raw": [],
        "requires_external_evidence": True,
    },
    {
        "id": "Q006",
        "text": "¿Qué representan exactamente los dos bloques, además de las velocidades observadas?",
        "related_raw": [],
        "requires_external_evidence": True,
    },
    {
        "id": "Q007",
        "text": "¿Cuál es el valor de Qbep del montaje para cada velocidad, si corresponde?",
        "related_raw": [],
        "requires_external_evidence": True,
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def results_path(dataset_id: str, root: Path | None = None) -> Path:
    return mapping_path(dataset_id, root).with_name("stage-2-1-results.json")


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _metadata(dataset_id: str, root: Path | None) -> Path:
    return mapping_path(dataset_id, root).parent


def _number(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _sheet_conditions(preprocess: dict) -> list[dict]:
    found = []
    seen = set()
    for item in preprocess.get("files") or []:
        workbook = ((item.get("structure") or {}).get("workbook") or {})
        for name in workbook.get("sheet_names") or []:
            match = _SHEET_PRESSURE.match(name or "")
            if not match or name in seen:
                continue
            seen.add(name)
            found.append(
                {
                    "type": "sheet_pressure",
                    "raw_value": name,
                    "value": _number(float(match.group(1))),
                    "unit": "psig",
                    "canonical_variable": None,
                    "status": "observed",
                }
            )
    return sorted(found, key=lambda item: item["value"])


def _header_conditions(mapping: dict) -> list[dict]:
    found = []
    seen = set()
    for item in mapping.get("variables") or []:
        raw_name = (item.get("source") or {}).get("raw_name")
        for occurrence in (item.get("source") or {}).get("occurrences") or []:
            context = occurrence.get("experimental_context")
            if not context:
                continue
            key = (raw_name, context.get("value"), context.get("unit"))
            if key in seen:
                continue
            seen.add(key)
            found.append(
                {
                    "type": "header_condition",
                    "raw_name": raw_name,
                    "raw_value": context.get("value"),
                    "value": _number(context.get("value")),
                    "unit": context.get("unit"),
                    "source": context.get("source"),
                    "canonical_variable": None,
                    "status": "observed",
                }
            )
    return sorted(found, key=lambda item: (str(item.get("raw_name")), item.get("value") is None, str(item.get("value"))))


def _group_statement(label: str) -> dict:
    match = _QBEP.match(label or "")
    if match:
        factor = match.group(1)
        if factor:
            statement = (
                f"Si Qbep es el caudal del punto de mejor eficiencia, {label} indica "
                f"el {float(factor) * 100:g} % de ese caudal. El valor de Qbep no está en los libros "
                "y esta lectura no está validada."
            )
        else:
            statement = (
                "Qbep nombra una condición de operación referida al punto de mejor eficiencia. "
                "El caudal correspondiente no está en los libros y esta lectura no está validada."
            )
        return {"label": label, "kind": "operating_group", "interpretation_status": "hypothesis", "statement": statement}
    if (label or "").startswith("Qgd="):
        statement = "Rótulo de grupo observado. No se interpreta como una serie de caudal de gas."
    elif label == "Single Phase":
        statement = "Rótulo de grupo observado. No se asigna una fase canónica."
    else:
        statement = "Rótulo de grupo observado. No se le asigna una variable canónica."
    return {"label": label, "kind": "group_label", "interpretation_status": "observed", "statement": statement}


def _groups(mapping: dict) -> list[dict]:
    labels = []
    for item in mapping.get("variables") or []:
        for label in (item.get("source") or {}).get("group_labels") or []:
            if label not in labels:
                labels.append(label)
    return [_group_statement(label) for label in sorted(labels)]


def _structure(preprocess: dict, mapping: dict) -> dict:
    files = preprocess.get("files") or []
    sheets = []
    blocks = 0
    for item in files:
        workbook = ((item.get("structure") or {}).get("workbook") or {})
        for sheet in workbook.get("sheets") or []:
            sheets.append(sheet.get("name"))
            blocks += len(sheet.get("blocks") or [])
    coverage = mapping.get("coverage") or {}
    return {
        "files": len(files),
        "sheets": len(sheets),
        "blocks": blocks,
        "signatures": coverage.get("signatures", 0),
        "occurrences": coverage.get("occurrences", 0),
    }


def _questions(previous: dict | None) -> list[dict]:
    saved = {item["id"]: item for item in (previous or {}).get("open_questions") or []}
    rows = []
    for item in OPEN_QUESTIONS:
        prior = saved.get(item["id"]) or {}
        status = prior.get("status") if prior.get("status") in QUESTION_STATUSES else "open"
        rows.append(
            {
                "id": item["id"],
                "text": item["text"],
                "related_raw": list(item["related_raw"]),
                "status": status,
                "requires_external_evidence": item["requires_external_evidence"],
                "evidence_ids": list(prior.get("evidence_ids") or []),
            }
        )
    return rows


def _gaps(mapping: dict) -> list[dict]:
    coverage = {item["id"]: item for item in (mapping.get("coverage") or {}).get("expected") or []}
    relations = {
        item["output"]: item
        for item in mapping.get("derivable_relations") or []
    }
    rows = []
    for variable_id in expected_variable_ids():
        variable = canonical_by_id(variable_id)
        row = coverage.get(variable_id) or {}
        relation = relations.get(variable_id)
        candidate = bool(row.get("is_candidate"))
        validated = bool(row.get("validated"))
        raw_names = list(row.get("raw_evidence") or [])
        inputs_ready = bool(relation and relation.get("inputs_available"))
        if validated:
            note = "Hay una asignación canónica validada."
        elif candidate:
            note = "Hay un candidato canónico. Todavía no está validado."
        elif raw_names:
            note = "Hay evidencia RAW posible. No alcanza para un mapping canónico."
        elif relation:
            note = "Existe una relación registrada y no se ha ejecutado."
        else:
            note = "No aparece en los encabezados ni como candidato."
        rows.append(
            {
                "id": variable_id,
                "symbol": variable["symbol"],
                "raw_evidence_found": bool(raw_names),
                "raw_names": raw_names,
                "canonical_candidate": candidate,
                "validated": validated,
                "derivable": inputs_ready,
                "relation_registered": relation is not None,
                "missing": not candidate and not validated,
                "notes": note,
            }
        )
    return rows


def _names(gaps: list[dict], *wanted: str) -> list[str]:
    return [item for item in wanted if any(gap["id"] == item and (gap["raw_evidence_found"] or gap["canonical_candidate"] or gap["validated"]) for gap in gaps)]


def _missing(gaps: list[dict], *wanted: str) -> list[str]:
    present = set(_names(gaps, *wanted))
    return [item for item in wanted if item not in present]


def _feasibility(gaps: list[dict], filenames: list[str]) -> list[dict]:
    by_id = {item["id"]: item for item in gaps}
    has_surging = any("surg" in name.lower() for name in filenames)

    def seen(variable_id: str) -> bool:
        gap = by_id[variable_id]
        return bool(gap["raw_evidence_found"] or gap["canonical_candidate"] or gap["validated"])

    problems = []

    gas = seen("gas_volume_fraction") or seen("gas_flow_rate")
    hydraulic = seen("liquid_flow_rate") or seen("pump_pressure_difference") or seen("pump_head")
    if gas and hydraulic:
        degradation = "needs_mapping"
        degradation_note = "Hay pistas de gas y de una respuesta hidráulica, sin un mapping validado. No hay un modelo."
    else:
        degradation = "needs_additional_dataset"
        degradation_note = "Falta evidencia de gas o de la respuesta hidráulica."
    problems.append(
        {
            "id": "hydraulic_degradation_gassy",
            "status": degradation,
            "required_variables": ["gas_volume_fraction", "liquid_flow_rate", "pump_pressure_difference"],
            "available_evidence": _names(gaps, "gas_volume_fraction", "gas_flow_rate", "liquid_flow_rate", "pump_pressure_difference", "pump_head", "rotary_speed"),
            "missing_variables": _missing(gaps, "gas_volume_fraction", "liquid_flow_rate", "pump_pressure_difference"),
            "notes": degradation_note,
            "model_trained": False,
        }
    )

    if seen("pump_pressure_difference") or seen("pump_head"):
        pressure_status = "needs_mapping"
        pressure_note = "Hay una pista de diferencia de presión o de head, sin puntos ni unidad validados."
    else:
        pressure_status = "needs_additional_dataset"
        pressure_note = "No hay evidencia RAW de head ni de una diferencia de presión identificada."
    problems.append(
        {
            "id": "pressure_head_response",
            "status": pressure_status,
            "required_variables": ["pump_pressure_difference", "pump_head", "liquid_flow_rate"],
            "available_evidence": _names(gaps, "pump_pressure_difference", "pump_head", "liquid_flow_rate", "rotary_speed"),
            "missing_variables": _missing(gaps, "pump_pressure_difference", "pump_head", "liquid_flow_rate"),
            "notes": pressure_note,
            "model_trained": False,
        }
    )

    if has_surging and seen("rotary_speed") and (seen("gas_volume_fraction") or seen("pump_pressure_difference")):
        surging_status = "potentially_feasible"
        surging_note = (
            "El libro de surging, las velocidades de encabezado y los grupos de operación están observados. "
            "GVF0 y DP2-3 siguen sin mapping canónico. No significa que exista un modelo."
        )
    else:
        surging_status = "needs_mapping"
        surging_note = "La caracterización de surging todavía no tiene las condiciones y las series identificadas."
    problems.append(
        {
            "id": "surging_regime",
            "status": surging_status,
            "required_variables": ["rotary_speed", "gas_volume_fraction", "pump_pressure_difference"],
            "available_evidence": _names(gaps, "rotary_speed", "gas_volume_fraction", "pump_pressure_difference"),
            "missing_variables": _missing(gaps, "rotary_speed", "gas_volume_fraction", "pump_pressure_difference"),
            "notes": surging_note,
            "model_trained": False,
        }
    )

    for problem_id, variable_id, note in (
        (
            "sensorless_intake_pressure",
            "intake_pressure",
            "No hay una columna que pueda sostener la presión de admisión.",
        ),
        (
            "flowing_bottomhole_pressure",
            "flowing_bottomhole_pressure",
            "No hay una columna que pueda sostener la presión de fondo fluyente.",
        ),
        (
            "dynamic_level",
            "dynamic_fluid_level",
            "No hay una columna que pueda sostener el nivel dinámico.",
        ),
    ):
        status = "needs_mapping" if seen(variable_id) else "needs_additional_dataset"
        problems.append(
            {
                "id": problem_id,
                "status": status,
                "required_variables": [variable_id],
                "available_evidence": _names(gaps, variable_id),
                "missing_variables": [] if seen(variable_id) else [variable_id],
                "notes": note if status == "needs_additional_dataset" else "Hay una pista y falta validarla.",
                "model_trained": False,
            }
        )

    problems.append(
        {
            "id": "anomaly_detection",
            "status": "needs_additional_dataset",
            "required_variables": ["intake_pressure", "liquid_flow_rate"],
            "available_evidence": [],
            "missing_variables": ["intake_pressure", "liquid_flow_rate"],
            "notes": "2-1 no clasifica anomalías ni entrena un detector. Haría falta un criterio de anomalía que este dataset no trae.",
            "model_trained": False,
        }
    )
    return problems


def _findings(structure: dict, conditions: list[dict], groups: list[dict], mapping: dict) -> list[dict]:
    headers = sorted(
        name
        for name in ((item.get("source") or {}).get("raw_name") for item in mapping.get("variables") or [])
        if name
    )
    speeds = [item for item in conditions if item["type"] == "header_condition"]
    pressures = [item for item in conditions if item["type"] == "sheet_pressure"]
    if pressures:
        pressure_text = (
            "Las hojas nombran presiones nominales: "
            + ", ".join(f"{item['value']} {item['unit']}" for item in pressures)
            + ". El punto físico de esa presión no está identificado."
        )
    else:
        pressure_text = "No se observaron hojas cuyo nombre sea una presión en psig."
    if speeds:
        speed_text = (
            "Las condiciones de velocidad leídas en encabezados son: "
            + ", ".join(f"{item['value']} {item['unit']}" for item in speeds)
            + "."
        )
    else:
        speed_text = "No se observaron condiciones numéricas dentro de los encabezados."
    if groups:
        group_text = "Los rótulos de grupo observados son: " + ", ".join(item["label"] for item in groups) + "."
    else:
        group_text = "No se observaron rótulos de grupo."
    findings = [
        {
            "id": "F001",
            "statement": f"El dataset contiene {structure['files']} archivos experimentales.",
            "status": "observed",
            "evidence_ids": ["E001"],
        },
        {
            "id": "F002",
            "statement": pressure_text,
            "status": "observed",
            "evidence_ids": ["E001"],
        },
        {
            "id": "F003",
            "statement": f"La estructura observada tiene {structure['sheets']} hojas y {structure['blocks']} bloques.",
            "status": "observed",
            "evidence_ids": ["E001"],
        },
        {
            "id": "F004",
            "statement": speed_text,
            "status": "observed",
            "evidence_ids": ["E001"],
        },
        {
            "id": "F005",
            "statement": group_text,
            "status": "observed",
            "evidence_ids": ["E001"],
        },
        {
            "id": "F006",
            "statement": "Los encabezados RAW con nombre son: " + ", ".join(headers) + ".",
            "status": "observed",
            "evidence_ids": ["E001"],
        },
    ]
    repeated = [
        (item.get("source") or {}).get("raw_name")
        for item in mapping.get("variables") or []
        if len((item.get("source") or {}).get("occurrences") or []) > 1 and (item.get("source") or {}).get("raw_name")
    ]
    if repeated:
        findings.append(
            {
                "id": "F007",
                "statement": "Hay encabezados repetidos entre hojas o bloques: " + ", ".join(sorted(set(repeated))) + ".",
                "status": "observed",
                "evidence_ids": ["E001"],
            }
        )
    for group in groups:
        if group["interpretation_status"] == "hypothesis":
            findings.append(
                {
                    "id": f"F-{group['label']}",
                    "statement": group["statement"],
                    "status": "hypothesis",
                    "evidence_ids": ["E001"],
                }
            )
    return sorted(findings, key=lambda item: item["id"])


def _flags(mapping: dict, structure: dict) -> list[dict]:
    flags = []
    variables = mapping.get("variables") or []
    if any(len((item.get("source") or {}).get("occurrences") or []) > 1 for item in variables):
        flags.append({"id": "repeated_headers", "level": "notice", "status": "observed"})
    if structure["blocks"] > structure["sheets"]:
        flags.append({"id": "multi_block_structure", "level": "notice", "status": "observed"})
    if any((item.get("source") or {}).get("raw_name") and not (item.get("source") or {}).get("raw_unit") for item in variables):
        flags.append({"id": "missing_units", "level": "notice", "status": "observed"})
    if any(item.get("raw_hint") for item in variables):
        flags.append({"id": "ambiguous_semantics", "level": "notice", "status": "observed"})
    if any(
        occurrence.get("experimental_context")
        for item in variables
        for occurrence in (item.get("source") or {}).get("occurrences") or []
    ):
        flags.append({"id": "context_in_headers", "level": "notice", "status": "observed"})
    return flags


def _lineage(root: Path, manifest: dict, preprocess: dict, mapping: dict) -> tuple[dict, str]:
    files = []
    mismatch = False
    for item in sorted(manifest.get("files") or [], key=lambda entry: entry.get("original_filename") or ""):
        name = item.get("original_filename")
        declared = item.get("sha256")
        relative = item.get("relative_path")
        actual = None
        if relative:
            path = root / relative
            if path.is_file():
                actual = sha256_file(path)
                if actual != declared:
                    mismatch = True
        preprocess_sha = next(
            (
                entry.get("sha256")
                for entry in preprocess.get("files") or []
                if entry.get("original_filename") == name
            ),
            None,
        )
        mapping_sha = (mapping.get("lineage") or {}).get("source_sha256", {}).get(name)
        if preprocess_sha and preprocess_sha != declared:
            mismatch = True
        if mapping_sha and mapping_sha != declared:
            mismatch = True
        files.append(
            {
                "filename": name,
                "sha256": declared,
                "preprocess_sha256": preprocess_sha,
                "mapping_sha256": mapping_sha,
                "file_sha256": actual,
            }
        )
    revisions = [int(item.get("revision") or 0) for item in mapping.get("variables") or []]
    lineage = {
        "manifest_schema_version": manifest.get("schema_version"),
        "preprocess_schema_version": preprocess.get("schema_version"),
        "preprocess_generated_at": preprocess.get("generated_at"),
        "mapping_schema_version": mapping.get("schema_version"),
        "mapping_updated_at": mapping.get("updated_at"),
        "last_mapping_revision": max(revisions) if revisions else 0,
        "files": files,
    }
    return lineage, "lineage_mismatch" if mismatch else "current"


def _evidence_sources(mapping: dict) -> list[dict]:
    sources = []
    for item in mapping.get("evidence_sources") or []:
        row = {
            "id": item.get("id"),
            "kind": item.get("kind"),
            "title": item.get("title"),
            "doi": item.get("doi"),
            "used": item.get("used", item.get("id") == "E001"),
        }
        sources.append(row)
    return sources


def build_stage_results(
    dataset_id: str,
    root: Path | None = None,
    *,
    now: str | None = None,
    previous: dict | None = None,
) -> dict:
    metadata = _metadata(dataset_id, root)
    manifest = _read_json(metadata / "manifest.json")
    preprocess = _read_json(metadata / "preprocess.json")
    stored_mapping = _read_json(mapping_path(dataset_id, root))
    if manifest is None or preprocess is None or stored_mapping is None:
        raise FileNotFoundError(dataset_id)
    mapping = annotate_mapping(copy.deepcopy(stored_mapping))
    if root is None:
        from app.research.datasets import data_root

        base = data_root()
    else:
        base = root
    lineage, lineage_status = _lineage(base, manifest, preprocess, stored_mapping)
    conditions = _sheet_conditions(preprocess) + _header_conditions(mapping)
    groups = _groups(mapping)
    structure = _structure(preprocess, mapping)
    questions = _questions(previous if previous is not None else _read_json(results_path(dataset_id, root)))
    gaps = _gaps(mapping)
    filenames = [item.get("filename") for item in lineage["files"]]
    findings = _findings(structure, conditions, groups, mapping)
    coverage = mapping.get("coverage") or {}
    counts = coverage.get("by_status") or {}
    revision = int((previous or {}).get("revision") or 0) + 1 if previous else _next_revision(dataset_id, root)
    return {
        "schema_version": RESULTS_SCHEMA,
        "stage": "2-1",
        "dataset_id": dataset_id,
        "generated_at": now or _now(),
        "revision": revision,
        "status": lineage_status,
        "results_stale": False,
        "versions": {
            "project_stage": "2-1",
            "mapping_schema_version": mapping.get("schema_version"),
            "physics_model": PHYSICS_MODEL,
            "physics_mode": PHYSICS_MODE,
            "model_trained": False,
            "derived_calculations": "not_executed",
        },
        "source_lineage": lineage,
        "history_reference": {"location": "mapping.json", "field": "variables[].history"},
        "structural_summary": structure,
        "mapping_summary": {
            "validated": counts.get("validated", 0),
            "reviewed": counts.get("reviewed", 0),
            "candidate": counts.get("candidate", 0),
            "unmapped": counts.get("unmapped", 0),
            "rejected": counts.get("rejected", 0),
            "not_applicable": counts.get("not_applicable", 0),
        },
        "raw_evidence": [
            {
                "signature_id": item.get("signature_id"),
                "raw_name": (item.get("source") or {}).get("raw_name"),
                "raw_unit": (item.get("source") or {}).get("raw_unit"),
                "semantic_role": item.get("semantic_role"),
                "quantity_family": item.get("quantity_family"),
                "status": item.get("status"),
                "confidence": item.get("confidence"),
                "canonical_id": (item.get("canonical") or {}).get("id") if item.get("canonical") else None,
                "context_labels": (item.get("source") or {}).get("context_labels") or [],
                "group_labels": (item.get("source") or {}).get("group_labels") or [],
                "raw_hint": item.get("raw_hint"),
                "evidence": item.get("evidence") or [],
            }
            for item in mapping.get("variables") or []
        ],
        "canonical_coverage": coverage.get("expected") or [],
        "coverage": {
            "signatures": coverage.get("signatures"),
            "occurrences": coverage.get("occurrences"),
            "validated": coverage.get("validated"),
            "candidate": coverage.get("candidate"),
            "unmapped": coverage.get("unmapped"),
            "expected": coverage.get("expected") or [],
        },
        "experimental_conditions": conditions,
        "experimental_groups": groups,
        "open_questions": questions,
        "derivable_relations": mapping.get("derivable_relations") or [],
        "modeling_feasibility": _feasibility(gaps, filenames),
        "data_gaps": gaps,
        "findings": findings,
        "quality_flags": _flags(mapping, structure),
        "evidence_sources": _evidence_sources(mapping),
        "limitations": [
            "El artículo E002 está citado y no fue usado: su texto no está en el repositorio.",
            "No se convierten unidades ni se ejecutan relaciones derivadas.",
            "Una pista RAW no es un mapping canónico.",
            "No hay Machine Learning ni Physics-AI.",
        ],
        "next_actions": [
            question["text"]
            for question in questions
            if question["status"] == "open"
        ],
    }


def _next_revision(dataset_id: str, root: Path | None) -> int:
    previous = _read_json(results_path(dataset_id, root))
    if not previous:
        return 1
    return int(previous.get("revision") or 0) + 1


def _fingerprint(document: dict) -> dict:
    lineage = document.get("source_lineage") or {}
    return {
        "mapping_updated_at": lineage.get("mapping_updated_at"),
        "preprocess_generated_at": lineage.get("preprocess_generated_at"),
        "last_mapping_revision": lineage.get("last_mapping_revision"),
        "files": [(item.get("filename"), item.get("sha256")) for item in lineage.get("files") or []],
    }


def is_stale(dataset_id: str, root: Path | None = None) -> bool:
    path = results_path(dataset_id, root)
    stored = _read_json(path)
    if stored is None:
        return True
    metadata = _metadata(dataset_id, root)
    manifest = _read_json(metadata / "manifest.json") or {}
    preprocess = _read_json(metadata / "preprocess.json") or {}
    mapping = _read_json(mapping_path(dataset_id, root)) or {}
    revisions = [int(item.get("revision") or 0) for item in mapping.get("variables") or []]
    current = {
        "mapping_updated_at": mapping.get("updated_at"),
        "preprocess_generated_at": preprocess.get("generated_at"),
        "last_mapping_revision": max(revisions) if revisions else 0,
        "files": sorted(
            (item.get("original_filename"), item.get("sha256"))
            for item in manifest.get("files") or []
        ),
    }
    saved = _fingerprint(stored)
    saved["files"] = sorted(tuple(item) for item in saved.get("files") or [])
    return saved != current


def refresh_stage_results(dataset_id: str, root: Path | None = None, *, now: str | None = None) -> dict | None:
    if not mapping_path(dataset_id, root).is_file():
        return None
    if not (_metadata(dataset_id, root) / "manifest.json").is_file():
        return None
    if not (_metadata(dataset_id, root) / "preprocess.json").is_file():
        return None
    previous = _read_json(results_path(dataset_id, root))
    document = build_stage_results(dataset_id, root, now=now, previous=previous)
    path = results_path(dataset_id, root)
    from app.research.mapping import _write

    _write(path, document)
    return document


def load_stage_results(dataset_id: str, root: Path | None = None) -> dict:
    if is_stale(dataset_id, root):
        document = refresh_stage_results(dataset_id, root)
        if document is None:
            raise FileNotFoundError(dataset_id)
        return document
    stored = _read_json(results_path(dataset_id, root))
    if stored is None:
        raise FileNotFoundError(dataset_id)
    return stored


def update_question(
    dataset_id: str,
    question_id: str,
    status: str,
    root: Path | None = None,
    evidence_ids: list[str] | None = None,
) -> dict:
    if status not in QUESTION_STATUSES:
        raise ValueError(status)
    document = load_stage_results(dataset_id, root)
    found = next((item for item in document.get("open_questions") or [] if item["id"] == question_id), None)
    if found is None:
        raise KeyError(question_id)
    found["status"] = status
    if evidence_ids is not None:
        found["evidence_ids"] = list(evidence_ids)
    document["next_actions"] = [
        item["text"] for item in document["open_questions"] if item["status"] == "open"
    ]
    document["generated_at"] = _now()
    from app.research.mapping import _write

    _write(results_path(dataset_id, root), document)
    return document


def scientific_view(document: dict) -> dict:
    """Contenido comparable, sin la fecha de generación."""

    ignored = {"generated_at"}
    return {key: value for key, value in document.items() if key not in ignored}
