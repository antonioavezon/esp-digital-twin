"""Catálogo canónico de variables físicas de la ESP.

No depende de un dataset. No convierte unidades ni calcula magnitudes.
La ubicación describe dónde se define la variable, no dónde cayó una columna.
"""

from __future__ import annotations

STATUSES = (
    "unmapped",
    "candidate",
    "reviewed",
    "validated",
    "rejected",
    "not_applicable",
)

CONFIDENCE = ("high", "medium", "low")

EVIDENCE_TYPES = (
    "explicit_header",
    "explicit_unit",
    "dataset_documentation",
    "article",
    "figure",
    "table",
    "manual_research_review",
    "derived_relationship",
)

LOCATIONS = (
    "pump_intake",
    "pump_discharge",
    "downhole",
    "surface",
    "pump",
    "test_loop",
    "unknown",
)

FAMILIES = (
    "pressure",
    "flow",
    "fraction",
    "head",
    "power",
    "rotational_speed",
    "frequency",
    "density",
    "temperature",
    "length",
)

# Relaciones posibles. calculation_status permanece not_executed en 2-1.
DERIVABLE_RELATIONS = (
    {
        "id": "gvf_from_phase_rates",
        "output": "gas_volume_fraction",
        "equation": "GVF = Q_G / (Q_G + Q_L)",
        "requires": ("gas_flow_rate", "liquid_flow_rate"),
        "conditions": (
            "Q_G y Q_L deben ser caudales volumétricos de las mismas condiciones "
            "y el denominador no puede ser cero."
        ),
        "calculation_status": "not_executed",
    },
    {
        "id": "head_from_pressure_and_density",
        "output": "pump_head",
        "equation": "H = ΔP / (ρ g)",
        "requires": ("pump_pressure_difference", "liquid_density"),
        "conditions": (
            "ΔP tiene que estar definido entre dos puntos identificados "
            "y la densidad tiene que corresponder a ese tramo."
        ),
        "calculation_status": "not_executed",
    },
    {
        "id": "hydraulic_power_from_flow_and_pressure",
        "output": "hydraulic_power",
        "equation": "P_hyd = Q ΔP",
        "requires": ("liquid_flow_rate", "pump_pressure_difference"),
        "conditions": (
            "Q y ΔP tienen que referirse al mismo tramo. "
            "No sustituye a la potencia de eje ni a la potencia eléctrica."
        ),
        "calculation_status": "not_executed",
    },
    {
        "id": "hydraulic_power_from_head",
        "output": "hydraulic_power",
        "equation": "P_hyd = ρ g Q H",
        "requires": ("liquid_density", "liquid_flow_rate", "pump_head"),
        "conditions": "Q, H y ρ tienen que estar definidos para el mismo fluido y tramo.",
        "calculation_status": "not_executed",
    },
)


def _variable(
    variable_id: str,
    symbol: str,
    description: str,
    quantity: str,
    family: str,
    si_unit: str,
    location: str,
    display_unit: str | None = None,
    expected_range: str | None = None,
) -> dict:
    return {
        "id": variable_id,
        "symbol": symbol,
        "description": description,
        "quantity": quantity,
        "family": family,
        "si_unit": si_unit,
        "display_unit": display_unit,
        "location": location,
        "expected_range": expected_range,
    }


CANONICAL_VARIABLES = (
    _variable(
        "intake_pressure",
        "P_int",
        "Presión del fluido en la admisión de la bomba.",
        "pressure",
        "pressure",
        "Pa",
        "pump_intake",
    ),
    _variable(
        "flowing_bottomhole_pressure",
        "P_wf",
        "Presión de fondo fluyente del pozo.",
        "pressure",
        "pressure",
        "Pa",
        "downhole",
    ),
    _variable(
        "liquid_flow_rate",
        "Q_L",
        "Caudal volumétrico de la fase líquida.",
        "volumetric_flow_rate",
        "flow",
        "m3/s",
        "unknown",
    ),
    _variable(
        "gas_flow_rate",
        "Q_G",
        "Caudal volumétrico de la fase gaseosa.",
        "volumetric_flow_rate",
        "flow",
        "m3/s",
        "unknown",
    ),
    _variable(
        "dynamic_fluid_level",
        "h_D",
        "Nivel dinámico del fluido durante producción.",
        "length",
        "length",
        "m",
        "downhole",
    ),
    _variable(
        "gas_volume_fraction",
        "GVF",
        "Fracción volumétrica de gas.",
        "dimensionless_fraction",
        "fraction",
        "1",
        "unknown",
        expected_range="0–1",
    ),
    _variable(
        "pump_head",
        "H",
        "Energía transferida por unidad de peso, escrita como altura equivalente.",
        "head",
        "head",
        "m",
        "pump",
    ),
    _variable(
        "pump_pressure_difference",
        "ΔP",
        "Diferencia de presión entre dos puntos identificados alrededor de la bomba o de la sección considerada.",
        "pressure",
        "pressure",
        "Pa",
        "pump",
    ),
    _variable(
        "hydraulic_power",
        "P_hyd",
        "Potencia hidráulica transferida al fluido.",
        "power",
        "power",
        "W",
        "pump",
    ),
    _variable(
        "shaft_power",
        "P_shaft",
        "Potencia mecánica entregada al eje de la bomba.",
        "power",
        "power",
        "W",
        "pump",
    ),
    _variable(
        "electrical_power",
        "P_el",
        "Potencia eléctrica asociada al sistema.",
        "power",
        "power",
        "W",
        "unknown",
    ),
    _variable(
        "rotary_speed",
        "N",
        "Velocidad de rotación de la bomba.",
        "rotational_speed",
        "rotational_speed",
        "rad/s",
        "pump",
        display_unit="rpm",
    ),
    _variable(
        "frequency",
        "f",
        "Frecuencia eléctrica o de giro, según la definición que aporte la evidencia.",
        "frequency",
        "frequency",
        "Hz",
        "unknown",
    ),
    _variable(
        "liquid_density",
        "ρ_L",
        "Densidad de la fase líquida.",
        "density",
        "density",
        "kg/m3",
        "unknown",
    ),
)

_BY_ID = {item["id"]: item for item in CANONICAL_VARIABLES}


def canonical_catalog() -> list[dict]:
    return [dict(item) for item in CANONICAL_VARIABLES]


def canonical_by_id(variable_id: str) -> dict | None:
    found = _BY_ID.get(variable_id)
    return dict(found) if found else None


def expected_variable_ids() -> tuple[str, ...]:
    return tuple(item["id"] for item in CANONICAL_VARIABLES)
