"""Rutas del motor físico. La ecuación no vive aquí."""

import logging

from fastapi import APIRouter, HTTPException

from app.physics.charts import build_charts
from app.physics.constants import PHYSICS_MODEL, PHYSICS_MODE
from app.physics.experiments import constants_payload
from app.physics.hydraulics import PhysicsInputError, compare_fluids, run_hydraulics
from app.physics.schema import CompareRequest, HydraulicsRequest

logger = logging.getLogger("esp.core")
router = APIRouter()


def _reject(exc: PhysicsInputError) -> None:
    logger.warning("Physics input rejected")
    raise HTTPException(
        status_code=422,
        detail={"error": "validation", "messages": exc.messages},
    ) from exc


@router.get("/physics/constants")
def physics_constants() -> dict:
    return constants_payload()


@router.post("/physics/hydraulics")
def physics_hydraulics(body: HydraulicsRequest) -> dict:
    logger.info("Physics calculation requested")
    try:
        result = run_hydraulics(body)
    except PhysicsInputError as exc:
        _reject(exc)
    logger.info("Input normalized")
    logger.info("Hydraulic calculation completed")
    for warning in result["warnings"]:
        logger.warning("Validation warning generated: %s", warning["code"])
    return result


@router.post("/physics/charts")
def physics_charts(body: HydraulicsRequest) -> dict:
    logger.info("Physics calculation requested")
    try:
        chart = build_charts(body)
    except PhysicsInputError as exc:
        _reject(exc)
    logger.info("Input normalized")
    logger.info("Hydraulic calculation completed")
    return chart


@router.post("/physics/compare")
def physics_compare(body: CompareRequest) -> dict:
    logger.info("Physics calculation requested")
    try:
        result = compare_fluids(body)
    except PhysicsInputError as exc:
        _reject(exc)
    logger.info("Input normalized")
    logger.info("Hydraulic calculation completed")
    return result


def physics_availability() -> dict:
    return {"enabled": True, "model": PHYSICS_MODEL, "mode": PHYSICS_MODE}
