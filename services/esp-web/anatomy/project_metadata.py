"""Metadatos públicos de presentación de ESP Digital Twin.

La etapa técnica y el identificador del modelo físico coinciden con esp-core.
About puede sustituirlos por la respuesta de salud del núcleo cuando está
disponible. Este módulo no calcula física ni lee configuración del host.
"""

PROJECT_NAME = "ESP Digital Twin"
PROJECT_YEAR = 2026
DEVELOPMENT_STAGE = "1C"
PHYSICS_MODEL = "hydraulics-v0.1"
PHYSICS_MODE = "static"
ENHANCEMENT_ID = "1C.1"
ENHANCEMENT_LABEL = "About & Project Credits — 1C.1"

STAGE_LABELS = {
    "1A": "1A — Anatomy",
    "1B": "1B — Multistage Centrifugal Pump",
    "1C": "1C — Basic Hydraulics",
}

AUTHOR = {
    "name": "Antonio Ralph Avezon Saavedra",
    "role": "Desarrollador e investigador",
    "degree": "Ingeniero en Informática",
    "study": "Estudiante del Magíster en Gestión de TI y Telecomunicaciones",
    "university": "Universidad Andrés Bello",
    "university_short": "UNAB",
    "country": "Chile",
}

RESEARCH = {
    "program": "Virtual Research Internship",
    "program_short": "VRI",
    "title_en": (
        "Hybrid Physics-AI Model for Sensorless Monitoring "
        "and Anomaly Detection in ESP Systems"
    ),
    "title_es": (
        "Modelo híbrido Física-IA para monitoreo sin sensores "
        "y detección de anomalías en sistemas ESP."
    ),
}

SUPERVISION = (
    {
        "role": "Profesor guía UNAB",
        "name": "Juan Pablo Vásconez",
        "institution": "Universidad Andrés Bello",
    },
    {
        "role": "Profesor líder VRI",
        "name": "Nicolás Ratkovich",
        "institution": "Universidad de los Andes, Colombia",
    },
)

STACK = (
    "Python",
    "Django",
    "FastAPI",
    "JavaScript",
    "HTML5",
    "CSS",
    "SVG",
    "Podman",
)

PLANNED_CAPABILITIES = (
    "Machine Learning",
    "Modelos physics-informed",
    "Digital twin operativo",
    "Detección de anomalías",
)

PHILOSOPHY = (
    "Understand",
    "Model",
    "Simulate",
    "Measure",
    "Predict",
    "Hybridize",
)

ROADMAP = (
    {
        "id": "1A",
        "name": "Anatomy",
        "status": "done",
        "hint": "Esquema del conjunto sin valores de operación",
    },
    {
        "id": "1B",
        "name": "Multistage Pump",
        "status": "done",
        "hint": "Interior de la bomba: impulsor y difusor",
    },
    {
        "id": "1C",
        "name": "Basic Hydraulics",
        "status": "done",
        "hint": "Presión diferencial, head y potencia hidráulica",
    },
    {
        "id": "1D",
        "name": "Pump Performance Curves",
        "status": "done",
        "hint": "Curvas de la bomba frente al caudal",
    },
    {
        "id": "1E",
        "name": "Motor",
        "status": "done",
        "hint": "Modelo del motor eléctrico de fondo",
    },
    {
        "id": "1F",
        "name": "VSD/VFD",
        "status": "done",
        "hint": "Variador y su efecto sobre la velocidad",
    },
)

STATUS_LABELS = {
    "done": "Completada",
    "planned": "Prevista",
}


def stage_label_for(stage: str) -> str:
    return STAGE_LABELS.get(stage, f"Stage {stage}")


def public_context() -> dict:
    """Datos institucionales aptos para plantillas. Sin secretos ni rutas de host."""
    return {
        "name": PROJECT_NAME,
        "year": PROJECT_YEAR,
        "stage": DEVELOPMENT_STAGE,
        "stage_label": stage_label_for(DEVELOPMENT_STAGE),
        "stage_name": "Basic Hydraulics Physics Engine",
        "physics_model": PHYSICS_MODEL,
        "physics_mode": PHYSICS_MODE,
        "simulation_label": "Basic static calculations",
        "ai_label": "Not enabled",
        "enhancement_id": ENHANCEMENT_ID,
        "enhancement_label": ENHANCEMENT_LABEL,
        "author": AUTHOR,
        "research": RESEARCH,
        "supervision": SUPERVISION,
        "stack": STACK,
        "planned_capabilities": PLANNED_CAPABILITIES,
        "philosophy": PHILOSOPHY,
        "roadmap": [
            {**item, "status_label": STATUS_LABELS[item["status"]]} for item in ROADMAP
        ],
    }
