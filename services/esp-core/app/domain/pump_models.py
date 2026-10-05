"""Contrato de la bomba multietapa. Etapa 1B.

Este documento sigue siendo cualitativo. Las magnitudes numéricas salen del motor
en ``app.physics`` y no se incrustan aquí. ``quantitative_model`` permanece en null.
"""

from typing import Literal

from pydantic import BaseModel, Field

Motion = Literal["rotating", "stationary"]
PartType = Literal["impeller", "diffuser"]
StepKind = Literal["boundary", "stage", "part"]


class StagePart(BaseModel):
    id: str
    type: PartType
    name: str
    motion: Motion
    motion_label: str
    simple_explanation: str
    technical_explanation: str
    receives: str
    delivers: str


class PumpStage(BaseModel):
    id: str
    type: Literal["pump_stage"] = "pump_stage"
    order: int
    name: str
    inlet: str
    outlet: str
    next_label: str
    components: list[StagePart]


class FlowPathStep(BaseModel):
    order: int
    id: str
    label: str
    kind: StepKind
    summary: str


class FlowPath(BaseModel):
    id: str
    note: str
    steps: list[FlowPathStep]


class PumpFlowPaths(BaseModel):
    single_stage: FlowPath
    multistage: FlowPath


class EnergyMark(BaseModel):
    id: str
    label: str
    order: int
    blocks: str
    adds_energy: bool


class PumpStatus(BaseModel):
    simulation: str
    physics_engine: str
    realtime_control: str
    ai_model: str


class PumpCapabilities(BaseModel):
    simulation: bool = False
    physics_engine: bool = False
    ai_model: bool = False
    control: bool = False


class PumpDescription(BaseModel):
    id: str
    name: str
    stage: str
    stage_label: str
    overview_component_id: str
    disclaimer: str
    definition: str
    why_multistage: str
    stage_count_note: str
    animation_note: str
    fluid_path_note: str
    energy_note: str
    status: PumpStatus
    capabilities: PumpCapabilities
    stages: list[PumpStage]
    flow_path: PumpFlowPaths
    energy_marks: list[EnergyMark]
    quantitative_model: dict | None = Field(
        default=None,
        description="Reservado para la etapa 1C. Presión, head, caudal y energía cuantitativa.",
    )


class PumpStagesResponse(BaseModel):
    stage: str
    stage_count_note: str
    definition: str
    stages: list[PumpStage]


class PumpFlowResponse(BaseModel):
    stage: str
    animation_note: str
    fluid_path_note: str
    single_stage: FlowPath
    multistage: FlowPath
