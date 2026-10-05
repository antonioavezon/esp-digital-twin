"""Descripción cualitativa de la bomba centrífuga multietapa.

Tres etapas son una representación didáctica, no un diseño de equipo.
"""

from app.domain.models import PUMP_STAGE
from app.domain.pump_models import (
    EnergyMark,
    FlowPath,
    FlowPathStep,
    PumpCapabilities,
    PumpDescription,
    PumpFlowPaths,
    PumpStage,
    PumpStatus,
    StagePart,
)

IMPELLER_SIMPLE = "El impulsor gira y entrega energía al fluido."
IMPELLER_TECHNICAL = (
    "El impulsor es el elemento rotativo de la etapa centrífuga. "
    "Está unido al eje, recibe de él energía mecánica y la transfiere al fluido. "
    "El fluido entra cerca del centro y el giro lo dirige hacia la salida del impulsor, "
    "donde lo recoge el difusor."
)
DIFFUSER_SIMPLE = "El difusor permanece fijo y guía el fluido hacia la siguiente etapa."
DIFFUSER_TECHNICAL = (
    "El difusor es estacionario. Recibe el fluido que sale del impulsor y lo conduce "
    "hacia la entrada de la etapa siguiente. La transferencia de energía y la conversión "
    "entre formas de esa energía ocurren en el conjunto de la etapa, impulsor y difusor, "
    "no en una sola de las dos piezas."
)

STAGE_COUNT_NOTE = "Educational representation — real ESP stage count depends on design."
ANIMATION_NOTE = "Conceptual animation — not physical RPM"
ENERGY_NOTE = "Conceptual energy representation"
FLUID_NOTE = (
    "El recorrido es didáctico. No representa una velocidad real del fluido."
)

FORBIDDEN_KEYS = {
    "head",
    "efficiency",
    "bep",
    "flow_rate",
    "pressure",
    "frequency",
    "horsepower",
    "rpm",
    "affinity",
    "cavitation",
}


def _impeller(stage_number: int) -> StagePart:
    return StagePart(
        id=f"stage-{stage_number}-impeller",
        type="impeller",
        name="Impulsor",
        motion="rotating",
        motion_label="GIRA · ROTATING",
        simple_explanation=IMPELLER_SIMPLE,
        technical_explanation=IMPELLER_TECHNICAL,
        receives="Energía mecánica del eje y fluido que entra a la etapa.",
        delivers="Fluido con energía añadida, hacia el difusor.",
    )


def _diffuser(stage_number: int) -> StagePart:
    return StagePart(
        id=f"stage-{stage_number}-diffuser",
        type="diffuser",
        name="Difusor",
        motion="stationary",
        motion_label="FIJO · STATIONARY",
        simple_explanation=DIFFUSER_SIMPLE,
        technical_explanation=DIFFUSER_TECHNICAL,
        receives="Fluido que sale del impulsor de la misma etapa.",
        delivers="Fluido guiado hacia la entrada de la etapa siguiente, o hacia la descarga si es la última.",
    )


def _stages() -> list[PumpStage]:
    boundaries = {
        1: (
            "El fluido entra desde la admisión de la bomba.",
            "El fluido sale del difusor hacia la etapa 2.",
            "Etapa 2",
        ),
        2: (
            "El fluido entra desde el difusor de la etapa 1.",
            "El fluido sale del difusor hacia la etapa 3.",
            "Etapa 3",
        ),
        3: (
            "El fluido entra desde el difusor de la etapa 2.",
            "El fluido sale del difusor hacia la descarga de la bomba.",
            "Descarga",
        ),
    }
    stages = []
    for number in (1, 2, 3):
        inlet, outlet, nxt = boundaries[number]
        stages.append(
            PumpStage(
                id=f"stage-{number}",
                order=number,
                name=f"Etapa {number}",
                inlet=inlet,
                outlet=outlet,
                next_label=nxt,
                components=[_impeller(number), _diffuser(number)],
            )
        )
    return stages


