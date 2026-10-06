"""Endpoints de investigación. La etapa 2-1 agrega el mapeo de variables. Sin modelos de IA."""

import logging

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.research.datasets import (
    DatasetUnavailable,
    UnknownBlock,
    UnknownDataset,
    UnknownFile,
    UnknownSheet,
    dataset_detail,
    dataset_preview,
    dataset_profile,
    list_datasets,
    research_status,
)
from app.research.ingest import (
    IngestError,
    cancel_intake,
    commit_intake,
    create_intake,
    read_intake,
    reprofile,
    stored_manifest,
    stored_preprocess,
)
from app.research.profiling import WorkbookError
from app.research.mapping import (
    MappingError,
    annotate_mapping,
    coverage_of,
    ensure_mapping,
    save_decision,
)
from app.research.results import load_stage_results
from app.research.variables import canonical_catalog

logger = logging.getLogger("esp.research")

router = APIRouter(prefix="/research", tags=["research"])


def _error(status_code: int, code: str, **extra):
    return JSONResponse(status_code=status_code, content={"error": code, **extra})


def _ingest(action):
    try:
        return action()
    except IngestError as exc:
        return _error(exc.status, exc.code, **exc.details)
    except Exception:
        logger.exception("research ingest failed")
        return _error(422, "ingest_failed")


class ImportRequest(BaseModel):
    intake_id: str
    title: str | None = None
    author: str | None = None
    organization: str | None = None
    url: str | None = None
    doi: str | None = None
    article_doi: str | None = None
    license: str | None = None
    notes: str | None = None
    type: str | None = None
    acknowledge_duplicates: bool = False


@router.get("/status")
def status():
    return research_status()


@router.get("/datasets")
def datasets():
    return list_datasets()


@router.post("/intake")
async def intake(files: list[UploadFile] = File(default=[])):
    blobs = []
    for upload in files:
        blobs.append((upload.filename or "", await upload.read()))
    return _ingest(lambda: create_intake(blobs))


@router.get("/intake/{intake_id}")
def intake_detail(intake_id: str):
    return _ingest(lambda: read_intake(intake_id))


@router.post("/intake/{intake_id}/cancel")
def intake_cancel(intake_id: str):
    return _ingest(lambda: cancel_intake(intake_id))


@router.post("/datasets/import")
def import_dataset(body: ImportRequest):
    provenance = body.model_dump(exclude={"intake_id", "acknowledge_duplicates"})
    return _ingest(lambda: commit_intake(body.intake_id, provenance, body.acknowledge_duplicates))


@router.get("/datasets/{dataset_id}")
def dataset(dataset_id: str):
    try:
        return dataset_detail(dataset_id)
    except UnknownDataset:
        return _error(404, "unknown_dataset", dataset_id=dataset_id)
    except DatasetUnavailable:
        return _error(404, "dataset_unavailable", dataset_id=dataset_id)


@router.get("/datasets/{dataset_id}/manifest")
def manifest(dataset_id: str):
    try:
        dataset_detail(dataset_id)
    except UnknownDataset:
        return _error(404, "unknown_dataset", dataset_id=dataset_id)
    except DatasetUnavailable:
        return _error(404, "dataset_unavailable", dataset_id=dataset_id)
    return _ingest(lambda: stored_manifest(dataset_id))


@router.get("/datasets/{dataset_id}/preprocess")
def preprocess(dataset_id: str):
    try:
        dataset_detail(dataset_id)
    except UnknownDataset:
        return _error(404, "unknown_dataset", dataset_id=dataset_id)
    except DatasetUnavailable:
        return _error(404, "dataset_unavailable", dataset_id=dataset_id)
    return _ingest(lambda: stored_preprocess(dataset_id))


@router.post("/datasets/{dataset_id}/reprofile")
def reprofile_dataset(dataset_id: str):
    try:
        dataset_detail(dataset_id)
    except UnknownDataset:
        return _error(404, "unknown_dataset", dataset_id=dataset_id)
    except DatasetUnavailable:
        return _error(404, "dataset_unavailable", dataset_id=dataset_id)
    return _ingest(lambda: reprofile(dataset_id))


class MappingDecision(BaseModel):
    signature_id: str | None = None
    canonical_id: str | None = None
    status: str
    confidence: str | None = None
    quantity_family: str | None = None
    location: str = "unknown"
    evidence: list[dict] = []
    notes: str | None = None


def _mapping_call(action):
    try:
        return action()
    except MappingError as exc:
        return _error(exc.status, exc.code, **exc.details)
    except IngestError as exc:
        return _error(exc.status, exc.code, **exc.details)
    except Exception:
        logger.exception("research mapping failed")
        return _error(422, "mapping_failed")


@router.get("/variables")
def variables():
    return {"variables": canonical_catalog()}


@router.get("/datasets/{dataset_id}/mapping/coverage")
def mapping_coverage(dataset_id: str):
    def read():
        document = annotate_mapping(ensure_mapping(dataset_id))
        return document.get("coverage") or coverage_of(document)

    return _mapping_call(read)


@router.get("/datasets/{dataset_id}/mapping")
def mapping_document(dataset_id: str):
    return _mapping_call(lambda: annotate_mapping(ensure_mapping(dataset_id)))


@router.get("/datasets/{dataset_id}/stage-2-1-results")
def stage_results(dataset_id: str):
    def read():
        try:
            return load_stage_results(dataset_id)
        except FileNotFoundError:
            raise MappingError("results_missing", 404, dataset_id=dataset_id) from None

    return _mapping_call(read)


@router.post("/datasets/{dataset_id}/mapping")
def mapping_save(dataset_id: str, body: MappingDecision):
    return _mapping_call(lambda: save_decision(dataset_id, body.model_dump()))


@router.patch("/datasets/{dataset_id}/mapping/{mapping_id}")
def mapping_revise(dataset_id: str, mapping_id: str, body: MappingDecision):
    return _mapping_call(
        lambda: save_decision(dataset_id, body.model_dump(), mapping_id=mapping_id)
    )


@router.get("/datasets/{dataset_id}/profile")
def profile(dataset_id: str):
    try:
        return dataset_profile(dataset_id)
    except UnknownDataset:
        return _error(404, "unknown_dataset", dataset_id=dataset_id)
    except DatasetUnavailable:
        return _error(404, "dataset_unavailable", dataset_id=dataset_id)
    except WorkbookError as exc:
        return _error(422, "unreadable_workbook", filename=exc.filename)


@router.get("/datasets/{dataset_id}/preview")
def preview(
    dataset_id: str,
    file: str = Query(...),
    sheet: str = Query(...),
    limit: int = Query(30, ge=1, le=50),
    block: int = Query(1, ge=1),
):
    try:
        return dataset_preview(dataset_id, file, sheet, limit, block)
    except UnknownDataset:
        return _error(404, "unknown_dataset", dataset_id=dataset_id)
    except DatasetUnavailable:
        return _error(404, "dataset_unavailable", dataset_id=dataset_id)
    except UnknownFile:
        return _error(404, "unknown_file", filename=file)
    except UnknownSheet:
        return _error(404, "unknown_sheet", sheet=sheet)
    except UnknownBlock:
        return _error(404, "unknown_block", block=block)
    except WorkbookError as exc:
        return _error(422, "unreadable_workbook", filename=exc.filename)
