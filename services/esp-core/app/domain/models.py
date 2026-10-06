"""Contrato de datos de la etapa 1A.

Las claves de ``extensions`` quedan reservadas para etapas posteriores.
En 1A deben permanecer en null. No representan sensores, estados ni cálculos.
"""

from typing import Literal

from pydantic import BaseModel, Field

STAGE = "1A"
PUMP_STAGE = "1B"
PROJECT_PHASE = "2"
PROJECT_STAGE = "2-0"
FOUNDATION_STAGE = "1F"
SERVICE_NAME = "esp-core"

Location = Literal["surface", "downhole", "wellbore", "reservoir"]
Category = Literal["electrical", "mechanical", "hydraulic", "structural", "flow"]


class ExtensionSlots(BaseModel):
    """Huecos aditivos. Poblarlos es responsabilidad de una etapa futura."""

    variables: dict | None = Field(default=None, description="Reservado. Sin variables físicas en 1A.")
    sensors: dict | None = Field(default=None, description="Reservado. Sin sensores en 1A.")
    states: dict | None = Field(default=None, description="Reservado. Sin estados operativos en 1A.")
    limits: dict | None = Field(default=None, description="Reservado. Sin límites en 1A.")
    equations: dict | None = Field(default=None, description="Reservado. Sin ecuaciones en 1A.")
    alarms: dict | None = Field(default=None, description="Reservado. Sin alarmas en 1A.")
    events: dict | None = Field(default=None, description="Reservado. Sin eventos en 1A.")
    predictive_models: dict | None = Field(
        default=None, description="Reservado. Sin modelos predictivos en 1A."
    )


class Component(BaseModel):
    id: str
    name: str
    location: Location
    location_label: str
    category: Category
    description: str
    function: str
    input: str
    output: str
    relation: str
    relations: list[str]
    display_order: int
    extensions: ExtensionSlots = Field(default_factory=ExtensionSlots)


class FlowStep(BaseModel):
    order: int
    component_id: str
    label: str


class Flow(BaseModel):
    id: Literal["energy", "fluid"]
    name: str
    description: str
    steps: list[FlowStep]


class FlowSet(BaseModel):
    energy: Flow
    fluid: Flow


class Capabilities(BaseModel):
    simulation: bool = False
    physics_engine: bool = False
    ai_model: bool = False
    control: bool = False


class EspAssembly(BaseModel):
    id: str
    name: str
    stage: str
    stage_label: str
    mode: str
    disclaimer: str
    capabilities: Capabilities
    components: list[Component]
    flows: FlowSet


class PhysicsAvailability(BaseModel):
    """Disponibilidad del motor. El cálculo vive en ``app.physics``."""

    enabled: bool
    model: str
    mode: Literal["static"]


class ResearchAvailability(BaseModel):
    """Gobernanza de datos de la etapa vigente. No implica un modelo de IA."""

    enabled: bool
    stage: str
    ai_model: bool


class HealthStatus(BaseModel):
    service: str
    status: Literal["healthy"]
    stage: str
    phase: str
    foundation_stage: str
    physics: PhysicsAvailability
    research: ResearchAvailability


class ComponentListResponse(BaseModel):
    stage: str
    components: list[Component]


class FlowListResponse(BaseModel):
    stage: str
    flows: FlowSet
