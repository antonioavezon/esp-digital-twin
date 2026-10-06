"""Manifest reproducible de un libro crudo. No modifica el archivo."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from app.research.profiling import profile_workbook
from app.research.schema import DATASETS, TOOL_VERSION


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(dataset_id: str, path, relative_path: str | None = None) -> dict:
    spec = DATASETS.get(
        dataset_id,
        {
            "dataset_id": dataset_id,
            "dataset_doi": None,
            "source_type": "experimental",
            "processing_status": "raw",
        },
    )
    profile = profile_workbook(path)
    sheets = []
    for sheet in profile["sheets"]:
        sheets.append(
            {
                "name": sheet["name"],
                "row_count": sheet["row_count"],
                "column_count": sheet["column_count"],
                "block_count": sheet["block_count"],
                "data_row_count": sheet["data_row_count"],
                "empty_row_count": sheet["empty_row_count"],
                "blocks": [
                    {
                        "start_row": block["start_row"],
                        "end_row": block["end_row"],
                        "header_row_count": block["header_row_count"],
                        "data_row_count": block["data_row_count"],
                        "column_count": block["column_count"],
                        "columns": [
                            {
                                "index": column["index"],
                                "headers": column["headers"],
                                "name": column["name"],
                                "unit": column["unit"],
                            }
                            for column in block["columns"]
                        ],
                    }
                    for block in sheet["blocks"]
                ],
            }
        )
    return {
        "filename": path.name,
        "relative_path": relative_path or f"{dataset_id}/{path.name}",
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "workbook_type": path.suffix.lstrip(".").lower() or None,
        "sheets": sheets,
        "dataset_id": spec["dataset_id"],
        "dataset_doi": spec["dataset_doi"],
        "source_type": spec["source_type"],
        "processing_status": spec["processing_status"],
    }


def build_manifest(dataset_id: str, folder) -> dict:
    spec = DATASETS[dataset_id]
    files = [file_record(dataset_id, folder / name) for name in spec["files"]]
    return {
        "dataset_id": spec["dataset_id"],
        "title": spec["title"],
        "author": spec["author"],
        "dataset_doi": spec["dataset_doi"],
        "article_doi": spec["article_doi"],
        "source_type": spec["source_type"],
        "processing_status": spec["processing_status"],
        "analyzed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "tool_version": TOOL_VERSION,
        "files": files,
    }
