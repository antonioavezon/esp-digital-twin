"""Conversiones hacia y desde el Sistema Internacional.

Las funciones de hidráulica trabajan en Pa, m, kg, s, m³/s y W.
Este módulo es el único lugar con factores de conversión.
"""

from app.physics.constants import STANDARD_GRAVITY_M_S2

# 1 lbf/in² en pascales. Valor NIST usado de forma explícita.
PSI_TO_PA = 6894.757293168361
BAR_TO_PA = 100_000.0
KPA_TO_PA = 1_000.0

# Barril de petróleo estadounidense: 42 galones US = 0.158987294928 m³.
BARREL_M3 = 0.158987294928
SECONDS_PER_DAY = 86_400.0
FT_TO_M = 0.3048
HP_TO_W = 745.6998715822702

_PRESSURE_TO_PA = {
    "pa": 1.0,
    "kpa": KPA_TO_PA,
    "bar": BAR_TO_PA,
    "psi": PSI_TO_PA,
}
_FLOW_TO_M3S = {
    "m3/s": 1.0,
    "m3/day": 1.0 / SECONDS_PER_DAY,
    "bpd": BARREL_M3 / SECONDS_PER_DAY,
}
_DENSITY_TO_KG_M3 = {
    "kg/m3": 1.0,
}
_HEAD_TO_M = {
    "m": 1.0,
    "ft": FT_TO_M,
}
_POWER_TO_W = {
    "w": 1.0,
    "kw": 1000.0,
    "hp": HP_TO_W,
}

PRESSURE_UNITS = tuple(_PRESSURE_TO_PA)
FLOW_UNITS = tuple(_FLOW_TO_M3S)
DENSITY_UNITS = tuple(_DENSITY_TO_KG_M3)
HEAD_UNITS = tuple(_HEAD_TO_M)
POWER_UNITS = ("hp", "kW")


class UnitError(ValueError):
    def __init__(self, unit: str, family: str):
        self.unit = unit
        self.family = family
        super().__init__(f"Unidad desconocida para {family}: {unit}")


def canonical_unit(unit: str) -> str:
    text = unit.strip().lower().replace("³", "3").replace("μ", "u")
    text = text.replace(" ", "")
    aliases = {
        "m³/s": "m3/s",
        "m^3/s": "m3/s",
        "m³/day": "m3/day",
        "m^3/day": "m3/day",
        "m3/d": "m3/day",
        "kg/m³": "kg/m3",
        "kg/m^3": "kg/m3",
        "ft": "ft",
        "feet": "ft",
        "kw": "kw",
        "hp": "hp",
        "w": "w",
    }
    return aliases.get(text, text)


def _factor(table: dict[str, float], unit: str, family: str) -> float:
    key = canonical_unit(unit)
    if key not in table:
        raise UnitError(unit, family)
    return table[key]


def to_pascal(value: float, unit: str) -> float:
    return value * _factor(_PRESSURE_TO_PA, unit, "presión")


def from_pascal(value_pa: float, unit: str) -> float:
    return value_pa / _factor(_PRESSURE_TO_PA, unit, "presión")


def to_cubic_metres_per_second(value: float, unit: str) -> float:
    return value * _factor(_FLOW_TO_M3S, unit, "caudal")


def from_cubic_metres_per_second(value_m3s: float, unit: str) -> float:
    return value_m3s / _factor(_FLOW_TO_M3S, unit, "caudal")


def to_kg_per_m3(value: float, unit: str) -> float:
    return value * _factor(_DENSITY_TO_KG_M3, unit, "densidad")


def to_metres(value: float, unit: str) -> float:
    return value * _factor(_HEAD_TO_M, unit, "head")


def from_metres(value_m: float, unit: str) -> float:
    return value_m / _factor(_HEAD_TO_M, unit, "head")


def to_watts(value: float, unit: str) -> float:
    return value * _factor(_POWER_TO_W, unit, "potencia")


def from_watts(value_w: float, unit: str) -> float:
    return value_w / _factor(_POWER_TO_W, unit, "potencia")


def pressure_presentations(value_pa: float) -> dict[str, float]:
    return {unit: from_pascal(value_pa, unit) for unit in PRESSURE_UNITS}


def flow_presentations(value_m3s: float) -> dict[str, float]:
    return {unit: from_cubic_metres_per_second(value_m3s, unit) for unit in FLOW_UNITS}


def format_quantity(value: float, unit: str) -> str:
    """Texto de presentación. No se usa como entrada de otro cálculo."""
    return f"{value:.6g} {unit}"


def gravity_display() -> str:
    return format_quantity(STANDARD_GRAVITY_M_S2, "m/s²")
