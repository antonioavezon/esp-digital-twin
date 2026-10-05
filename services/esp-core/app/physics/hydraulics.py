"""Hidráulica estática de un fluido monofásico, incompresible y de densidad constante.

Las funciones puras reciben y devuelven magnitudes en el SI.
No redondean. El texto de los pasos es solo para mostrar el cálculo ya hecho.
"""

from app.physics.constants import (
    PHYSICS_MODEL,
    PHYSICS_MODE,
    STANDARD_GRAVITY_M_S2,
)
from app.physics.schema import CompareRequest, HydraulicsRequest, MeasuredValue
from app.physics.units import (
    UnitError,
    flow_presentations,
    format_quantity,
    from_pascal,
    pressure_presentations,
    to_cubic_metres_per_second,
    to_kg_per_m3,
    to_pascal,
)


class PhysicsInputError(Exception):
    def __init__(self, messages: list[dict[str, str]]):
        self.messages = messages
        super().__init__(messages[0]["message"] if messages else "entrada inválida")


def pressure_difference(discharge_pa: float, intake_pa: float) -> float:
    """ΔP = P_discharge − P_intake."""
    return discharge_pa - intake_pa


def pressure_to_head(delta_p_pa: float, density_kg_m3: float, gravity_m_s2: float) -> float:
    """H = ΔP / (ρ g). Densidad y gravedad deben ser distintas de cero."""
    return delta_p_pa / (density_kg_m3 * gravity_m_s2)


def hydraulic_power_from_head(
    density_kg_m3: float,
    gravity_m_s2: float,
    flow_m3_s: float,
    head_m: float,
) -> float:
    """P_hyd = ρ g Q H."""
    return density_kg_m3 * gravity_m_s2 * flow_m3_s * head_m


def hydraulic_power_from_delta_p(flow_m3_s: float, delta_p_pa: float) -> float:
    """P_hyd = Q ΔP. Equivale a ρ g Q H cuando H = ΔP / (ρ g)."""
    return flow_m3_s * delta_p_pa


def _fail(field: str, message: str) -> None:
    raise PhysicsInputError([{"field": field, "message": message}])


def _convert_pressure(field: str, measured: MeasuredValue) -> float:
    if measured.value < 0:
        _fail(field, "La presión no puede ser negativa en este modelo educativo.")
    try:
        return to_pascal(measured.value, measured.unit)
    except UnitError as exc:
        _fail(field, f"Unidad de presión desconocida: {exc.unit}. Use Pa, kPa, bar o psi.")


def _convert_density(measured: MeasuredValue) -> float:
    try:
        density = to_kg_per_m3(measured.value, measured.unit)
    except UnitError as exc:
        _fail("density", f"Unidad de densidad desconocida: {exc.unit}. Use kg/m3.")
    if density <= 0:
        _fail("density", "La densidad tiene que ser mayor que cero.")
    return density


def _convert_flow(measured: MeasuredValue) -> float:
    if measured.value < 0:
        _fail("flow_rate", "El caudal no puede ser negativo.")
    try:
        return to_cubic_metres_per_second(measured.value, measured.unit)
    except UnitError as exc:
        _fail("flow_rate", f"Unidad de caudal desconocida: {exc.unit}. Use m3/s, m3/day o bpd.")


def _stages(stages: int | None) -> int | None:
    if stages is None:
        return None
    if isinstance(stages, bool) or stages < 1:
        _fail("stages", "El número de etapas tiene que ser un entero mayor o igual que 1.")
    return stages


def _quantity(
    *,
    value: float,
    unit: str,
    si_value: float,
    si_unit: str,
    source: str,
    role: str,
    display: str,
    presentations: dict | None = None,
) -> dict:
    item = {
        "value": value,
        "unit": unit,
        "si_value": si_value,
        "si_unit": si_unit,
        "source": source,
        "role": role,
        "display": display,
    }
    if presentations is not None:
        item["presentations"] = presentations
    return item


