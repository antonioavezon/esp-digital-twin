"""Localización de datasets crudos. No escribe en los libros originales."""

from __future__ import annotations

import os
from pathlib import Path

from app.research.profiling import WorkbookError, preview_sheet, profile_workbook
from app.research.schema import DATASETS, RESEARCH_STAGE


class DatasetUnavailable(Exception):
    pass


class UnknownDataset(Exception):
    pass


class UnknownFile(Exception):
    pass


class UnknownSheet(Exception):
    pass


class UnknownBlock(Exception):
    pass


def data_root() -> Path:
    return Path(os.environ.get("ESP_DATA_ROOT", "/app/data"))


def dataset_dir(dataset_id: str) -> Path:
    return data_root() / dataset_id


def research_health() -> dict:
    return {
        "enabled": True,
        "stage": RESEARCH_STAGE,
        "ai_model": False,
    }


def _files_present(dataset_id: str) -> bool:
    spec = DATASETS[dataset_id]
    folder = dataset_dir(dataset_id)
    if not folder.is_dir():
        return False
    return all((folder / name).is_file() for name in spec["files"])


def research_status() -> dict:
    from app.research.registry import scan

    root = data_root()
    records, errors = scan(root) if root.is_dir() else ([], [])
    available = [item["dataset_id"] for item in records]
    availability = "ready" if available else "dataset_unavailable"
    return {
        **research_health(),
        "physics_ai": False,
        "anomaly_detection": False,
        "availability": availability,
        "datasets": available,
        "errors": errors,
    }


def list_datasets() -> dict:
    from app.research.registry import scan

    status = research_status()
    records, _errors = scan(data_root()) if data_root().is_dir() else ([], [])
    by_id = {item["dataset_id"]: item for item in records}
    items = []
    for dataset_id in status["datasets"]:
        spec = by_id[dataset_id]
        formats = sorted({entry.get("format") for entry in spec["file_entries"] if entry.get("format")})
        items.append(
            {
                "dataset_id": dataset_id,
                "title": spec["title"],
                "short_title": spec["short_title"],
                "source_type": spec["source_type"],
                "processing_status": spec["processing_status"],
                "status": spec["status"],
                "distribution": spec["distribution"],
                "imported_at": spec["imported_at"],
                "dataset_doi": spec["dataset_doi"],
                "file_count": len(spec["files"]),
                "formats": formats,
            }
        )
    return {"availability": status["availability"], "datasets": items, "errors": status["errors"]}


def _require(dataset_id: str) -> dict:
    from app.research.registry import scan

    root = data_root()
    if not root.is_dir():
        raise DatasetUnavailable(dataset_id)
    records, _errors = scan(root)
    for record in records:
        if record["dataset_id"] == dataset_id:
            return record
    if dataset_id in DATASETS:
        raise DatasetUnavailable(dataset_id)
    raise UnknownDataset(dataset_id)


def _workbook_path(dataset_id: str, filename: str) -> Path:
    spec = _require(dataset_id)
    if not filename or "/" in filename or "\\" in filename or ".." in filename:
        raise UnknownFile(filename)
    root = data_root().resolve()
    for entry in spec["file_entries"]:
        names = {entry.get("original_filename"), entry.get("stored_filename")}
        if filename not in names:
            continue
        path = (data_root() / entry["relative_path"]).resolve()
        if root != path and root not in path.parents:
            raise UnknownFile(filename)
        return path
    raise UnknownFile(filename)


def dataset_detail(dataset_id: str) -> dict:
    from app.research.manifest import file_record, sha256_file

    spec = _require(dataset_id)
    files = []
    for entry in spec["file_entries"]:
        filename = entry["original_filename"]
        path = _workbook_path(dataset_id, filename)
        fmt = str(entry.get("format") or path.suffix.lstrip(".")).lower()
        if fmt in {"xlsx", "xlsm"}:
            try:
                record = file_record(dataset_id, path, entry.get("relative_path"))
                record["filename"] = filename
                files.append(record)
            except WorkbookError:
                files.append(
                    {
                        "filename": filename,
                        "relative_path": entry.get("relative_path") or f"{dataset_id}/{filename}",
                        "error": "unreadable_workbook",
                    }
                )
        else:
            files.append(
                {
                    "filename": filename,
                    "relative_path": entry.get("relative_path"),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "format": fmt,
                    "sheets": [],
                }
            )
    return {
        "dataset_id": spec["dataset_id"],
        "title": spec["title"],
        "short_title": spec["short_title"],
        "author": spec["author"],
        "dataset_doi": spec["dataset_doi"],
        "article_doi": spec["article_doi"],
        "source_type": spec["source_type"],
        "processing_status": spec["processing_status"],
        "status": spec["status"],
        "distribution": spec["distribution"],
        "imported_at": spec["imported_at"],
        "organization": spec["organization"],
        "license": spec["license"],
        "notes": spec["notes"],
        "provenance": {
            "source_type": spec["source_type"],
            "role": (
                "Fuente experimental externa. No es user_input, physics_model, "
                "constant, sensor, simulation, ml ni physics_ai."
            ),
        },
        "files": files,
    }


def dataset_profile(dataset_id: str) -> dict:
    from app.research.manifest import sha256_file

    spec = _require(dataset_id)
    files = []
    for filename in spec["files"]:
        path = _workbook_path(dataset_id, filename)
        if path.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise WorkbookError(filename)
        try:
            profile = profile_workbook(path)
        except WorkbookError as exc:
            raise WorkbookError(exc.filename) from exc
        profile["generated_from"] = f"{dataset_id}/{filename}"
        profile["source_sha256"] = sha256_file(path)
        files.append(profile)
    return {
        "dataset_id": dataset_id,
        "tool_version": files[0]["tool_version"] if files else None,
        "files": files,
    }


def dataset_preview(dataset_id: str, filename: str, sheet: str, limit: int, block: int = 1) -> dict:
    path = _workbook_path(dataset_id, filename)
    bounded = max(1, min(int(limit), 50))
    try:
        preview = preview_sheet(path, sheet, bounded, block)
    except WorkbookError as exc:
        raise WorkbookError(exc.filename) from exc
    if not preview:
        raise UnknownSheet(sheet)
    if preview.get("unknown_block"):
        raise UnknownBlock(str(block))
    preview["dataset_id"] = dataset_id
    preview["filename"] = filename
    return preview
