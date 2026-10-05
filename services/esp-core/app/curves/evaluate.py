"""Presentación, escalado e interpolación de una curva ya cargada.

Las conversiones viven en units.py. Aquí no se inventan puntos fuera del rango.
"""

from app.curves.catalog import CURVE_MODEL
from app.physics.units import (
    UnitError,
    canonical_unit,
    from_cubic_metres_per_second,
    from_metres,
    from_watts,
    to_cubic_metres_per_second,
)


class CurveRequestError(Exception):
    def __init__(self, messages: list[dict[str, str]]):
        self.messages = messages
        super().__init__(messages[0]["message"] if messages else "solicitud inválida")


def _fail(field: str, message: str) -> None:
    raise CurveRequestError([{"field": field, "message": message}])


def interpolate(points: list[dict], flow_m3_s: float) -> float | None:
    """Interpolación lineal. None si el caudal queda fuera del tramo publicado."""
    if len(points) < 2:
        return None
    ordered = points
    first = ordered[0]["flow_m3_s"]
    last = ordered[-1]["flow_m3_s"]
    if flow_m3_s < first or flow_m3_s > last:
        return None
    for left, right in zip(ordered, ordered[1:]):
        span = right["flow_m3_s"] - left["flow_m3_s"]
        if left["flow_m3_s"] <= flow_m3_s <= right["flow_m3_s"] and span != 0:
            weight = (flow_m3_s - left["flow_m3_s"]) / span
            return left["value_si"] + weight * (right["value_si"] - left["value_si"])
    return ordered[-1]["value_si"]


def _display_flow(flow_m3_s: float, unit: str) -> float:
    try:
        return from_cubic_metres_per_second(flow_m3_s, unit)
    except UnitError as exc:
        _fail("flow_unit", f"Unidad de caudal desconocida: {exc.unit}.")


def _display_head(head_m: float, unit: str) -> float:
    try:
        return from_metres(head_m, unit)
    except UnitError as exc:
        _fail("head_unit", f"Unidad de head desconocida: {exc.unit}. Use m o ft.")


def _display_power(power_w: float, unit: str) -> float:
    try:
        return from_watts(power_w, unit)
    except UnitError as exc:
        _fail("power_unit", f"Unidad de potencia desconocida: {exc.unit}. Use hp o kW.")


def _series(points: list[dict], flow_unit: str, convert, multiplier: float) -> list[dict]:
    plotted = []
    for point in points:
        plotted.append(
            {
                "flow": _display_flow(point["flow_m3_s"], flow_unit),
                "value": convert(point["value_si"] * multiplier),
            }
        )
    return plotted


def present_curve(
    curve: dict,
    *,
    stages: int | None,
    flow_unit: str,
    head_unit: str,
    power_unit: str,
) -> dict:
    if stages is not None and stages < 1:
        _fail("stages", "El número de etapas tiene que ser un entero mayor o igual que 1.")
    per_stage = curve["curve_basis"] == "per_stage"
    if stages is None or not per_stage:
        multiplier = 1
        basis = {"code": "per_stage" if per_stage else "as_published", "stages": None}
    else:
        multiplier = stages
        basis = {
            "code": "per_stage" if stages == 1 else "total_estimate",
            "stages": stages,
        }
    flow_key = canonical_unit(flow_unit)
    head_key = canonical_unit(head_unit)
    power_key = canonical_unit(power_unit)
    head = _series(curve["head_flow_points"], flow_key, lambda value: _display_head(value, head_key), multiplier)
    power = _series(
        curve["shaft_power_flow_points"],
        flow_key,
        lambda value: _display_power(value, power_key),
        multiplier,
    )
    efficiency = _series(
        curve["efficiency_flow_points"],
        flow_key,
        lambda value: value * 100.0,
        1.0,
    )
    bep = None
    if curve.get("bep"):
        raw = curve["bep"]
        bep = {
            "origin": raw["origin"],
            "flow": _display_flow(raw["flow_m3_s"], flow_key),
            "head": _display_head(raw["head_m"] * multiplier, head_key),
            "shaft_power": _display_power(raw["power_w"] * multiplier, power_key),
            "efficiency_percent": raw["efficiency_percent"],
        }
    operating = _operating_range(curve, flow_key)
    warnings = []
    if curve["data_quality"] == "approximate_digitization":
        warnings.append(
            {
                "code": "approximate_digitization",
                "message": curve["digitization"]["warning"],
            }
        )
    if per_stage and stages is None:
        warnings.append(
            {
                "code": "per_stage_without_count",
                "message": (
                    "La ficha es por etapa. Sin un número de etapas no se compara "
                    "el head total del laboratorio con esta curva."
                ),
            }
        )
    return {
        "model": CURVE_MODEL,
        "id": curve["id"],
        "manufacturer": curve["manufacturer"],
        "series": curve["series"],
        "pump_model": curve["model"],
        "frequency_hz": curve["frequency_hz"],
        "speed_rpm": curve["speed_rpm"],
        "stage_count_reference": curve["stage_count_reference"],
        "specific_gravity_reference": curve["specific_gravity_reference"],
        "curve_basis": curve["curve_basis"],
        "basis": basis,
        "display_units": {
            "flow": flow_key,
            "head": head_key,
            "power": "kW" if power_key == "kw" else power_key,
            "efficiency": "%",
        },
        "source": {
            "document": curve["source_document"],
            "page": curve["source_page"],
            "revision": curve["source_revision"],
            "method": curve["source_method"],
            "quality": curve["data_quality"],
            "url": curve.get("source_url"),
            "digitization": curve.get("digitization"),
        },
        "series": {"head": head, "shaft_power": power, "efficiency": efficiency},
        "bep": bep,
        "operating_range": operating,
        "warnings": warnings,
    }


