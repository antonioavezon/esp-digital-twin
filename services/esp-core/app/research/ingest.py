"""Ingesta de datasets. Copia el crudo y no lo modifica.

El archivo original es la evidencia. manifest.json dice qué es.
preprocess.json dice cómo está organizado. Ninguno sustituye al crudo.
"""

from __future__ import annotations

import errno
import fcntl
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.research.contract import (
    PROFILER_NAME,
    PROFILER_VERSION,
    SCHEMA_VERSION,
)
from app.research.datasets import data_root
from app.research.manifest import sha256_file
from app.research.registry import allocate_id, scan
from app.research.structure import StructureError, detect_format, profile_path

_SAFE_NAME = re.compile(r"^[^\\/\x00]{1,180}$")


class IngestError(Exception):
    def __init__(self, code: str, status: int = 400, **details):
        self.code = code
        self.status = status
        self.details = details
        super().__init__(code)


def max_upload_bytes() -> int:
    raw = os.environ.get("ESP_DATA_MAX_UPLOAD_MB", "32")
    try:
        megabytes = int(raw)
    except ValueError:
        megabytes = 32
    if megabytes < 1:
        megabytes = 32
    return megabytes * 1024 * 1024


def _relax(path: Path) -> None:
    """El proceso del contenedor no es el usuario del host. El directorio queda borrable."""
    try:
        path.chmod(0o777 if path.is_dir() else 0o666)
    except OSError:
        return


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _safe_filename(name: str) -> str:
    base = Path(name or "").name
    if not base or base in {".", ".."} or base.startswith("."):
        raise IngestError("invalid_filename")
    if not _SAFE_NAME.match(base) or "/" in base or "\\" in base:
        raise IngestError("invalid_filename")
    return base