def run_hydraulics(request: HydraulicsRequest, *, gravity: float = STANDARD_GRAVITY_M_S2) -> dict:
    intake_pa = _convert_pressure("intake_pressure", request.intake_pressure)
    discharge_pa = _convert_pressure("discharge_pressure", request.discharge_pressure)
    density = _convert_density(request.density)
    flow = _convert_flow(request.flow_rate)
    stage_count = _stages(request.stages)

    delta_p = pressure_difference(discharge_pa, intake_pa)
    head = pressure_to_head(delta_p, density, gravity)
    power = hydraulic_power_from_head(density, gravity, flow, head)
    power_from_pressure = hydraulic_power_from_delta_p(flow, delta_p)

    warnings: list[dict[str, str]] = []
    if discharge_pa <= intake_pa:
        warnings.append(
            {
                "code": "discharge_not_above_intake",
                "message": (
                    "La presión de descarga no supera a la de entrada. "
                    "El cálculo sigue, pero este no es el escenario educativo de una bomba impulsando fluido. "
                    "ΔP nulo o negativo no describe el aporte de presión esperado."
                ),
            }
        )
    if flow == 0:
        warnings.append(
            {
                "code": "zero_flow",
                "message": "El caudal es cero. La potencia hidráulica resulta cero porque no hay flujo.",
            }
        )

    pressure_unit = request.discharge_pressure.unit
    try:
        delta_display_value = from_pascal(delta_p, pressure_unit)
        delta_display = format_quantity(delta_display_value, pressure_unit)
    except UnitError:
        delta_display = format_quantity(delta_p, "Pa")

    stage_head = None
    if stage_count is not None:
        per_stage = head / stage_count
        stage_head = {
            "n_stages": stage_count,
            "si_value": per_stage,
            "si_unit": "m",
            "source": "physics_model",
            "role": "calculated",
            "display": format_quantity(per_stage, "m"),
            "assumption": (
                "Simplificación ideal de aprendizaje: el head total se reparte en partes iguales. "
                "No afirma que cada etapa real produzca el mismo head en cualquier condición."
            ),
        }

    steps = [
        {
            "order": 1,
            "title": "Presión diferencial",
            "equation": "ΔP = P_discharge − P_intake",
            "substitution": (
                f"ΔP = {format_quantity(discharge_pa, 'Pa')} − {format_quantity(intake_pa, 'Pa')}"
            ),
            "result_value": delta_p,
            "result_unit": "Pa",
            "display": f"{format_quantity(delta_p, 'Pa')} ({delta_display})",
            "interpretation": (
                "ΔP es el incremento de presión entre la entrada y la descarga, "
                "con las simplificaciones de este modelo. Un valor positivo significa "
                "que la descarga está a mayor presión que la entrada."
            ),
        },
        {
            "order": 2,
            "title": "Head",
            "equation": "H = ΔP / (ρ · g)",
            "substitution": (
                f"H = {format_quantity(delta_p, 'Pa')} / "
                f"({format_quantity(density, 'kg/m³')} · {format_quantity(gravity, 'm/s²')})"
            ),
            "result_value": head,
            "result_unit": "m",
            "display": format_quantity(head, "m"),
            "interpretation": (
                "El head es energía por unidad de peso, escrita como altura equivalente "
                "de columna de fluido. No significa que haya una columna vertical de esa "
                "altura colocada físicamente sobre la bomba. La presión y el head no son "
                "la misma magnitud: a igual ΔP, un fluido más liviano da un head mayor."
            ),
        },
        {
            "order": 3,
            "title": "Potencia hidráulica",
            "equation": "P_hyd = ρ · g · Q · H",
            "substitution": (
                f"P_hyd = {format_quantity(density, 'kg/m³')} · "
                f"{format_quantity(gravity, 'm/s²')} · "
                f"{format_quantity(flow, 'm³/s')} · {format_quantity(head, 'm')}"
            ),
            "result_value": power,
            "result_unit": "W",
            "display": f"{format_quantity(power, 'W')} ({format_quantity(power / 1000.0, 'kW')})",
            "equivalence": {
                "equation": "P_hyd = Q · ΔP",
                "substitution": (
                    f"P_hyd = {format_quantity(flow, 'm³/s')} · {format_quantity(delta_p, 'Pa')}"
                ),
                "result_value": power_from_pressure,
                "result_unit": "W",
                "display": format_quantity(power_from_pressure, "W"),
            },
            "interpretation": (
                "Es la potencia que el modelo asocia al aumento de energía hidráulica del fluido. "
                "Con densidad constante, ρ g Q H y Q ΔP describen el mismo resultado. "
                "Todavía no es la potencia eléctrica del motor ni incluye eficiencia."
            ),
        },
    ]
    if stage_head is not None:
        steps.append(
            {
                "order": 4,
                "title": "Reparto ideal entre etapas",
                "equation": "H_etapa = H_total / N",
                "substitution": (
                    f"H_etapa = {format_quantity(head, 'm')} / {stage_count}"
                ),
                "result_value": stage_head["si_value"],
                "result_unit": "m",
                "display": stage_head["display"],
                "interpretation": stage_head["assumption"],
            }
        )

    return {
        "physics_model": PHYSICS_MODEL,
        "mode": PHYSICS_MODE,
        "inputs": {
            "intake_pressure": _quantity(
                value=request.intake_pressure.value,
                unit=request.intake_pressure.unit,
                si_value=intake_pa,
                si_unit="Pa",
                source="user_input",
                role="input",
                display=format_quantity(request.intake_pressure.value, request.intake_pressure.unit),
                presentations=pressure_presentations(intake_pa),
            ),
            "discharge_pressure": _quantity(
                value=request.discharge_pressure.value,
                unit=request.discharge_pressure.unit,
                si_value=discharge_pa,
                si_unit="Pa",
                source="user_input",
                role="input",
                display=format_quantity(request.discharge_pressure.value, request.discharge_pressure.unit),
                presentations=pressure_presentations(discharge_pa),
            ),
            "density": _quantity(
                value=request.density.value,
                unit=request.density.unit,
                si_value=density,
                si_unit="kg/m³",
                source="user_input",
                role="input",
                display=format_quantity(density, "kg/m³"),
            ),
            "flow_rate": _quantity(
                value=request.flow_rate.value,
                unit=request.flow_rate.unit,
                si_value=flow,
                si_unit="m³/s",
                source="user_input",
                role="input",
                display=format_quantity(request.flow_rate.value, request.flow_rate.unit),
                presentations=flow_presentations(flow),
            ),
        },
        "constants": {
            "gravity": _quantity(
                value=gravity,
                unit="m/s²",
                si_value=gravity,
                si_unit="m/s²",
                source="constant",
                role="constant",
                display=format_quantity(gravity, "m/s²"),
            )
        },
        "results": {
            "pressure_difference": _quantity(
                value=delta_p,
                unit="Pa",
                si_value=delta_p,
                si_unit="Pa",
                source="physics_model",
                role="calculated",
                display=delta_display,
                presentations=pressure_presentations(delta_p),
            ),
            "head": _quantity(
                value=head,
                unit="m",
                si_value=head,
                si_unit="m",
                source="physics_model",
                role="calculated",
                display=format_quantity(head, "m"),
            ),
            "flow_rate": _quantity(
                value=flow,
                unit="m³/s",
                si_value=flow,
                si_unit="m³/s",
                source="user_input",
                role="input",
                display=format_quantity(request.flow_rate.value, request.flow_rate.unit),
                presentations=flow_presentations(flow),
            ),
            "hydraulic_power": _quantity(
                value=power,
                unit="W",
                si_value=power,
                si_unit="W",
                source="physics_model",
                role="calculated",
                display=format_quantity(power / 1000.0, "kW"),
                presentations={"W": power, "kW": power / 1000.0, "Q_delta_p_W": power_from_pressure},
            ),
            "stage_head": stage_head,
        },
        "calculation_steps": steps,
        "warnings": warnings,
        "notes": {
            "fluid": "Monofásico, incompresible, densidad constante.",
            "flow_rate_origin": "user_input",
            "flow_rate_later": (
                "En este modelo Q es una entrada del experimento. "
                "Una etapa posterior podrá relacionarlo con una curva de bomba."
            ),
            "time": "Cálculo estático. No hay evolución temporal.",
        },
    }


