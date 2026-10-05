"""Rutas del catálogo de curvas. La hidráulica del laboratorio no se recalcula aquí."""

import logging

from fastapi import APIRouter, HTTPException

from app.curves.catalog import curve_by_id, index_payload
from app.curves.evaluate import CurveRequestError, lab_comparison, present_curve
from app.curves.schema import MarkerRequest

logger = logging.getLogger("esp.core")
router = APIRouter()


def _reject(exc: CurveRequestError) -> None:
    raise HTTPException(
        status_code=422,
        detail={"error": "validation", "messages": exc.messages},
    ) from exc


def _require(curve_id: str) -> dict:
    curve = curve_by_id(curve_id)
    if curve is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "messages": []})
    return curve


@router.get("/physics/curves")
def physics_curves() -> dict:
    return index_payload()


@router.get("/physics/curves/{curve_id}")
def physics_curve_detail(
    curve_id: str,
    stages: int | None = None,
    flow_unit: str = "bpd",
    head_unit: str = "ft",
    power_unit: str = "hp",
) -> dict:
    curve = _require(curve_id)
    logger.info("Curve requested id=%s stages=%s", curve["id"], stages)
    logger.info(
        "Curve conditions model=%s series=%s %s Hz %s rpm",
        curve["model"],
        curve["series"],
        curve["frequency_hz"],
        curve["speed_rpm"],
    )
    if curve["data_quality"] != "published":
        logger.warning("Approximate curve page=%s", curve["source_page"])
    try:
        return present_curve(
            curve,
            stages=stages,
            flow_unit=flow_unit,
            head_unit=head_unit,
            power_unit=power_unit,
        )
    except CurveRequestError as exc:
        _reject(exc)


@router.post("/physics/curves/{curve_id}/marker")
def physics_curve_marker(curve_id: str, body: MarkerRequest) -> dict:
    curve = _require(curve_id)
    logger.info("Curve requested id=%s stages=%s", curve["id"], body.stages)
    logger.info(
        "Physics Lab point associated flow_m3_s=%s head_m=%s",
        body.lab.flow_m3_s,
        body.lab.head_m,
    )
    try:
        result = lab_comparison(
            curve,
            stages=body.stages,
            flow_unit=body.flow_unit,
            head_unit=body.head_unit,
            power_unit=body.power_unit,
            flow_m3_s=body.lab.flow_m3_s,
            head_m=body.lab.head_m,
            hydraulic_power_w=body.lab.hydraulic_power_w,
            density_kg_m3=body.lab.density_kg_m3,
        )
    except CurveRequestError as exc:
        _reject(exc)
    for warning in result["warnings"]:
        logger.warning("Curve warning %s", warning["code"])
    logger.info("Curve comparison completed id=%s", curve["id"])
    return result
