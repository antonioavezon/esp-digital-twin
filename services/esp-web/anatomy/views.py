import json
import logging
import os
import re
from urllib.parse import quote, urlencode

from django.http import JsonResponse
from django.shortcuts import redirect, render

from anatomy.client import EspCoreClient, EspCoreError
from anatomy.i18n import localize_esp, text_for
from anatomy.preferences import LANGS, LANG_COOKIE, THEMES, THEME_COOKIE, language_of
from anatomy.project_metadata import (
    DEVELOPMENT_STAGE,
    FOUNDATION_STAGE,
    PHYSICS_MODE,
    PHYSICS_MODEL,
    PROJECT_PHASE,
    stage_label_for,
)

logger = logging.getLogger("esp.web")


def index(request):
    esp = None
    error = None
    try:
        esp = EspCoreClient().get_esp()
    except EspCoreError as exc:
        error = text_for(request, "error_esp")
        logger.warning("%s", error)
        logger.warning("esp-core unavailable: %s", exc)

    esp = localize_esp(esp, language_of(request))
    components = []
    if esp:
        components = sorted(esp.get("components", []), key=lambda item: item.get("display_order", 0))
    return render(
        request,
        "anatomy/index.html",
        {
            "esp": esp,
            "components": components,
            "error": error,
            "empty_payload": None,
        },
    )


def pump(request):
    pump_payload = None
    error = None
    try:
        pump_payload = EspCoreClient().get_pump()
    except EspCoreError as exc:
        error = text_for(request, "error_pump")
        logger.warning("%s", error)
        logger.warning("esp-core unavailable: %s", exc)
    return render(
        request,
        "anatomy/pump.html",
        {
            "pump": pump_payload,
            "error": error,
            "empty_payload": None,
        },
    )


def about(request):
    runtime = {
        "stage": DEVELOPMENT_STAGE,
        "stage_label": stage_label_for(DEVELOPMENT_STAGE),
        "physics_model": PHYSICS_MODEL,
        "physics_mode": PHYSICS_MODE,
    }
    try:
        health = EspCoreClient().get_health()
    except EspCoreError as exc:
        logger.warning("esp-core unavailable for about: %s", exc)
        health = None
    if health:
        stage = health.get("stage") or runtime["stage"]
        runtime["stage"] = stage
        runtime["stage_label"] = stage_label_for(stage)
        physics = health.get("physics") or {}
        if physics.get("model"):
            runtime["physics_model"] = physics["model"]
        if physics.get("mode"):
            runtime["physics_mode"] = physics["mode"]
    return render(request, "anatomy/about.html", {"runtime": runtime})


def curves(request):
    return render(request, "anatomy/curves.html")


def physics(request):
    constants = None
    error = None
    try:
        constants = EspCoreClient().get_physics_constants()
    except EspCoreError as exc:
        error = text_for(request, "error_physics")
        logger.warning("%s", error)
        logger.warning("esp-core unavailable: %s", exc)
    return render(
        request,
        "anatomy/physics.html",
        {
            "constants": constants,
            "error": error,
            "empty_payload": None,
            "stage_choices": range(1, 121),
        },
    )


def _proxy_physics(request, path: str):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "detail": {
                    "error": "validation",
                    "messages": [{"field": "body", "message": "El cuerpo no es JSON."}],
                }
            },
            status=400,
        )
    if not isinstance(payload, dict):
        return JsonResponse(
            {
                "detail": {
                    "error": "validation",
                    "messages": [{"field": "body", "message": "Se esperaba un objeto JSON."}],
                }
            },
            status=400,
        )
    try:
        data, status = EspCoreClient().post_json(path, payload)
    except EspCoreError as exc:
        logger.warning("esp-core unavailable: %s", exc)
        return JsonResponse(
            {
                "detail": {
                    "error": "unavailable",
                    "messages": [{"field": "esp-core", "message": "No se pudo calcular en esp-core."}],
                }
            },
            status=503,
        )
    return JsonResponse(data, status=status)


def physics_hydraulics(request):
    return _proxy_physics(request, "/api/v1/physics/hydraulics")


def physics_charts(request):
    return _proxy_physics(request, "/api/v1/physics/charts")


def physics_compare(request):
    return _proxy_physics(request, "/api/v1/physics/compare")


