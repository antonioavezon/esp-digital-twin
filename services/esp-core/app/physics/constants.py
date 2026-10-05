"""Constantes del modelo hydraulics-v0.1.

La densidad del agua educativa es un valor sugerido, no un número enterrado
en las ecuaciones. Quien llama al motor pasa la densidad que quiere usar.
"""

PHYSICS_MODEL = "hydraulics-v0.1"
PHYSICS_MODE = "static"

# Gravedad estándar convencional. No es una medición del pozo.
STANDARD_GRAVITY_M_S2 = 9.80665

# Caso de partida para el laboratorio. Las fórmulas reciben ρ como argumento.
DEFAULT_DENSITY_KG_M3 = 1000.0

VARIABLE_SOURCES = ("user_input", "physics_model", "constant")
RESERVED_SOURCES = ("sensor", "simulation", "ml", "physics_ai")

STATUS = {
    "stage": "1C — Basic Hydraulics",
    "anatomy": "Enabled",
    "pump_internal_view": "Enabled",
    "physics_engine": PHYSICS_MODEL,
    "simulation": "Basic static calculations",
    "dynamic_simulation": "Not enabled",
    "ai_model": "Not enabled",
}
