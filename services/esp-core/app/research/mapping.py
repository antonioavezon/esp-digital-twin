"""Mapeo semántico de columnas. No modifica RAW, manifest ni preprocess.

Una sugerencia determinista nunca queda en estado validated.
La validación entra solo por una revisión explícita.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.research.variables import (
    CONFIDENCE,
    DERIVABLE_RELATIONS,
    EVIDENCE_TYPES,
    FAMILIES,
    LOCATIONS,
    STATUSES,
    canonical_by_id,
    expected_variable_ids,
)

MAPPING_SCHEMA = "1.0"
MAPPING_VERSION = "0.1"
_SLUG = re.compile(r"[^a-z0-9]+")
_RANGE = re.compile(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$")


class MappingError(Exception):
    def __init__(self, code: str, status: int = 400, **details):
        self.code = code
        self.status = status
        self.details = details
        super().__init__(code)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slug(value: str | None) -> str:
    text = _SLUG.sub("-", (value or "").strip().lower()).strip("-")
    return text or "blank"


def signature_id(raw_name: str | None, raw_unit: str | None) -> str:
    if not raw_name:
        return "S-blank"
    unit = "nou" if not raw_unit else _slug(raw_unit)
    return f"S-{_slug(raw_name)}-{unit}"


def column_ref(dataset_id: str, file_id: str, sheet: str, block_id: str, position: int, raw_name: str | None) -> str:
    return f"{dataset_id}/{file_id}/{sheet}/{block_id}/c{int(position):02d}/{_slug(raw_name)}"


def _column_letters(position: int) -> str:
    letters = ""
    number = int(position)
    while number:
        number, rest = divmod(number - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def _parse_range(text: str) -> tuple[int, int, int, int] | None:
    match = _RANGE.match(text or "")
    if not match:
        return None

    def column(label: str) -> int:
        value = 0
        for char in label:
            value = value * 26 + ord(char) - 64
        return value

    return column(match.group(1)), int(match.group(2)), column(match.group(3)), int(match.group(4))


def suggest(raw_name: str | None, raw_unit: str | None, samples: dict | None = None) -> dict:
    """Reglas deterministas. El rango numérico no asigna una variable."""

    del samples  # el rango no es evidencia
    text = (raw_name or "").strip()
    lowered = text.lower()
    unit = (raw_unit or "").strip().lower()
    if not text:
        return {
            "status": "not_applicable",
            "canonical_id": None,
            "quantity_family": None,
            "confidence": None,
            "evidence": [],
            "notes": "Columna vacía. Se usa como separación y no representa una variable física.",
        }
    if lowered == "pressure":
        return _family_only(
            "pressure",
            text,
            "El encabezado dice Pressure y no indica el punto. No es P_int, P_wf ni ΔP.",
        )
    if lowered == "power":
        return _family_only(
            "power",
            text,
            "El encabezado dice Power y no distingue potencia hidráulica, de eje o eléctrica.",
        )
    if lowered in {"dp2-3", "dp2–3"}:
        return _unmapped(
            "DP2-3 no identifica los puntos 2 y 3. No se asigna diferencia de presión de bomba.",
            text,
        )
    if lowered == "gvf" or lowered.startswith("gvf"):
        return _unmapped(
            "El encabezado no es la variable GVF con unidad explícita. "
            "El sufijo y la unidad faltan, así que no se asigna gas_volume_fraction.",
            text,
        )
    if lowered in {"flow rate", "flow"}:
        return _family_only(
            "flow",
            text,
            "El encabezado indica un caudal y no dice si es líquido, gas o total, ni trae unidad.",
        )
    if "rotary speed" in lowered and unit == "rpm":
        return _candidate(
            "rotary_speed",
            "high",
            [
                {"type": "explicit_header", "value": text},
                {"type": "explicit_unit", "value": raw_unit},
            ],
            "El nombre y la unidad rpm están en el encabezado. Queda como candidate hasta una revisión.",
        )
    if lowered == "rotary speed":
        return _candidate(
            "rotary_speed",
            "medium",
            [{"type": "explicit_header", "value": text}],
            "El encabezado nombra la velocidad de rotación y no escribe la unidad. No se valida.",
        )
    return _unmapped("No hay una regla explícita para este encabezado.")


def _family_only(family: str, header: str, notes: str) -> dict:
    return {
        "status": "unmapped",
        "canonical_id": None,
        "quantity_family": family,
        "confidence": None,
        "evidence": [{"type": "explicit_header", "value": header}],
        "notes": notes,
    }


def _unmapped(notes: str, header: str | None = None) -> dict:
    evidence = [{"type": "explicit_header", "value": header}] if header else []
    return {
        "status": "unmapped",
        "canonical_id": None,
        "quantity_family": None,
        "confidence": None,
        "evidence": evidence,
        "notes": notes,
    }


def _candidate(canonical_id: str, confidence: str, evidence: list[dict], notes: str) -> dict:
    variable = canonical_by_id(canonical_id)
    return {
        "status": "candidate",
        "canonical_id": canonical_id,
        "quantity_family": variable["family"] if variable else None,
        "confidence": confidence,
        "evidence": evidence,
        "notes": notes,
    }


def _merges(preprocess: dict) -> dict[str, list[tuple[int, int, int, int]]]:
    found: dict[str, list[tuple[int, int, int, int]]] = {}
    for item in preprocess.get("files") or []:
        workbook = ((item.get("structure") or {}).get("workbook") or {})
        for merge in workbook.get("merged_cells") or []:
            parsed = _parse_range(merge.get("range") or "")
            if parsed:
                found.setdefault(merge.get("sheet") or "", []).append(parsed)
    return found


def _group_label(merges, sheet: str, header_row: int, position: int, stacks: dict) -> str | None:
    for start_col, start_row, end_col, end_row in merges.get(sheet) or []:
        if not (start_row <= header_row <= end_row and start_col <= position <= end_col):
            continue
        origin = stacks.get(start_col) or []
        offset = header_row - start_row
        if 0 <= offset < len(origin) and isinstance(origin[offset], str) and origin[offset].strip():
            return origin[offset].strip()
    return None


def _observations(root: Path, preprocess: dict) -> dict:
    """Encabezados reales, solo lectura. Si el libro no está, se usa preprocess."""
    try:
        from app.research.profiling import profile_workbook
    except ImportError:
        return {}
    found = {}
    for item in preprocess.get("files") or []:
        relative = item.get("relative_path")
        if not relative:
            continue
        path = root / relative
        if not path.is_file():
            continue
        try:
            profile = profile_workbook(path)
        except Exception:
            continue
        sheets = {}
        for sheet in profile.get("sheets") or []:
            blocks = {}
            for index, block in enumerate(sheet.get("blocks") or [], start=1):
                columns = {}
                for column in block.get("columns") or []:
                    columns[column["index"]] = {
                        "headers": column.get("headers") or [],
                        "min": column.get("min"),
                        "max": column.get("max"),
                        "first": column.get("first"),
                        "last": column.get("last"),
                    }
                blocks[f"B{index:02d}"] = columns
            sheets[sheet["name"]] = blocks
        found[item.get("original_filename")] = sheets
    return found


def build_mapping(
    preprocess: dict,
    manifest: dict | None = None,
    root: Path | None = None,
    now: str | None = None,
    observations: dict | None = None,
) -> dict:
    stamp = now or _now()
    dataset_id = preprocess.get("dataset_id") or (manifest or {}).get("dataset_id")
    if not dataset_id:
        raise MappingError("unknown_dataset", 404)
    if observations is None:
        observations = _observations(root, preprocess) if root is not None else {}
    merges = _merges(preprocess)
    sha_by_name = {
        item.get("original_filename"): item.get("sha256")
        for item in (manifest or {}).get("files") or []
    }
    grouped: dict[str, dict] = {}
    for item in preprocess.get("files") or []:
        filename = item.get("original_filename")
        file_id = item.get("file_id") or "F00"
        workbook = ((item.get("structure") or {}).get("workbook") or {})
        for sheet in workbook.get("sheets") or []:
            for block in sheet.get("blocks") or []:
                observed = (
                    observations.get(filename, {}).get(sheet.get("name"), {}).get(block.get("block_id"), {})
                )
                stacks = {index: (column.get("headers") or []) for index, column in observed.items()}
                for header in block.get("headers") or []:
                    raw_name = header.get("raw_name")
                    raw_unit = header.get("unit")
                    key = signature_id(raw_name, raw_unit)
                    position = header.get("position")
                    stack = list(stacks.get(position) or [])
                    occurrence = {
                        "column_ref": column_ref(
                            dataset_id, file_id, sheet.get("name"), block.get("block_id"), position, raw_name
                        ),
                        "file": filename,
                        "file_id": file_id,
                        "sheet": sheet.get("name"),
                        "block_id": block.get("block_id"),
                        "column_index": position,
                        "column_letter": _column_letters(position),
                        "header_stack": stack,
                        "group_label": _group_label(
                            merges, sheet.get("name"), block.get("header_row") or block.get("start_row") or 0, position, stacks
                        ),
                        "primitive_type": header.get("primitive_type"),
                        "empty": bool(header.get("empty")),
                        "source_sha256": sha_by_name.get(filename),
                        "min": (observed.get(position) or {}).get("min"),
                        "max": (observed.get(position) or {}).get("max"),
                        "example": (observed.get(position) or {}).get("first"),
                    }
                    bucket = grouped.setdefault(
                        key,
                        {
                            "raw_name": raw_name,
                            "raw_unit": raw_unit,
                            "normalized_name": header.get("normalized_name"),
                            "occurrences": [],
                            "group_labels": [],
                        },
                    )
                    bucket["occurrences"].append(occurrence)
                    label = occurrence.get("group_label")
                    if label and label not in bucket["group_labels"]:
                        bucket["group_labels"].append(label)
    variables = []
    for index, key in enumerate(sorted(grouped), start=1):
        bucket = grouped[key]
        decision = suggest(bucket["raw_name"], bucket["raw_unit"])
        canonical = canonical_by_id(decision["canonical_id"]) if decision["canonical_id"] else None
        evidence = [
            item for item in decision["evidence"] if item.get("type") in {"explicit_header", "explicit_unit"}
        ]
        if decision["status"] == "candidate" and not any(item["type"] == "explicit_header" for item in evidence):
            evidence.insert(0, {"type": "explicit_header", "value": bucket["raw_name"]})
        record = {
            "mapping_id": f"M{index:03d}",
            "signature_id": key,
            "source": {
                "raw_name": bucket["raw_name"],
                "raw_unit": bucket["raw_unit"],
                "normalized_name": bucket["normalized_name"],
                "group_labels": bucket["group_labels"],
                "occurrences": bucket["occurrences"],
            },
            "quantity_family": decision["quantity_family"],
            "location": "unknown",
            "canonical": _canonical_view(canonical),
            "evidence": evidence,
            "evidence_ids": ["E001"] if evidence else [],
            "confidence": decision["confidence"],
            "status": decision["status"],
            "notes": decision["notes"],
            "revision": 1,
            "created_at": stamp,
            "updated_at": stamp,
            "history": [
                {
                    "revision": 1,
                    "at": stamp,
                    "status": decision["status"],
                    "canonical_id": decision["canonical_id"],
                    "confidence": decision["confidence"],
                    "evidence": evidence,
                    "notes": decision["notes"],
                    "action": "initial",
                }
            ],
        }
        variables.append(record)
    source = (manifest or {}).get("source") or preprocess.get("source") or {}
    document = {
        "schema_version": MAPPING_SCHEMA,
        "mapping_version": MAPPING_VERSION,
        "dataset_id": dataset_id,
        "created_at": stamp,
        "updated_at": stamp,
        "status": "in_review",
        "semantic_status": "mapping_in_progress",
        "lineage": {
            "preprocess_schema_version": preprocess.get("schema_version"),
            "mapping_schema_version": MAPPING_SCHEMA,
            "source_sha256": sha_by_name,
        },
        "evidence_sources": [
            {
                "id": "E001",
                "kind": "dataset",
                "title": source.get("title"),
                "doi": source.get("doi") or source.get("dataset_doi"),
            },
            {
                "id": "E002",
                "kind": "article",
                "title": source.get("title"),
                "doi": source.get("article_doi"),
                "used": False,
            },
        ],
        "variables": variables,
        "unmapped_columns": [
            item["signature_id"] for item in variables if item["status"] == "unmapped"
        ],
        "derivable_relations": _relations(variables),
        "review_notes": (
            "El artículo asociado no está incorporado al repositorio, así que no se cita como evidencia de columnas. "
            "Las celdas combinadas pueden mostrar un rótulo de grupo sobre dos columnas; "
            "ese rótulo no define por sí solo la magnitud. "
            "No se infiere unidad por el rango numérico y no se ejecuta ninguna relación derivada."
        ),
    }
    document["missing_expected_variables"] = [
        item["id"] for item in coverage_of(document)["expected"] if item["state"] == "not_found"
    ]
    document["coverage"] = coverage_of(document)
    return document


def _canonical_view(variable: dict | None) -> dict | None:
    if not variable:
        return None
    return {
        "id": variable["id"],
        "symbol": variable["symbol"],
        "quantity": variable["quantity"],
        "si_unit": variable["si_unit"],
    }


def _relations(variables: list[dict]) -> list[dict]:
    available = {
        item["canonical"]["id"]
        for item in variables
        if item.get("canonical") and item["status"] in {"candidate", "reviewed", "validated"}
    }
    relations = []
    for item in DERIVABLE_RELATIONS:
        relations.append(
            {
                **item,
                "requires": list(item["requires"]),
                "inputs_available": all(name in available for name in item["requires"]),
                "calculation_status": "not_executed",
            }
        )
    return relations


def experimental_context(raw_name: str | None, raw_unit: str | None, header_stack: list | None) -> dict | None:
    """Un número guardado en el encabezado es una condición, no una serie medida."""

    del raw_name
    numbers = [
        item
        for item in (header_stack or [])
        if isinstance(item, (int, float)) and not isinstance(item, bool)
    ]
    if not numbers:
        return None
    return {"value": numbers[-1], "unit": raw_unit, "source": "header_stack"}


def raw_hint_for(raw_name: str | None) -> dict | None:
    """Pista léxica. No asigna variable canónica ni cambia el estado."""

    lowered = (raw_name or "").strip().lower()
    if lowered == "gvf" or lowered.startswith("gvf"):
        return {
            "possible_target": "gas_volume_fraction",
            "reason": "lexical_similarity",
            "status": "needs_evidence",
            "evidence_required": True,
            "requires_external_evidence": True,
            "question_ids": ["Q002"],
        }
    if lowered in {"dp2-3", "dp2–3"}:
        return {
            "possible_target": "pump_pressure_difference",
            "quantity_family_candidate": "pressure",
            "reason": "lexical_pattern",
            "status": "needs_evidence",
            "evidence_required": True,
            "requires_external_evidence": True,
            "question_ids": ["Q001"],
        }
    if lowered in {"flow rate", "flow"}:
        return {
            "possible_targets": ["liquid_flow_rate", "gas_flow_rate"],
            "reason": "quantity_family_only",
            "status": "needs_evidence",
            "evidence_required": True,
            "requires_external_evidence": True,
            "question_ids": ["Q003", "Q004"],
        }
    return None


def _context_label(context: dict | None) -> str | None:
    if not context or context.get("value") is None:
        return None
    value = context["value"]
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    unit = context.get("unit") or ""
    return f"{value} {unit}".strip()


def _semantic_role(raw_name: str | None, status: str | None, occurrences: list[dict]) -> str:
    if not raw_name or status == "not_applicable":
        return "structural"
    has_series = any(item.get("example") is not None or item.get("min") is not None for item in occurrences)
    has_context = any(item.get("experimental_context") for item in occurrences)
    if has_context and not has_series:
        return "condition"
    if has_series:
        return "measurement"
    return "unknown"


def annotate_mapping(document: dict) -> dict:
    """Añade contexto, rol y pistas sin cambiar estado, confianza ni variable canónica."""

    variables = document.get("variables") or []
    by_block: dict[tuple, list[dict]] = {}
    for item in variables:
        source = item.setdefault("source", {})
        raw_name = source.get("raw_name")
        raw_unit = source.get("raw_unit")
        for occurrence in source.get("occurrences") or []:
            occurrence["experimental_context"] = experimental_context(
                raw_name, raw_unit, occurrence.get("header_stack") or []
            )
            if occurrence.get("experimental_context"):
                key = (occurrence.get("file"), occurrence.get("sheet"), occurrence.get("block_id"))
                label = _context_label(occurrence["experimental_context"])
                entry = {
                    "raw_name": raw_name,
                    "value": occurrence["experimental_context"]["value"],
                    "unit": occurrence["experimental_context"].get("unit"),
                    "source": "header_stack",
                    "label": label,
                }
                found = by_block.setdefault(key, [])
                if entry not in found:
                    found.append(entry)
    for item in variables:
        source = item.setdefault("source", {})
        for occurrence in source.get("occurrences") or []:
            key = (occurrence.get("file"), occurrence.get("sheet"), occurrence.get("block_id"))
            own = _context_label(occurrence.get("experimental_context"))
            occurrence["block_conditions"] = [
                entry for entry in by_block.get(key, []) if entry.get("label") != own
            ]
        labels = []
        for occurrence in source.get("occurrences") or []:
            own = _context_label(occurrence.get("experimental_context"))
            if own:
                labels.append((occurrence["experimental_context"]["value"], own))
            else:
                for entry in occurrence.get("block_conditions") or []:
                    labels.append((entry.get("value"), entry.get("label")))
        ordered = []
        for _, label in sorted(labels, key=lambda pair: (pair[0] is None, str(pair[0]))):
            if label and label not in ordered:
                ordered.append(label)
        source["context_labels"] = ordered
        source["files"] = sorted({item.get("file") for item in source.get("occurrences") or [] if item.get("file")})
        source["sheets"] = sorted({item.get("sheet") for item in source.get("occurrences") or [] if item.get("sheet")})
        item["semantic_role"] = _semantic_role(source.get("raw_name"), item.get("status"), source.get("occurrences") or [])
        item["raw_hint"] = raw_hint_for(source.get("raw_name"))
    document["coverage"] = coverage_of(document)
    return document


def coverage_of(document: dict) -> dict:
    variables = document.get("variables") or []
    counts = {status: 0 for status in STATUSES}
    for item in variables:
        counts[item.get("status") or "unmapped"] = counts.get(item.get("status") or "unmapped", 0) + 1
    by_variable: dict[str, str] = {}
    identified: dict[str, list[str]] = {}
    hinted: dict[str, list[str]] = {}
    rank = {"rejected": 0, "candidate": 1, "reviewed": 2, "validated": 3}
    for item in variables:
        raw_name = (item.get("source") or {}).get("raw_name")
        canonical = (item.get("canonical") or {}).get("id")
        status = item.get("status")
        if canonical and status in rank:
            current = by_variable.get(canonical)
            if current is None or rank[status] > rank[current]:
                by_variable[canonical] = status
            if status in {"candidate", "reviewed", "validated"} and raw_name and raw_name not in identified.setdefault(canonical, []):
                identified[canonical].append(raw_name)
        hint = item.get("raw_hint") or {}
        targets = []
        if hint.get("possible_target"):
            targets.append(hint["possible_target"])
        targets.extend(hint.get("possible_targets") or [])
        for target in targets:
            if raw_name and raw_name not in hinted.setdefault(target, []):
                hinted[target].append(raw_name)
    expected = []
    for variable_id in expected_variable_ids():
        variable = canonical_by_id(variable_id)
        state = by_variable.get(variable_id, "not_found")
        names = sorted(set(identified.get(variable_id, []) + hinted.get(variable_id, [])))
        if variable_id in identified:
            raw_status = "identified"
        elif variable_id in hinted:
            raw_status = "possible"
            if state == "not_found":
                state = "needs_evidence"
        else:
            raw_status = "none"
        expected.append(
            {
                "id": variable_id,
                "symbol": variable["symbol"],
                "state": state,
                "raw_evidence": names,
                "raw_status": raw_status,
                "present": state in {"candidate", "reviewed", "validated"},
                "is_candidate": state == "candidate",
                "mapped": state in {"reviewed", "validated"},
                "validated": state == "validated",
            }
        )
    return {
        "signatures": len(variables),
        "occurrences": sum(len((item.get("source") or {}).get("occurrences") or []) for item in variables),
        "by_status": counts,
        "validated": counts.get("validated", 0),
        "candidate": counts.get("candidate", 0),
        "unmapped": counts.get("unmapped", 0),
        "rejected": counts.get("rejected", 0),
        "reviewed": counts.get("reviewed", 0),
        "not_applicable": counts.get("not_applicable", 0),
        "expected": expected,
        "expected_present": [item["id"] for item in expected if item["present"]],
        "expected_missing": [item["id"] for item in expected if item["state"] == "not_found"],
    }


def mapping_path(dataset_id: str, root: Path | None = None) -> Path:
    from app.research.datasets import data_root

    base = root or data_root()
    return base / "datasets" / dataset_id / "metadata" / "mapping.json"


def load_mapping(dataset_id: str, root: Path | None = None) -> dict:
    path = mapping_path(dataset_id, root)
    if not path.is_file():
        raise MappingError("mapping_missing", 404, dataset_id=dataset_id)
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_mapping(dataset_id: str, root: Path | None = None) -> dict:
    path = mapping_path(dataset_id, root)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    from app.research.datasets import data_root

    base = root or data_root()
    metadata = base / "datasets" / dataset_id / "metadata"
    preprocess_path = metadata / "preprocess.json"
    if not preprocess_path.is_file():
        raise MappingError("preprocess_missing", 404, dataset_id=dataset_id)
    preprocess = json.loads(preprocess_path.read_text(encoding="utf-8"))
    manifest_path = metadata / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    document = build_mapping(preprocess, manifest, base)
    _write(path, document)
    from app.research.results import refresh_stage_results

    refresh_stage_results(dataset_id, base)
    return document


def _write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        temporary.chmod(0o666)
    except OSError:
        pass
    temporary.replace(path)
    try:
        path.chmod(0o666)
    except OSError:
        pass


def _check_decision(payload: dict, *, require_status: bool) -> dict:
    status = payload.get("status")
    if require_status or "status" in payload:
        if status not in STATUSES:
            raise MappingError("invalid_status", 422, received=status)
    confidence = payload.get("confidence")
    if confidence is not None and confidence not in CONFIDENCE:
        raise MappingError("invalid_confidence", 422, confidence=confidence)
    if status in {"candidate", "reviewed", "validated", "rejected"} and confidence not in CONFIDENCE:
        raise MappingError("invalid_confidence", 422, confidence=confidence)
    canonical_id = payload.get("canonical_id")
    variable = None
    if canonical_id:
        variable = canonical_by_id(canonical_id)
        if variable is None:
            raise MappingError("invalid_canonical_variable", 422, canonical_id=canonical_id)
    if status == "validated" and variable is None:
        raise MappingError("invalid_canonical_variable", 422, canonical_id=canonical_id)
    if status in {"unmapped", "not_applicable"} and canonical_id:
        raise MappingError("invalid_canonical_variable", 422, canonical_id=canonical_id)
    if status == "rejected" and variable is None:
        raise MappingError("invalid_canonical_variable", 422, canonical_id=canonical_id)
    family = payload.get("quantity_family")
    if family is not None and family not in FAMILIES:
        raise MappingError("invalid_quantity_family", 422, quantity_family=family)
    if variable and family and family != variable["family"]:
        raise MappingError("invalid_quantity_family", 422, quantity_family=family)
    location = payload.get("location", "unknown")
    if location not in LOCATIONS:
        raise MappingError("invalid_location", 422, location=location)
    evidence = payload.get("evidence") or []
    if not isinstance(evidence, list):
        raise MappingError("invalid_evidence", 422)
    for item in evidence:
        if not isinstance(item, dict) or item.get("type") not in EVIDENCE_TYPES:
            raise MappingError("invalid_evidence", 422, evidence=item)
    if status in {"candidate", "reviewed", "validated", "rejected"} and not evidence:
        raise MappingError("evidence_required", 422)
    return {
        "status": status,
        "confidence": confidence,
        "canonical_id": canonical_id,
        "quantity_family": variable["family"] if variable else family,
        "location": location,
        "evidence": evidence,
        "notes": payload.get("notes"),
    }


def apply_decision(document: dict, payload: dict, *, mapping_id: str | None = None) -> dict:
    decision = _check_decision(payload, require_status=True)
    variables = document.setdefault("variables", [])
    if mapping_id:
        record = next((item for item in variables if item.get("mapping_id") == mapping_id), None)
        if record is None:
            raise MappingError("unknown_mapping", 404, mapping_id=mapping_id)
    else:
        signature = payload.get("signature_id")
        record = next((item for item in variables if item.get("signature_id") == signature), None)
        if record is None:
            raise MappingError("unknown_signature", 404, signature_id=signature)
    stamp = _now()
    revision = int(record.get("revision") or 1) + 1
    variable = canonical_by_id(decision["canonical_id"]) if decision["canonical_id"] else None
    record["status"] = decision["status"]
    record["confidence"] = decision["confidence"]
    record["quantity_family"] = decision["quantity_family"]
    record["location"] = decision["location"]
    record["canonical"] = _canonical_view(variable)
    record["evidence"] = decision["evidence"]
    record["evidence_ids"] = ["E001"] if decision["evidence"] else []
    record["notes"] = decision["notes"]
    record["revision"] = revision
    record["updated_at"] = stamp
    record.setdefault("history", []).append(
        {
            "revision": revision,
            "at": stamp,
            "status": decision["status"],
            "canonical_id": decision["canonical_id"],
            "confidence": decision["confidence"],
            "evidence": decision["evidence"],
            "notes": decision["notes"],
            "action": "review",
        }
    )
    document["updated_at"] = stamp
    document["unmapped_columns"] = [
        item["signature_id"] for item in variables if item["status"] == "unmapped"
    ]
    document["derivable_relations"] = _relations(variables)
    document["coverage"] = coverage_of(document)
    document["missing_expected_variables"] = document["coverage"]["expected_missing"]
    document["status"] = "in_review"
    document["semantic_status"] = "mapping_in_progress"
    return record


def save_decision(dataset_id: str, payload: dict, *, mapping_id: str | None = None, root: Path | None = None) -> dict:
    document = ensure_mapping(dataset_id, root)
    record = apply_decision(document, payload, mapping_id=mapping_id)
    _write(mapping_path(dataset_id, root), document)
    from app.research.results import refresh_stage_results

    refresh_stage_results(dataset_id, root)
    return record
