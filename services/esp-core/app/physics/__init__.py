"""Motor físico estático. Hoy: hidráulica monofásica v0.1.

El paquete no conoce HTTP ni HTML. Una etapa posterior puede extraerlo
si el cálculo deja de caber en esp-core.
"""

from app.physics.constants import PHYSICS_MODEL, PHYSICS_MODE

__all__ = ["PHYSICS_MODEL", "PHYSICS_MODE"]
