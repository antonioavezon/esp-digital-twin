import json
import logging

from django.http import JsonResponse
from django.shortcuts import redirect, render

from anatomy.client import EspCoreClient, EspCoreError
from anatomy.i18n import localize_esp, text_for
from anatomy.preferences import LANGS, LANG_COOKIE, THEMES, THEME_COOKIE, language_of
from anatomy.project_metadata import PHYSICS_MODE, PHYSICS_MODEL, DEVELOPMENT_STAGE, stage_label_for

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


def health(request):
    try:
        core = EspCoreClient().get_health()
    except EspCoreError:
        return JsonResponse(
            {
                "service": "esp-web",
                "status": "degraded",
                "stage": "1C",
                "esp_core": "unreachable",
            },
            status=503,
        )
    core_ok = core.get("status") == "healthy"
    return JsonResponse(
        {
            "service": "esp-web",
            "status": "healthy" if core_ok else "degraded",
            "stage": core.get("stage", "1C"),
            "esp_core": core.get("status", "unknown"),
            "physics": core.get("physics"),
        },
        status=200 if core_ok else 503,
    )