def _lock(root: Path):
    folder = root / "datasets"
    folder.mkdir(parents=True, exist_ok=True)
    handle = (folder / ".lock").open("a+")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def _os_error(exc: OSError) -> IngestError:
    if exc.errno == errno.ENOSPC:
        return IngestError("disk_full", 507)
    if exc.errno in {errno.EACCES, errno.EPERM}:
        return IngestError("permission_denied", 403)
    return IngestError("copy_failed", 422)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _relax(path.parent)
    temporary = path.with_suffix(path.suffix + ".partial")
    try:
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, path)
        _relax(path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise _os_error(exc) from exc


def _copy_exact(source: Path, dest: Path, expected: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    _relax(dest.parent)
    partial = dest.with_name(dest.name + ".partial")
    try:
        with source.open("rb") as incoming, partial.open("wb") as outgoing:
            while True:
                chunk = incoming.read(1024 * 1024)
                if not chunk:
                    break
                outgoing.write(chunk)
        if sha256_file(partial) != expected:
            partial.unlink(missing_ok=True)
            raise IngestError("copy_failed", 422)
        os.replace(partial, dest)
        _relax(dest)
    except IngestError:
        raise
    except OSError as exc:
        partial.unlink(missing_ok=True)
        raise _os_error(exc) from exc
    if sha256_file(dest) != expected:
        raise IngestError("copy_failed", 422)


def _hash_index(root: Path) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    records, _errors = scan(root)
    for record in records:
        for entry in record["file_entries"]:
            path = root / entry["relative_path"]
            digest = entry.get("sha256")
            if not isinstance(digest, str) and path.is_file():
                digest = sha256_file(path)
            if not isinstance(digest, str):
                continue
            index.setdefault(digest, []).append(
                {
                    "dataset_id": record["dataset_id"],
                    "filename": entry.get("original_filename"),
                }
            )
    return index


def _intake_dir(root: Path, intake_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", intake_id):
        raise IngestError("intake_missing", 404)
    folder = root / "inbox" / intake_id
    if not folder.is_dir():
        raise IngestError("intake_missing", 404)
    return folder


def create_intake(blobs: list[tuple[str, bytes]]) -> dict:
    if not blobs:
        raise IngestError("no_files")
    root = data_root()
    limit = max_upload_bytes()
    total = 0
    intake_id = uuid.uuid4().hex
    folder = root / "inbox" / intake_id
    payload = folder / "files"
    try:
        payload.mkdir(parents=True, exist_ok=False)
        _relax(folder)
        _relax(payload)
    except OSError as exc:
        raise _os_error(exc) from exc
    known = _hash_index(root)
    seen: dict[str, str] = {}
    files = []
    try:
        for index, (original, content) in enumerate(blobs, start=1):
            total += len(content)
            item = _stage_file(payload, index, original, content, total, limit, known, seen)
            files.append(item)
    except IngestError:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    blocked = any(item["status"] == "error" for item in files)
    document = {
        "schema_version": SCHEMA_VERSION,
        "intake_id": intake_id,
        "created_at": _now(),
        "status": "error" if blocked else "validated",
        "files": files,
    }
    _write_json(folder / "intake.json", document)
    return document


def _stage_file(folder, index, original, content, total, limit, known, seen) -> dict:
    try:
        name = _safe_filename(original)
    except IngestError as exc:
        return _failed(index, original or "", exc.code)
    if len(content) > limit or total > limit:
        return _failed(index, name, "file_too_large")
    if len(content) == 0:
        return _failed(index, name, "empty_file")
    stored = name
    if (folder / stored).exists():
        stem = Path(name).stem
        suffix = Path(name).suffix
        stored = f"{stem}-{index}{suffix}"
    path = folder / stored
    try:
        path.write_bytes(content)
        _relax(path)
    except OSError as exc:
        raise _os_error(exc) from exc
    digest = sha256_file(path)
    if digest != _sha_bytes(content):
        return _failed(index, name, "copy_failed", stored)
    item = {
        "file_id": f"F{index:02d}",
        "original_filename": name,
        "stored_filename": stored,
        "size_bytes": len(content),
        "sha256": digest,
        "status": "validated",
        "warnings": [],
        "errors": [],
        "duplicates": [],
        "format": None,
        "structure": None,
    }
    if digest in seen:
        item["status"] = "error"
        item["errors"].append("duplicate_in_selection")
        return item
    seen[digest] = name
    item["duplicates"] = known.get(digest, [])
    try:
        fmt = detect_format(path, name)
        profiled = profile_path(path, fmt, limit)
    except StructureError as exc:
        item["status"] = "error"
        item["errors"].append(exc.code)
        return item
    item["format"] = fmt
    item["warnings"] = profiled["warnings"]
    item["structure"] = profiled["structure"]
    return item


def _sha_bytes(content: bytes) -> str:
    import hashlib

    return hashlib.sha256(content).hexdigest()


def _failed(index: int, name: str, code: str, stored: str | None = None) -> dict:
    return {
        "file_id": f"F{index:02d}",
        "original_filename": name,
        "stored_filename": stored or name,
        "size_bytes": 0,
        "sha256": None,
        "status": "error",
        "warnings": [],
        "errors": [code],
        "duplicates": [],
        "format": None,
        "structure": None,
    }


def read_intake(intake_id: str) -> dict:
    folder = _intake_dir(data_root(), intake_id)
    path = folder / "intake.json"
    if not path.is_file():
        raise IngestError("intake_missing", 404)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IngestError("intake_missing", 404) from exc
    return data


def cancel_intake(intake_id: str) -> dict:
    folder = _intake_dir(data_root(), intake_id)
    shutil.rmtree(folder)
    return {"intake_id": intake_id, "status": "cancelled"}


def commit_intake(intake_id: str, provenance: dict, acknowledge_duplicates: bool) -> dict:
    root = data_root()
    document = read_intake(intake_id)
    if any(item["status"] == "error" for item in document["files"]):
        raise IngestError("invalid_intake", 422, files=document["files"])
    duplicates = [
        {"filename": item["original_filename"], "datasets": item["duplicates"]}
        for item in document["files"]
        if item["duplicates"]
    ]
    if duplicates and not acknowledge_duplicates:
        names = []
        for item in duplicates:
            for found in item["datasets"]:
                label = found.get("dataset_id")
                if label and label not in names:
                    names.append(label)
        shown = ", ".join(names) if names else "?"
        raise IngestError(
            "duplicate_sha",
            409,
            message=f"Este archivo ya existe en Dataset {shown}",
            duplicates=duplicates,
        )
    folder = _intake_dir(root, intake_id)
    lock = _lock(root)
    dataset_id = None
    manifest_written = False
    try:
        dataset_id = allocate_id(root)
        dataset_dir = root / "datasets" / dataset_id
        _relax(dataset_dir)
        raw_dir = dataset_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        _relax(raw_dir)
        stored_files = []
        for item in document["files"]:
            stored_files.append(_place_file(root, folder, dataset_id, item, acknowledge_duplicates))
        source = _source(provenance)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "dataset_id": dataset_id,
            "status": "imported",
            "distribution": "unknown",
            "imported_at": _now(),
            "source": source,
            "files": stored_files,
        }
        metadata = root / "datasets" / dataset_id / "metadata"
        derived = root / "datasets" / dataset_id / "derived"
        derived.mkdir(parents=True, exist_ok=True)
        _relax(derived)
        _relax(metadata)
        _write_json(metadata / "manifest.json", manifest)
        manifest_written = True
        try:
            preprocess = _preprocess(dataset_id, source, stored_files, root)
            _write_json(metadata / "preprocess.json", preprocess)
        except IngestError:
            manifest["status"] = "error"
            _write_json(metadata / "manifest.json", manifest)
            raise
        manifest["status"] = "ready_for_mapping"
        _write_json(metadata / "manifest.json", manifest)
    except IngestError:
        if dataset_id and not manifest_written:
            shutil.rmtree(root / "datasets" / dataset_id, ignore_errors=True)
        raise
    except RuntimeError as exc:
        if dataset_id and not manifest_written:
            shutil.rmtree(root / "datasets" / dataset_id, ignore_errors=True)
        if str(exc) == "dataset_id_exhausted":
            raise IngestError("dataset_id_exhausted", 409) from exc
        raise IngestError("ingest_failed", 422) from exc
    except Exception:
        if dataset_id and not manifest_written:
            shutil.rmtree(root / "datasets" / dataset_id, ignore_errors=True)
        raise
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()
    shutil.rmtree(folder, ignore_errors=True)
    return {"dataset_id": dataset_id, "status": "ready_for_mapping"}


def _place_file(root, inbox, dataset_id, item, acknowledge: bool) -> dict:
    source = inbox / "files" / item["stored_filename"]
    if not source.is_file():
        raise IngestError("file_vanished", 409, filename=item["original_filename"])
    record = {
        "file_id": item["file_id"],
        "original_filename": item["original_filename"],
        "stored_filename": item["stored_filename"],
        "format": item["format"],
        "size_bytes": item["size_bytes"],
        "sha256": item["sha256"],
        "imported_at": _now(),
        "source": None,
        "linked_from": None,
    }
    if item["duplicates"] and acknowledge:
        target = item["duplicates"][0]
        records, _errors = scan(root)
        for dataset in records:
            if dataset["dataset_id"] != target["dataset_id"]:
                continue
            for entry in dataset["file_entries"]:
                if entry.get("sha256") == item["sha256"] or entry.get("original_filename") == target.get("filename"):
                    if (root / entry["relative_path"]).is_file() and sha256_file(root / entry["relative_path"]) == item["sha256"]:
                        record["relative_path"] = entry["relative_path"]
                        record["stored_filename"] = entry.get("stored_filename") or entry["original_filename"]
                        record["linked_from"] = dataset["dataset_id"]
                        return record
        raise IngestError("duplicate_sha", 409, filename=item["original_filename"])
    relative = f"datasets/{dataset_id}/raw/{item['stored_filename']}"
    _copy_exact(source, root / relative, item["sha256"])
    record["relative_path"] = relative
    return record


def _source(provenance: dict) -> dict:
    return {
        "type": _blank(provenance.get("type")),
        "title": _blank(provenance.get("title")),
        "short_title": _blank(provenance.get("title")),
        "author": _blank(provenance.get("author")),
        "organization": _blank(provenance.get("organization")),
        "url": _blank(provenance.get("url")),
        "doi": _blank(provenance.get("doi")),
        "article_doi": _blank(provenance.get("article_doi")),
        "license": _blank(provenance.get("license")),
        "notes": _blank(provenance.get("notes")),
    }


def _preprocess(dataset_id: str, source: dict, files: list[dict], root: Path, previous: dict | None = None) -> dict:
    limit = max_upload_bytes()
    described = []
    for item in files:
        path = root / item["relative_path"]
        if not path.is_file():
            raise IngestError("file_vanished", 409, filename=item["original_filename"])
        if sha256_file(path) != item["sha256"]:
            raise IngestError("copy_failed", 422, filename=item["original_filename"])
        try:
            profiled = profile_path(path, item["format"], limit)
        except StructureError as exc:
            raise IngestError(exc.code, 422, filename=item["original_filename"]) from exc
        described.append(
            {
                "file_id": item["file_id"],
                "original_filename": item["original_filename"],
                "stored_filename": item["stored_filename"],
                "format": item["format"],
                "size_bytes": item["size_bytes"],
                "sha256": item["sha256"],
                "generated_from_sha256": item["sha256"],
                "structure": profiled["structure"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "status": "profiled",
        "profiler": {"name": PROFILER_NAME, "version": PROFILER_VERSION},
        "generated_at": _now(),
        "previous_profiler_version": (previous or {}).get("profiler", {}).get("version"),
        "previous_generated_at": (previous or {}).get("generated_at"),
        "source": {
            "type": source.get("type"),
            "title": source.get("title"),
            "doi": source.get("doi"),
            "article_doi": source.get("article_doi"),
            "license": source.get("license"),
        },
        "files": described,
        "semantic_mapping": {"status": "not_started"},
    }


def stored_manifest(dataset_id: str) -> dict:
    path = data_root() / "datasets" / dataset_id / "metadata" / "manifest.json"
    if not path.is_file():
        raise IngestError("manifest_missing", 404)
    return json.loads(path.read_text(encoding="utf-8"))


def stored_preprocess(dataset_id: str) -> dict:
    path = data_root() / "datasets" / dataset_id / "metadata" / "preprocess.json"
    if not path.is_file():
        raise IngestError("preprocess_missing", 404)
    return json.loads(path.read_text(encoding="utf-8"))


def reprofile(dataset_id: str) -> dict:
    root = data_root()
    manifest_path = root / "datasets" / dataset_id / "metadata" / "manifest.json"
    if not manifest_path.is_file():
        raise IngestError("manifest_missing", 404)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    before = []
    for item in manifest["files"]:
        path = root / item["relative_path"]
        if not path.is_file():
            raise IngestError("file_vanished", 409, filename=item.get("original_filename"))
        before.append(sha256_file(path))
    previous = None
    preprocess_path = manifest_path.with_name("preprocess.json")
    if preprocess_path.is_file():
        previous = json.loads(preprocess_path.read_text(encoding="utf-8"))
    document = _preprocess(dataset_id, manifest.get("source") or {}, manifest["files"], root, previous)
    _write_json(preprocess_path, document)
    after = [sha256_file(root / item["relative_path"]) for item in manifest["files"]]
    if before != after:
        raise IngestError("raw_changed", 422)
    if manifest.get("status") == "error":
        manifest["status"] = "ready_for_mapping"
        _write_json(manifest_path, manifest)
    from app.research.results import refresh_stage_results

    refresh_stage_results(dataset_id, root)
    return document


def bootstrap_dataset_001(root: Path | None = None) -> dict:
    """Registra la metadata del dataset 001 sin copiar ni alterar los xlsx."""
    from app.research.schema import DATASETS

    root = root or data_root()
    spec = DATASETS["001"]
    files = []
    for index, name in enumerate(spec["files"], start=1):
        path = root / "001" / name
        if not path.is_file():
            raise IngestError("incomplete_dataset", 404, filename=name)
        files.append(
            {
                "file_id": f"F{index:02d}",
                "original_filename": name,
                "stored_filename": name,
                "relative_path": f"001/{name}",
                "format": "xlsx",
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "imported_at": None,
                "source": "experimental",
                "linked_from": None,
            }
        )
    source = {
        "type": "experimental",
        "title": spec["title"],
        "short_title": spec["short_title"],
        "author": spec["author"],
        "organization": None,
        "url": None,
        "doi": spec["dataset_doi"],
        "article_doi": spec["article_doi"],
        "license": None,
        "notes": None,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": "001",
        "status": "ready_for_mapping",
        "distribution": "public",
        "imported_at": None,
        "source": source,
        "files": files,
    }
    metadata = root / "datasets" / "001" / "metadata"
    derived = root / "datasets" / "001" / "derived"
    derived.mkdir(parents=True, exist_ok=True)
    preprocess = _preprocess("001", source, files, root)
    _write_json(metadata / "manifest.json", manifest)
    _write_json(metadata / "preprocess.json", preprocess)
    return manifest