def _flow_paths() -> PumpFlowPaths:
    single = FlowPath(
        id="single-stage",
        note="Recorrido dentro de una etapa. La etapa siguiente puede ser otra etapa o la descarga.",
        steps=[
            FlowPathStep(
                order=1,
                id="intake",
                label="Admisión",
                kind="boundary",
                summary="El fluido llega desde la admisión de la bomba, antes de la primera etapa.",
            ),
            FlowPathStep(
                order=2,
                id="impeller",
                label="Impulsor",
                kind="part",
                summary="El impulsor, que gira con el eje, entrega energía al fluido.",
            ),
            FlowPathStep(
                order=3,
                id="diffuser",
                label="Difusor",
                kind="part",
                summary="El difusor, que no gira, conduce el fluido hacia la salida de la etapa.",
            ),
            FlowPathStep(
                order=4,
                id="next-stage",
                label="Etapa siguiente",
                kind="boundary",
                summary="El fluido pasa a la etapa siguiente. En la última, pasa a la descarga.",
            ),
        ],
    )
    multi = FlowPath(
        id="multistage",
        note=STAGE_COUNT_NOTE,
        steps=[
            FlowPathStep(
                order=1,
                id="intake",
                label="Admisión",
                kind="boundary",
                summary="Punto de entrada del fluido a la bomba. Todavía no atravesó ninguna etapa.",
            ),
            FlowPathStep(
                order=2,
                id="stage-1",
                label="Etapa 1",
                kind="stage",
                summary="Primera pareja impulsor y difusor. Agrega energía al fluido, en sentido conceptual.",
            ),
            FlowPathStep(
                order=3,
                id="stage-2",
                label="Etapa 2",
                kind="stage",
                summary="Segunda etapa. El fluido llega desde la etapa 1 y recibe otro aporte de energía.",
            ),
            FlowPathStep(
                order=4,
                id="stage-3",
                label="Etapa 3",
                kind="stage",
                summary="Tercera etapa de esta representación. Una ESP real puede tener más o menos etapas.",
            ),
            FlowPathStep(
                order=5,
                id="discharge",
                label="Descarga",
                kind="boundary",
                summary="El fluido abandona la bomba hacia el tubing. La descarga no es una etapa adicional.",
            ),
        ],
    )
    return PumpFlowPaths(single_stage=single, multistage=multi)


def _energy_marks() -> list[EnergyMark]:
    rows = [
        ("intake", "Admisión", 1, "█", False),
        ("stage-1", "Etapa 1", 2, "██", True),
        ("stage-2", "Etapa 2", 3, "███", True),
        ("stage-3", "Etapa 3", 4, "████", True),
        ("discharge", "Descarga", 5, "████", False),
    ]
    return [
        EnergyMark(id=mark_id, label=label, order=order, blocks=blocks, adds_energy=adds)
        for mark_id, label, order, blocks, adds in rows
    ]


def assert_pump(pump: PumpDescription) -> None:
    if pump.quantitative_model is not None:
        raise ValueError("El modelo cuantitativo debe permanecer vacío hasta la etapa 1C.")
    if pump.capabilities.model_dump() != {
        "simulation": False,
        "physics_engine": False,
        "ai_model": False,
        "control": False,
    }:
        raise ValueError("La etapa 1B no habilita simulación, física, IA ni control.")
    if len(pump.stages) != 3:
        raise ValueError("La representación didáctica usa tres etapas.")
    ids = []
    for stage in pump.stages:
        if [part.type for part in stage.components] != ["impeller", "diffuser"]:
            raise ValueError(f"{stage.id} debe ser impulsor y luego difusor.")
        motions = [part.motion for part in stage.components]
        if motions != ["rotating", "stationary"]:
            raise ValueError(f"{stage.id} no distingue rotación y pieza fija.")
        ids.extend(part.id for part in stage.components)
        ids.append(stage.id)
    if len(ids) != len(set(ids)):
        raise ValueError("Hay identificadores repetidos en la bomba.")
    multi = [step.id for step in pump.flow_path.multistage.steps]
    if multi != ["intake", "stage-1", "stage-2", "stage-3", "discharge"]:
        raise ValueError("El recorrido multietapa no coincide con el contrato de 1B.")
    single = [step.id for step in pump.flow_path.single_stage.steps]
    if single != ["intake", "impeller", "diffuser", "next-stage"]:
        raise ValueError("El recorrido de una etapa no coincide con el contrato de 1B.")


def get_pump() -> PumpDescription:
    pump = PumpDescription(
        id="pump-educational-1b",
        name="Bomba centrífuga multietapa",
        stage=PUMP_STAGE,
        stage_label="1B — Multistage Centrifugal Pump",
        overview_component_id="pump",
        disclaimer=(
            "Educational / Simulation Environment. "
            "Esta vista no calcula el comportamiento de una bomba real."
        ),
        definition="1 etapa = impulsor + difusor.",
        why_multistage=(
            "Una etapa aporta energía al fluido, pero esa contribución es limitada. "
            "Una ESP encadena etapas para poder elevar el fluido hasta la superficie. "
            "La cantidad de etapas depende del diseño y de la aplicación. "
            "No existe un número único válido para todas las bombas."
        ),
        stage_count_note=STAGE_COUNT_NOTE,
        animation_note=ANIMATION_NOTE,
        fluid_path_note=FLUID_NOTE,
        energy_note=ENERGY_NOTE,
        status=PumpStatus(
            simulation="Conceptual only",
            physics_engine="Not enabled",
            realtime_control="Not enabled",
            ai_model="Not enabled",
        ),
        capabilities=PumpCapabilities(),
        stages=_stages(),
        flow_path=_flow_paths(),
        energy_marks=_energy_marks(),
        quantitative_model=None,
    )
    assert_pump(pump)
    return pump