def _proxy_get(path: str):
    try:
        data = EspCoreClient().get(path)
    except EspCoreError as exc:
        logger.warning("esp-core unavailable: %s", exc)
        return JsonResponse(
            {
                "detail": {
                    "error": "unavailable",
                    "messages": [{"field": "esp-core", "message": "No se pudo consultar esp-core."}],
                }
            },
            status=503,
        )
    return JsonResponse(data)


def physics_curves(request):
    return _proxy_get("/api/v1/physics/curves")


def physics_curve_detail(request, curve_id: str):
    query = request.META.get("QUERY_STRING", "")
    path = f"/api/v1/physics/curves/{curve_id}"
    if query:
        path = f"{path}?{query}"
    return _proxy_get(path)


def physics_curve_marker(request, curve_id: str):
    return _proxy_physics(request, f"/api/v1/physics/curves/{curve_id}/marker")


def config_page(request):
    if request.method == "POST":
        lang = request.POST.get("lang", "es")
        theme = request.POST.get("theme", "dark")
        if lang not in LANGS:
            lang = "es"
        if theme not in THEMES:
            theme = "dark"
        response = redirect("config")
        response.set_cookie(LANG_COOKIE, lang, max_age=60 * 60 * 24 * 365, samesite="Lax", path="/")
        response.set_cookie(THEME_COOKIE, theme, max_age=60 * 60 * 24 * 365, samesite="Lax", path="/")
        return response
    return render(request, "anatomy/config.html")


_DATASET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")
_INTAKE_ID = re.compile(r"^[a-f0-9]{32}$")
_NOTICE = {
    "no_files": "research_no_files",
    "file_too_large": "research_too_large",
    "core_unavailable": "research_unavailable",
    "unsupported_extension": "research_bad_extension",
    "empty_file": "research_empty_file",
    "content_mismatch": "research_mismatch",
    "corrupt_workbook": "research_corrupt",
    "invalid_json": "research_bad_json",
    "encoding_unknown": "research_bad_encoding",
    "duplicate_sha": "research_duplicate_short",
    "ingest_failed": "research_import_failed",
    "permission_denied": "research_permission",
    "disk_full": "research_disk",
    "invalid_filename": "research_bad_name",
}


def _upload_limit() -> int:
    try:
        megabytes = int(os.environ.get("ESP_DATA_MAX_UPLOAD_MB", "32"))
    except ValueError:
        megabytes = 32
    if megabytes < 1:
        megabytes = 32
    return megabytes * 1024 * 1024


def _status_label(request, status: str | None) -> str:
    labels = {
        "imported": "research_status_raw",
        "validated": "research_status_raw",
        "selected": "research_status_raw",
        "profiled": "research_status_profiled",
        "ready_for_mapping": "research_status_mapping",
        "error": "research_status_error",
    }
    return text_for(request, labels.get(status or "", "research_status_raw"))


def _catalog_rows(request, items: list[dict]) -> list[dict]:
    rows = []
    for item in items:
        formats = item.get("formats") or []
        if isinstance(formats, list):
            format_label = ", ".join(formats) if formats else "—"
        else:
            format_label = str(formats)
        rows.append(
            {
                "dataset_id": item.get("dataset_id"),
                "title": item.get("short_title") or item.get("title") or item.get("dataset_id"),
                "formats": format_label,
                "file_count": item.get("file_count") or 0,
                "status_label": _status_label(request, item.get("status")),
                "imported_at": item.get("imported_at") or "—",
            }
        )
    return rows


