"""Descubre datasets a partir de sus manifiestos. No los deja fijos en código."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.research.contract import SCHEMA_VERSION
from app.research.schema import DATASETS

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")


def _inside(root: Path, path: Path) -> bool:
    root_resolved = root.resolve()
    resolved = path.resolve()
    return resolved == root_resolved or root_resolved in resolved.parents


def _legacy_names(root: Path) -> list[str]:
    spec = DATASETS["001"]
    folder = root / "001"
    if not folder.is_dir():
        return []
    if all((folder / name).is_file() for name in spec["files"]):
        return list(spec["files"])
    return []


def _legacy_record() -> dict:
    spec = DATASETS["001"]
    entries = []
    for index, name in enumerate(spec["files"], start=1):
        entries.append(
            {
                "file_id": f"F{index:02d}",
                "original_filename": name,
                "stored_filename": name,
                "relative_path": f"001/{name}",
                "format": "xlsx",
                "source": spec["source_type"],
                "linked_from": None,
            }
        )
    return {
        "dataset_id": "001",
        "title": spec["title"],
        "short_title": spec["short_title"],
        "author": spec["author"],
        "dataset_doi": spec["dataset_doi"],
        "article_doi": spec["article_doi"],
        "source_type": spec["source_type"],
        "processing_status": spec["processing_status"],
        "status": "imported",
        "distribution": "public",
        "imported_at": None,
        "organization": None,
        "source_url": None,
        "license": None,
        "notes": None,
        "files": spec["files"],
        "file_entries": entries,
    }


def _record_from_manifest(data: dict) -> dict | None:
    if data.get("schema_version") != SCHEMA_VERSION:
        return None
    dataset_id = data.get("dataset_id")
    if not isinstance(dataset_id, str) or not _ID.match(dataset_id):
        return None
    source = data.get("source") if isinstance(data.get("source"), dict) else {}
    files = data.get("files")
    if not isinstance(files, list) or not files:
        return None
    entries = []
    names = []
    for item in files:
        if not isinstance(item, dict):
            return None
        name = item.get("original_filename")
        relative = item.get("relative_path")
        if not isinstance(name, str) or not name or "/" in name or "\\" in name:
            return None
        if not isinstance(relative, str) or relative.startswith(("/", "\\")) or ".." in Path(relative).parts:
            return None
        names.append(name)
        entries.append(item)
    title = source.get("title")
    return {
        "dataset_id": dataset_id,
        "title": title,
        "short_title": source.get("short_title") or title,
        "author": source.get("author"),
        "dataset_doi": source.get("doi"),
        "article_doi": source.get("article_doi"),
        "source_type": source.get("type"),
        "processing_status": "raw",
        "status": data.get("status") or "imported",
        "distribution": data.get("distribution") or "unknown",
        "imported_at": data.get("imported_at"),
        "organization": source.get("organization"),
        "source_url": source.get("url"),
        "license": source.get("license"),
        "notes": source.get("notes"),
        "files": tuple(names),
        "file_entries": entries,
    }


def _files_ready(root: Path, record: dict) -> bool:
    for entry in record["file_entries"]:
        path = root / entry["relative_path"]
        if not _inside(root, path) or not path.is_file():
            return False
    return True


def scan(root: Path) -> tuple[list[dict], list[dict]]:
    """Devuelve datasets válidos y errores que no deben tumbar la aplicación."""
    records: list[dict] = []
    errors: list[dict] = []
    seen: set[str] = set()
    if not root.is_dir():
        return records, errors
    datasets_dir = root / "datasets"
    if datasets_dir.is_dir():
        for child in sorted(datasets_dir.iterdir(), key=lambda item: item.name):
            if not child.is_dir() or child.name.startswith(".") or child.name.endswith(".partial"):
                continue
            manifest_path = child / "metadata" / "manifest.json"
            if not manifest_path.is_file():
                errors.append({"dataset_id": child.name, "error": "incomplete_dataset"})
                continue
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                errors.append({"dataset_id": child.name, "error": "invalid_manifest"})
                continue
            if not isinstance(data, dict):
                errors.append({"dataset_id": child.name, "error": "invalid_manifest"})
                continue
            if data.get("dataset_id") != child.name:
                errors.append({"dataset_id": child.name, "error": "invalid_manifest"})
                continue
            record = _record_from_manifest(data)
            if record is None:
                errors.append({"dataset_id": child.name, "error": "invalid_manifest"})
                continue
            if not _files_ready(root, record):
                errors.append({"dataset_id": child.name, "error": "incomplete_dataset"})
                continue
            records.append(record)
            seen.add(record["dataset_id"])
    if "001" not in seen and _legacy_names(root):
        legacy = _legacy_record()
        if _files_ready(root, legacy):
            records.append(legacy)
    records.sort(key=lambda item: item["dataset_id"])
    return records, errors


def used_ids(root: Path) -> set[str]:
    found, _errors = scan(root)
    used = {item["dataset_id"] for item in found}
    datasets_dir = root / "datasets"
    if datasets_dir.is_dir():
        for child in datasets_dir.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                used.add(child.name)
    if _legacy_names(root):
        used.add("001")
    return used


def allocate_id(root: Path) -> str:
    """Siguiente identificador numérico. 001 sigue si ya existe; el próximo es 002."""
    used = used_ids(root)
    for number in range(1, 10000):
        candidate = f"{number:03d}"
        if candidate in used:
            continue
        folder = root / "datasets" / candidate
        try:
            folder.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return candidate
    raise RuntimeError("dataset_id_exhausted")
