from fastapi import APIRouter

from app.domain.catalog import get_assembly
from app.api.physics import physics_availability
from app.domain.models import (
    SERVICE_NAME,
    PROJECT_STAGE,
    ComponentListResponse,
    EspAssembly,
    FlowListResponse,
    HealthStatus,
    PhysicsAvailability,
)
from app.domain.pump import get_pump
from app.domain.pump_models import PumpDescription, PumpFlowResponse, PumpStagesResponse

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(
        service=SERVICE_NAME,
        status="healthy",
        stage=PROJECT_STAGE,
        physics=PhysicsAvailability(**physics_availability()),
    )


@router.get("/esp", response_model=EspAssembly)
def esp_assembly() -> EspAssembly:
    return get_assembly()


@router.get("/esp/components", response_model=ComponentListResponse)
def esp_components() -> ComponentListResponse:
    assembly = get_assembly()
    return ComponentListResponse(stage=assembly.stage, components=assembly.components)


@router.get("/esp/flows", response_model=FlowListResponse)
def esp_flows() -> FlowListResponse:
    assembly = get_assembly()
    return FlowListResponse(stage=assembly.stage, flows=assembly.flows)


@router.get("/esp/pump", response_model=PumpDescription)
def esp_pump() -> PumpDescription:
    return get_pump()


@router.get("/esp/pump/stages", response_model=PumpStagesResponse)
def esp_pump_stages() -> PumpStagesResponse:
    pump = get_pump()
    return PumpStagesResponse(
        stage=pump.stage,
        stage_count_note=pump.stage_count_note,
        definition=pump.definition,
        stages=pump.stages,
    )


@router.get("/esp/pump/flow-path", response_model=PumpFlowResponse)
def esp_pump_flow_path() -> PumpFlowResponse:
    pump = get_pump()
    return PumpFlowResponse(
        stage=pump.stage,
        animation_note=pump.animation_note,
        fluid_path_note=pump.fluid_path_note,
        single_stage=pump.flow_path.single_stage,
        multistage=pump.flow_path.multistage,
    )