def research(request):
    core_down = False
    dataset = None
    preview = None
    preprocess = None
    catalog = []
    client = EspCoreClient()
    notice_code = request.GET.get("notice", "")
    notice = text_for(request, _NOTICE[notice_code]) if notice_code in _NOTICE else ""
    try:
        status = client.get("/api/v1/research/status")
    except EspCoreError as exc:
        logger.warning("research status unavailable: %s", exc)
        status = None
        core_down = True
    if not core_down:
        try:
            index = client.get("/api/v1/research/datasets")
            catalog = index.get("datasets") or []
        except EspCoreError as exc:
            logger.warning("research index unavailable: %s", exc)
            catalog = []
        requested = request.GET.get("dataset", "")
        if catalog:
            ids = [item.get("dataset_id") for item in catalog]
            dataset_id = requested if requested in ids else ids[0]
        else:
            dataset_id = requested or "001"
        if not _DATASET_ID.match(dataset_id or ""):
            dataset_id = ""
        if dataset_id:
            try:
                dataset = client.get(f"/api/v1/research/datasets/{dataset_id}")
            except EspCoreError as exc:
                logger.warning("research dataset unavailable: %s", exc)
                dataset = None
            if dataset is not None:
                try:
                    preprocess = client.get(f"/api/v1/research/datasets/{dataset_id}/preprocess")
                except EspCoreError:
                    preprocess = None
    selected = _research_selection(request, dataset)
    if dataset and not core_down and selected["file"] and selected["sheet"]:
        query = urlencode(
            {
                "file": selected["file"],
                "sheet": selected["sheet"],
                "block": selected["block"],
                "limit": 30,
            },
            quote_via=quote,
        )
        try:
            preview = client.get(
                f"/api/v1/research/datasets/{dataset['dataset_id']}/preview?{query}"
            )
        except EspCoreError as exc:
            logger.warning("research preview unavailable: %s", exc)
            preview = None
    rows = _catalog_rows(request, catalog)
    if not rows and dataset:
        rows = _catalog_rows(
            request,
            [
                {
                    "dataset_id": dataset.get("dataset_id"),
                    "short_title": dataset.get("short_title") or dataset.get("title"),
                    "formats": ["xlsx"],
                    "file_count": len(dataset.get("files") or []),
                    "status": dataset.get("status") or "imported",
                    "imported_at": dataset.get("imported_at"),
                }
            ],
        )
    preprocess_text = ""
    if preprocess and request.GET.get("view") == "preprocess":
        preprocess_text = json.dumps(preprocess, indent=2, ensure_ascii=False)
    return render(
        request,
        "anatomy/research.html",
        {
            "research_unavailable": core_down,
            "dataset": dataset,
            "preview": preview,
            "selected": selected,
            "catalog": rows,
            "preprocess": preprocess,
            "preprocess_text": preprocess_text,
            "import_notice": notice,
            "show_preprocess": request.GET.get("view") == "preprocess",
        },
    )


def research_analyze(request):
    if request.method != "POST":
        return redirect("research")
    uploads = request.FILES.getlist("files")
    if not uploads:
        return redirect("/research/?notice=no_files")
    limit = _upload_limit()
    total = 0
    blobs = []
    for upload in uploads:
        data = upload.read()
        total += len(data)
        if len(data) > limit or total > limit:
            return redirect("/research/?notice=file_too_large")
        blobs.append((upload.name, data, upload.content_type or "application/octet-stream"))
    try:
        body, code = EspCoreClient(timeout=120).post_files("/api/v1/research/intake", blobs)
    except EspCoreError as exc:
        logger.warning("research intake failed: %s", exc)
        return redirect("/research/?notice=core_unavailable")
    if code >= 400 or "intake_id" not in body:
        notice = body.get("error", "ingest_failed")
        if notice not in _NOTICE:
            notice = "ingest_failed"
        return redirect(f"/research/?notice={notice}")
    return redirect(f"/research/review/{body['intake_id']}/")


def research_review(request, intake_id: str):
    if not _INTAKE_ID.match(intake_id):
        return redirect("/research/?notice=ingest_failed")
    try:
        intake = EspCoreClient(timeout=30).get(f"/api/v1/research/intake/{intake_id}")
    except EspCoreError as exc:
        logger.warning("research review unavailable: %s", exc)
        return redirect("/research/?notice=core_unavailable")
    if intake.get("error"):
        return redirect("/research/?notice=ingest_failed")
    blocked = any(item.get("status") == "error" for item in intake.get("files", []))
    duplicates = []
    for item in intake.get("files", []):
        for found in item.get("duplicates") or []:
            duplicates.append(
                {
                    "filename": item.get("original_filename"),
                    "dataset_id": found.get("dataset_id"),
                    "message": text_for(request, "research_duplicate").replace(
                        "{dataset}", str(found.get("dataset_id"))
                    ),
                }
            )
    return render(
        request,
        "anatomy/research_review.html",
        {
            "intake": intake,
            "blocked": blocked,
            "duplicates": duplicates,
        },
    )