def compare_fluids(request: CompareRequest) -> dict:
    cases = []
    for fluid in request.fluids:
        single = HydraulicsRequest(
            intake_pressure=request.intake_pressure,
            discharge_pressure=request.discharge_pressure,
            density=fluid.density,
            flow_rate=request.flow_rate,
        )
        cases.append({"name": fluid.name, "result": run_hydraulics(single)})

    deltas = [case["result"]["results"]["pressure_difference"]["si_value"] for case in cases]
    heads = [case["result"]["results"]["head"]["si_value"] for case in cases]
    same_pressure = all(abs(item - deltas[0]) <= 1e-6 for item in deltas)
    same_head = all(abs(item - heads[0]) <= 1e-9 for item in heads)
    if same_pressure and not same_head:
        lesson = (
            "La diferencia de presión es la misma. El head es distinto porque "
            "H = ΔP / (ρ g) y la densidad no es la misma. Presión y head no son sinónimos."
        )
    elif same_pressure and same_head:
        lesson = (
            "La diferencia de presión es la misma y el head también, "
            "porque las densidades comparadas producen el mismo resultado."
        )
    else:
        lesson = "Las diferencias de presión no coinciden, así que el head no se compara a ΔP constante."
    return {
        "physics_model": PHYSICS_MODEL,
        "mode": PHYSICS_MODE,
        "pressure_difference_same": same_pressure,
        "head_same": same_head,
        "lesson": lesson,
        "cases": cases,
    }
