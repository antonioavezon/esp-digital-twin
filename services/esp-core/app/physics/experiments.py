"""Tres casos educativos y la comparación de fluidos.

No son datos de placa de una ESP comercial.
"""

from app.physics.constants import (
    DEFAULT_DENSITY_KG_M3,
    PHYSICS_MODEL,
    RESERVED_SOURCES,
    STANDARD_GRAVITY_M_S2,
    STATUS,
    VARIABLE_SOURCES,
)
from app.physics.units import DENSITY_UNITS, FLOW_UNITS, PRESSURE_UNITS, gravity_display


def _case(intake: float, discharge: float, density: float, flow: float) -> dict:
    return {
        "intake_pressure": {"value": intake, "unit": "psi"},
        "discharge_pressure": {"value": discharge, "unit": "psi"},
        "density": {"value": density, "unit": "kg/m3"},
        "flow_rate": {"value": flow, "unit": "m3/day"},
    }


def experiments() -> list[dict]:
    base_density = DEFAULT_DENSITY_KG_M3
    lighter = 850.0
    return [
        {
            "id": "base-water",
            "name": "Experiment 1 — Base",
            "objective": "Caso simple con densidad de agua. Sirve de referencia.",
            "disclaimer": "Caso educativo. No es la especificación de una ESP comercial.",
            "request": _case(100, 300, base_density, 500),
        },
        {
            "id": "higher-differential",
            "name": "Experiment 2 — Higher Differential Pressure",
            "objective": "Misma densidad y mismo caudal. Mayor ΔP: observar head y potencia hidráulica.",
            "disclaimer": "Caso educativo. No es la especificación de una ESP comercial.",
            "request": _case(100, 500, base_density, 500),
        },
        {
            "id": "different-density",
            "name": "Experiment 3 — Different Fluid Density",
            "objective": "Mismas presiones y mismo caudal que el caso base. Otra densidad: el head cambia.",
            "disclaimer": "Caso educativo. No es la especificación de una ESP comercial.",
            "request": _case(100, 300, lighter, 500),
        },
    ]


def compare_template() -> dict:
    base = experiments()[0]["request"]
    return {
        "id": "compare-fluids",
        "name": "Compare Fluids",
        "objective": "Mismo ΔP, dos densidades. La presión diferencial no cambia; el head sí.",
        "disclaimer": "Caso educativo. No es la especificación de una ESP comercial.",
        "intake_pressure": base["intake_pressure"],
        "discharge_pressure": base["discharge_pressure"],
        "flow_rate": base["flow_rate"],
        "fluids": [
            {"name": "Fluid A", "density": {"value": DEFAULT_DENSITY_KG_M3, "unit": "kg/m3"}},
            {"name": "Fluid B", "density": {"value": 850.0, "unit": "kg/m3"}},
        ],
    }


def constants_payload() -> dict:
    return {
        "physics_model": PHYSICS_MODEL,
        "mode": "static",
        "status": STATUS,
        "gravity": {
            "value": STANDARD_GRAVITY_M_S2,
            "unit": "m/s²",
            "display": gravity_display(),
            "source": "constant",
            "role": "constant",
        },
        "default_density": {
            "value": DEFAULT_DENSITY_KG_M3,
            "unit": "kg/m3",
            "source": "constant",
            "role": "constant",
            "note": "Valor sugerido para agua educativa. El cálculo usa la densidad que envíe el experimento.",
        },
        "units": {
            "pressure": list(PRESSURE_UNITS),
            "flow": list(FLOW_UNITS),
            "density": list(DENSITY_UNITS),
        },
        "variable_sources": list(VARIABLE_SOURCES),
        "reserved_sources": list(RESERVED_SOURCES),
        "experiments": experiments(),
        "compare_fluids": compare_template(),
    }
