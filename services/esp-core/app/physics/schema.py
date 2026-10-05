"""Contrato HTTP del motor hidráulico. No contiene ecuaciones."""

from pydantic import BaseModel, Field


class MeasuredValue(BaseModel):
    value: float
    unit: str


class HydraulicsRequest(BaseModel):
    intake_pressure: MeasuredValue
    discharge_pressure: MeasuredValue
    density: MeasuredValue
    flow_rate: MeasuredValue
    stages: int | None = None


class FluidCase(BaseModel):
    name: str = Field(min_length=1)
    density: MeasuredValue


class CompareRequest(BaseModel):
    intake_pressure: MeasuredValue
    discharge_pressure: MeasuredValue
    flow_rate: MeasuredValue
    fluids: list[FluidCase] = Field(min_length=2)
