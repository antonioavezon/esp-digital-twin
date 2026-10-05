"""Catálogo de curvas ya digitalizadas. No completa fichas que no pasaron la verificación."""

import json
from functools import lru_cache
from pathlib import Path

CURVE_MODEL = "pump-curves-v0.1"

_INDEX_FIELDS = (
    "id",
    "manufacturer",
    "series",
    "model",
    "frequency_hz",
    "speed_rpm",
    "stage_count_reference",
    "curve_basis",
    "specific_gravity_reference",
    "flow_unit_source",
    "head_unit_source",
    "power_unit_source",
    "source_document",
    "source_page",
    "source_revision",
    "source_method",
    "data_quality",
)


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    path = Path(__file__).resolve().parent / "data" / "reda.json"
    return json.loads(path.read_text(encoding="utf-8"))


def curves() -> list[dict]:
    return load_catalog()["curves"]


def curve_by_id(curve_id: str) -> dict | None:
    for curve in curves():
        if curve["id"] == curve_id:
            return curve
    return None


def index_payload() -> dict:
    listed = []
    for curve in curves():
        listed.append({field: curve[field] for field in _INDEX_FIELDS})
    return {
        "model": CURVE_MODEL,
        "source_document": load_catalog().get("source_document"),
        "source_note": load_catalog().get("source_note"),
        "curves": listed,
    }