def research_import(request, intake_id: str):
    if request.method != "POST" or not _INTAKE_ID.match(intake_id):
        return redirect("research")
    payload = {
        "intake_id": intake_id,
        "title": request.POST.get("title") or None,
        "author": request.POST.get("author") or None,
        "organization": request.POST.get("organization") or None,
        "url": request.POST.get("url") or None,
        "doi": request.POST.get("doi") or None,
        "article_doi": request.POST.get("article_doi") or None,
        "license": request.POST.get("license") or None,
        "notes": request.POST.get("notes") or None,
        "acknowledge_duplicates": request.POST.get("acknowledge_duplicates") == "yes",
    }
    try:
        body, code = EspCoreClient(timeout=120).post_json("/api/v1/research/datasets/import", payload)
    except EspCoreError as exc:
        logger.warning("research import failed: %s", exc)
        return redirect("/research/?notice=core_unavailable")
    if code == 409:
        return redirect(f"/research/review/{intake_id}/?notice=duplicate_sha")
    if code >= 400 or "dataset_id" not in body:
        notice = body.get("error", "ingest_failed")
        if notice not in _NOTICE:
            notice = "ingest_failed"
        return redirect(f"/research/?notice={notice}")
    return redirect(f"/research/?dataset={body['dataset_id']}")


def research_cancel(request, intake_id: str):
    if request.method != "POST" or not _INTAKE_ID.match(intake_id):
        return redirect("research")
    try:
        EspCoreClient(timeout=30).post_json(f"/api/v1/research/intake/{intake_id}/cancel", {})
    except EspCoreError as exc:
        logger.warning("research cancel failed: %s", exc)
    return redirect("research")


def research_reprofile(request, dataset_id: str):
    if request.method != "POST" or not _DATASET_ID.match(dataset_id):
        return redirect("research")
    try:
        body, code = EspCoreClient(timeout=120).post_json(
            f"/api/v1/research/datasets/{dataset_id}/reprofile",
            {},
        )
    except EspCoreError as exc:
        logger.warning("research reprofile failed: %s", exc)
        return redirect("/research/?notice=core_unavailable")
    if code >= 400:
        return redirect(f"/research/?dataset={dataset_id}&notice=ingest_failed")
    return redirect(f"/research/?dataset={dataset_id}&view=preprocess")


def _research_selection(request, dataset):
    selected = {"file": "", "sheet": "", "block": 1, "block_count": 1, "files": []}
    if not dataset:
        return selected
    files = [item for item in dataset.get("files", []) if item.get("sheets")]
    selected["files"] = files
    names = [item["filename"] for item in files]
    chosen_name = request.GET.get("file", "")
    if chosen_name not in names and names:
        chosen_name = names[0]
    chosen = next((item for item in files if item["filename"] == chosen_name), None)
    sheets = [sheet["name"] for sheet in (chosen or {}).get("sheets", [])]
    sheet_name = request.GET.get("sheet", "")
    if sheet_name not in sheets and sheets:
        sheet_name = sheets[0]
    sheet = next((item for item in (chosen or {}).get("sheets", []) if item["name"] == sheet_name), None)
    block_count = int((sheet or {}).get("block_count") or 1)
    try:
        block = int(request.GET.get("block", "1"))
    except ValueError:
        block = 1
    if block < 1 or block > block_count:
        block = 1
    selected.update(
        {
            "file": chosen_name,
            "sheet": sheet_name,
            "block": block,
            "block_count": block_count,
            "block_options": list(range(1, block_count + 1)),
            "sheet_names": sheets,
        }
    )
    return selected


def health(request):
    try:
        core = EspCoreClient().get_health()
    except EspCoreError:
        return JsonResponse(
            {
                "service": "esp-web",
                "status": "degraded",
                "stage": DEVELOPMENT_STAGE,
                "phase": PROJECT_PHASE,
                "foundation_stage": FOUNDATION_STAGE,
                "esp_core": "unreachable",
            },
            status=503,
        )
    core_ok = core.get("status") == "healthy"
    return JsonResponse(
        {
            "service": "esp-web",
            "status": "healthy" if core_ok else "degraded",
            "stage": core.get("stage", DEVELOPMENT_STAGE),
            "phase": core.get("phase", PROJECT_PHASE),
            "foundation_stage": core.get("foundation_stage", FOUNDATION_STAGE),
            "esp_core": core.get("status", "unknown"),
            "physics": core.get("physics"),
        },
        status=200 if core_ok else 503,
    )
