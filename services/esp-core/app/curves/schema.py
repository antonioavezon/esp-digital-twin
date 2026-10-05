"""Contrato HTTP de las curvas. No contiene ecuaciones."""

from pydantic import BaseModel, Field


class LabPoint(BaseModel):
    flow_m3_s: float
    head_m: float
    hydraulic_power_w: float
    density_kg_m3: float = Field(gt=0)


class MarkerRequest(BaseModel):
    stages: int | None = None
    flow_unit: str = "bpd"
    head_unit: str = "ft"
    power_unit: str = "hp"
    lab: LabPoint
