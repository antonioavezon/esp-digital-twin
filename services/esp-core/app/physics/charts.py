"""Barridos de las ecuaciones ya implementadas.

No son curvas de bomba. Cada punto sale de pressure_to_head o hydraulic_power_from_head.
"""

from app.physics.constants import PHYSICS_MODEL, STANDARD_GRAVITY_M_S2
from app.physics.hydraulics import (
    hydraulic_power_from_head,
    pressure_difference,
    pressure_to_head,
    run_hydraulics,
)
from app.physics.schema import HydraulicsRequest
from app.physics.units import to_cubic_metres_per_second, to_kg_per_m3, to_pascal


def _linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + index * step for index in range(count)]


def _plot(points: list[dict]) -> list[dict]:
    xs = [point["x"] for point in points]
    ys = [point["y"] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x
    span_y = max_y - min_y
    plotted = []
    for point in points:
        plot_x = 50.0 if span_x == 0 else (point["x"] - min_x) / span_x * 100.0
        plot_y = 50.0 if span_y == 0 else (point["y"] - min_y) / span_y * 100.0
        plotted.append({**point, "plot_x": plot_x, "plot_y": plot_y})
    return plotted


def _include(values: list[float], extra: float) -> list[float]:
    if any(abs(item - extra) <= 1e-12 * max(1.0, abs(extra)) for item in values):
        return values
    return sorted([*values, extra])


def build_charts(request: HydraulicsRequest, *, gravity: float = STANDARD_GRAVITY_M_S2) -> dict:
    solved = run_hydraulics(request, gravity=gravity)
    intake_pa = to_pascal(request.intake_pressure.value, request.intake_pressure.unit)
    discharge_pa = to_pascal(request.discharge_pressure.value, request.discharge_pressure.unit)
    density = to_kg_per_m3(request.density.value, request.density.unit)
    flow = to_cubic_metres_per_second(request.flow_rate.value, request.flow_rate.unit)
    delta_p = pressure_difference(discharge_pa, intake_pa)
    head = solved["results"]["head"]["si_value"]

    if delta_p > 0:
        span = _linspace(0.0, delta_p * 1.5, 8)
    else:
        span = _linspace(0.0, 200_000.0, 8)
    delta_samples = _include(span, delta_p)
    head_points = [
        {
            "x": sample,
            "y": pressure_to_head(sample, density, gravity),
            "x_unit": "Pa",
            "y_unit": "m",
        }
        for sample in delta_samples
    ]

    flow_stop = flow * 1.5 if flow > 0 else 0.001
    flow_samples = _include(_linspace(0.0, flow_stop, 8), flow)
    power_points = [
        {
            "x": sample,
            "y": hydraulic_power_from_head(density, gravity, sample, head),
            "x_unit": "m³/s",
            "y_unit": "W",
        }
        for sample in flow_samples
    ]

    return {
        "physics_model": PHYSICS_MODEL,
        "head_vs_pressure": {
            "title": "Head frente a ΔP",
            "note": (
                "Barrido de H = ΔP / (ρ g) con la densidad de este caso fija. "
                "No es una curva H-Q de bomba."
            ),
            "held_constant": ["density", "gravity"],
            "points": _plot(head_points),
        },
        "power_vs_flow": {
            "title": "Potencia hidráulica frente a caudal",
            "note": (
                "Barrido de P_hyd = ρ g Q H con el head de este caso fijo. "
                "No es la curva de potencia de una bomba."
            ),
            "held_constant": ["head", "density", "gravity"],
            "points": _plot(power_points),
        },
    }