def _operating_range(curve: dict, flow_unit: str) -> dict | None:
    raw_range = curve.get("operating_range")
    if not raw_range:
        return None
    return {
        "name": raw_range["name"],
        "flow_min": _display_flow(to_cubic_metres_per_second(raw_range["flow_min_bpd"], "bpd"), flow_unit),
        "flow_max": _display_flow(to_cubic_metres_per_second(raw_range["flow_max_bpd"], "bpd"), flow_unit),
    }


def lab_comparison(
    curve: dict,
    *,
    stages: int | None,
    flow_unit: str,
    head_unit: str,
    power_unit: str,
    flow_m3_s: float,
    head_m: float,
    hydraulic_power_w: float,
    density_kg_m3: float,
) -> dict:
    presented = present_curve(
        curve,
        stages=stages,
        flow_unit=flow_unit,
        head_unit=head_unit,
        power_unit=power_unit,
    )
    warnings = list(presented["warnings"])
    per_stage = curve["curve_basis"] == "per_stage"
    comparable = not (per_stage and stages is None)
    flow_key = presented["display_units"]["flow"]
    head_key = canonical_unit(head_unit)
    power_key = canonical_unit(power_unit)
    marker = {
        "name": "Physics Lab calculated point",
        "comparable": comparable,
        "flow": _display_flow(flow_m3_s, flow_key) if comparable else None,
        "head": _display_head(head_m, head_key) if comparable else None,
        "hydraulic_power": _display_power(hydraulic_power_w, power_key),
        "shaft_power_from_curve": None,
        "shaft_power_estimate": None,
        "efficiency_percent": None,
    }
    if not comparable:
        return {**presented, "marker": marker, "warnings": warnings}

    head_si = interpolate(curve["head_flow_points"], flow_m3_s)
    power_si = interpolate(curve["shaft_power_flow_points"], flow_m3_s)
    eta = interpolate(curve["efficiency_flow_points"], flow_m3_s)
    multiplier = stages if stages else 1
    outside = head_si is None or power_si is None or eta is None
    if outside:
        warnings.append(
            {
                "code": "outside_flow_range",
                "message": "El caudal del laboratorio queda fuera del tramo digitalizado. No se extrapola.",
            }
        )
    else:
        marker["shaft_power_from_curve"] = _display_power(power_si * multiplier, power_key)
        marker["efficiency_percent"] = eta * 100.0
        if eta <= 0:
            warnings.append(
                {
                    "code": "efficiency_unavailable",
                    "message": "La eficiencia interpolada no permite estimar la potencia de eje.",
                }
            )
        else:
            estimated_w = hydraulic_power_w / eta
            marker["shaft_power_estimate"] = {
                "value": _display_power(estimated_w, power_key),
                "unit": presented["display_units"]["power"],
                "method": "Pshaft_estimated = P_hyd / η",
                "interpolation": "linear",
                "efficiency_fraction": eta,
                "flow": marker["flow"],
                "note": (
                    "Estimación derivada con la eficiencia de la curva en este caudal. "
                    "No es la potencia de eje publicada. No incluye pérdidas del motor ni del variador."
                ),
            }
    reference = curve["specific_gravity_reference"] * 1000.0
    if reference > 0 and abs(density_kg_m3 - reference) / reference > 0.02:
        warnings.append(
            {
                "code": "density_not_corrected",
                "message": (
                    "La curva está referida a la gravedad específica de la ficha. "
                    "No se corrige por viscosidad y no se presenta como válida para otro fluido."
                ),
            }
        )
    return {**presented, "marker": marker, "warnings": warnings}
