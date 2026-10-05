"""Catálogo conceptual de una ESP para la etapa 1A.

Fuente única de la definición didáctica. No contiene parámetros de equipos
comerciales ni resultados de un modelo físico.
"""

from app.domain.models import (
    STAGE,
    Capabilities,
    Component,
    EspAssembly,
    Flow,
    FlowSet,
    FlowStep,
)

ENERGY_STEP_IDS = (
    "power-supply",
    "vsd",
    "electrical-cable",
    "motor",
    "shaft",
    "pump",
)

FLUID_STEP_IDS = (
    "reservoir",
    "well",
    "intake",
    "pump",
    "tubing",
    "surface",
)


def _component(**kwargs) -> Component:
    return Component(**kwargs)


def build_components() -> list[Component]:
    return [
        _component(
            id="surface",
            name="Superficie",
            location="surface",
            location_label="Superficie",
            category="structural",
            description=(
                "Zona de instalaciones fuera del pozo. Ahí están la alimentación, "
                "el variador y la llegada del fluido producido."
            ),
            function="Aloja los equipos de superficie y recibe la producción que asciende por el tubing.",
            input="Energía eléctrica del sitio y fluido producido que llega por el tubing.",
            output="Energía hacia el variador y fluido hacia las instalaciones de producción.",
            relation="Conecta el pozo con la alimentación eléctrica y con el manejo del fluido.",
            relations=["power-supply", "vsd", "production-flow", "well"],
            display_order=1,
        ),
        _component(
            id="power-supply",
            name="Alimentación eléctrica",
            location="surface",
            location_label="Superficie",
            category="electrical",
            description=(
                "Punto de suministro eléctrico de superficie que alimenta el sistema ESP. "
                "No representa un tablero, una tensión ni una red concretas."
            ),
            function="Entrega energía eléctrica al variador.",
            input="Energía eléctrica disponible en superficie.",
            output="Energía eléctrica hacia el VSD.",
            relation="Es el origen del recorrido energético del conjunto.",
            relations=["surface", "vsd"],
            display_order=2,
        ),
        _component(
            id="vsd",
            name="VSD / VFD",
            location="surface",
            location_label="Superficie",
            category="electrical",
            description=(
                "Variador de velocidad o de frecuencia, entre la alimentación y el cable. "
                "Más adelante se estudiará su efecto sobre la velocidad del motor. "
                "En esta etapa no se ajusta ni se simula la frecuencia."
            ),
            function="Acondiciona la energía eléctrica que viajará por el cable hacia el motor de fondo.",
            input="Energía eléctrica desde la alimentación.",
            output="Energía eléctrica hacia el cable.",
            relation="Intermedia entre la alimentación de superficie y el cable que baja al pozo.",
            relations=["power-supply", "electrical-cable"],
            display_order=3,
        ),
        _component(
            id="electrical-cable",
            name="Cable eléctrico",
            location="wellbore",
            location_label="Pozo",
            category="electrical",
            description=(
                "Cable de potencia que desciende por el espacio entre el casing y el tubing "
                "hasta el motor, en el extremo inferior del conjunto."
            ),
            function="Conduce la energía eléctrica desde el VSD hasta el motor.",
            input="Energía eléctrica proveniente del VSD.",
            output="Energía eléctrica en el motor de fondo.",
            relation="Une los equipos eléctricos de superficie con el motor. No alimenta la bomba de forma directa.",
            relations=["vsd", "motor"],
            display_order=4,
        ),
        _component(
            id="well",
            name="Pozo",
            location="wellbore",
            location_label="Pozo",
            category="structural",
            description=(
                "Conducto que comunica la superficie con la zona de interés. "
                "El cabezal (wellhead) marca el límite con superficie. "
                "En su interior se instalan el tubing, el cable y el conjunto ESP. "
                "No se modela la completación ni la presión del pozo."
            ),
            function="Contiene la ESP y da camino al fluido desde el reservorio hacia la superficie.",
            input="Fluido que proviene del reservorio.",
            output="Alojamiento para el cable, la sarta ESP y el tubing.",
            relation="Es el entorno físico donde se instala el conjunto de fondo.",
            relations=["reservoir", "surface", "tubing", "intake"],
            display_order=5,
        ),
        _component(
            id="tubing",
            name="Tubing",
            location="wellbore",
            location_label="Pozo",
            category="hydraulic",
            description=(
                "Tubería de producción colgada desde el cabezal. "
                "Conduce el fluido desde la descarga de la bomba hasta la superficie. "
                "No se calcula fricción ni se fija un diámetro."
            ),
            function="Canaliza el fluido producido hacia la superficie.",
            input="Fluido impulsado por la bomba.",
            output="Fluido hacia el cabezal y la superficie.",
            relation="Continúa el recorrido del fluido por encima de la bomba.",
            relations=["pump", "production-flow", "well"],
            display_order=6,
        ),
        _component(
            id="pump",
            name="Bomba",
            location="downhole",
            location_label="Fondo del pozo",
            category="hydraulic",
            description=(
                "Bomba centrífuga multietapa, en la parte superior del conjunto de fondo. "
                "Recibe rotación por el eje e impulsa el fluido hacia el tubing. "
                "No hay curvas, eficiencia ni cálculo de energía de bombeo."
            ),
            function="Transfiere energía al fluido para impulsarlo hacia la superficie.",
            input="Fluido desde la admisión y rotación mecánica del eje.",
            output="Fluido impulsado hacia el tubing.",
            relation="Es accionada por el motor a través del eje y descarga al tubing.",
            relations=["intake", "shaft", "tubing", "motor"],
            display_order=7,
        ),
        _component(
            id="intake",
            name="Admisión",
            location="downhole",
            location_label="Fondo del pozo",
            category="hydraulic",
            description=(
                "Entrada de fluido al conjunto de bombeo. "
                "El fluido del pozo ingresa aquí, desde el espacio anular, antes de la bomba. "
                "No se representa caudal."
            ),
            function="Permite que el fluido del pozo entre a la bomba.",
            input="Fluido proveniente del pozo.",
            output="Fluido hacia la bomba.",
            relation="Comunica el interior del pozo con la bomba. El eje la atraviesa.",
            relations=["well", "pump", "protector", "shaft"],
            display_order=8,
        ),
        _component(
            id="protector",
            name="Protector",
            location="downhole",
            location_label="Fondo del pozo",
            category="mechanical",
            description=(
                "Sección de sello entre el motor y la admisión. "
                "Aísla el motor, lleno de fluido dieléctrico, del fluido del pozo, "
                "y deja pasar el eje. No se calculan presiones ni volúmenes."
            ),
            function="Protege el motor del fluido del pozo y transmite la rotación del eje hacia arriba.",
            input="Rotación del eje desde el motor.",
            output="Rotación del eje hacia la admisión y la bomba.",
            relation="Separa el motor del fluido producido y mantiene la continuidad mecánica del eje.",
            relations=["motor", "intake", "shaft"],
            display_order=9,
        ),
        _component(
            id="shaft",
            name="Eje",
            location="downhole",
            location_label="Fondo del pozo",
            category="mechanical",
            description=(
                "Eje común del conjunto. Recorre el motor, el protector, la admisión y la bomba. "
                "Representa la rotación mecánica que acopla el motor con la bomba. "
                "No se modelan torque, velocidad ni vibración."
            ),
            function="Transmite la rotación del motor a la bomba.",
            input="Rotación generada por el motor.",
            output="Rotación aplicada a la bomba.",
            relation="Vincula mecánicamente el motor con la bomba a través del protector y la admisión.",
            relations=["motor", "protector", "intake", "pump"],
            display_order=10,
        ),
        _component(
            id="motor",
            name="Motor eléctrico",
            location="downhole",
            location_label="Fondo del pozo",
            category="electrical",
            description=(
                "Motor de fondo, en el extremo inferior del conjunto ESP. "
                "Convierte la energía eléctrica que llega por el cable en rotación del eje. "
                "No se representan potencia, corriente ni velocidad."
            ),
            function="Transforma energía eléctrica en energía mecánica.",
            input="Energía eléctrica.",
            output="Movimiento rotacional del eje.",
            relation="Acciona la bomba mediante el eje del conjunto ESP.",
            relations=["electrical-cable", "shaft", "protector"],
            display_order=11,
        ),
        _component(
            id="reservoir",
            name="Reservorio",
            location="reservoir",
            location_label="Reservorio",
            category="hydraulic",
            description=(
                "Origen conceptual del fluido. Indica de dónde proviene el líquido que entra al pozo. "
                "No hay modelo de yacimiento ni de productividad."
            ),
            function="Aporta el fluido que la ESP deberá elevar.",
            input="Fluido presente en la formación, en sentido conceptual.",
            output="Fluido hacia el pozo y, desde allí, hacia la admisión.",
            relation="Punto de partida del recorrido del fluido.",
            relations=["well"],
            display_order=12,
        ),
        _component(
            id="production-flow",
            name="Flujo de producción",
            location="surface",
            location_label="Superficie",
            category="flow",
            description=(
                "Recorrido conceptual del fluido ya elevado, desde la descarga de la bomba "
                "hasta su llegada a superficie. No es un equipo."
            ),
            function="Representa la salida del fluido del pozo hacia las instalaciones de superficie.",
            input="Fluido que asciende por el tubing.",
            output="Fluido en superficie.",
            relation="Cierra el recorrido del fluido iniciado en el reservorio.",
            relations=["tubing", "surface", "pump"],
            display_order=13,
        ),
    ]


def build_flows() -> FlowSet:
    energy_labels = {
        "power-supply": "Alimentación eléctrica",
        "vsd": "VSD / VFD",
        "electrical-cable": "Cable eléctrico",
        "motor": "Motor eléctrico",
        "shaft": "Rotación mecánica",
        "pump": "Bomba",
    }
    fluid_labels = {
        "reservoir": "Reservorio",
        "well": "Pozo",
        "intake": "Admisión",
        "pump": "Bomba",
        "tubing": "Tubing",
        "surface": "Superficie",
    }
    return FlowSet(
        energy=Flow(
            id="energy",
            name="ENERGY FLOW",
            description=(
                "La energía eléctrica parte de la alimentación en superficie, pasa por el VSD "
                "y el cable, llega al motor y se convierte en rotación del eje que acciona la bomba. "
                "No se calculan potencia ni velocidad."
            ),
            steps=[
                FlowStep(order=index, component_id=component_id, label=energy_labels[component_id])
                for index, component_id in enumerate(ENERGY_STEP_IDS, start=1)
            ],
        ),
        fluid=Flow(
            id="fluid",
            name="FLUID FLOW",
            description=(
                "El fluido sale del reservorio hacia el pozo, entra por la admisión, "
                "la bomba lo impulsa y sube por el tubing hasta superficie. "
                "No se calculan caudal ni presión."
            ),
            steps=[
                FlowStep(order=index, component_id=component_id, label=fluid_labels[component_id])
                for index, component_id in enumerate(FLUID_STEP_IDS, start=1)
            ],
        ),
    )


def assert_stage_1a(assembly: EspAssembly) -> None:
    """Traba de la etapa 1A. Una etapa futura debe relajarla de forma explícita."""

    ids = [component.id for component in assembly.components]
    if len(ids) != len(set(ids)):
        raise ValueError("Hay identificadores de componente duplicados.")
    orders = [component.display_order for component in assembly.components]
    if len(orders) != len(set(orders)):
        raise ValueError("Hay display_order duplicados.")

    known = set(ids)
    for component in assembly.components:
        unknown = [item for item in component.relations if item not in known]
        if unknown:
            raise ValueError(f"{component.id} referencia relaciones inexistentes: {unknown}")
        if any(value is not None for value in component.extensions.model_dump().values()):
            raise ValueError("Las extensiones deben permanecer vacías en la etapa 1A.")

    if assembly.capabilities.model_dump() != {
        "simulation": False,
        "physics_engine": False,
        "ai_model": False,
        "control": False,
    }:
        raise ValueError("Las capacidades avanzadas deben permanecer apagadas en la etapa 1A.")

    for flow, expected in (
        (assembly.flows.energy, ENERGY_STEP_IDS),
        (assembly.flows.fluid, FLUID_STEP_IDS),
    ):
        actual = tuple(step.component_id for step in flow.steps)
        if actual != expected:
            raise ValueError(f"El recorrido {flow.id} no coincide con el contrato de 1A.")
        orders = [step.order for step in flow.steps]
        if orders != list(range(1, len(orders) + 1)):
            raise ValueError(f"El recorrido {flow.id} no está numerado en secuencia.")


def get_assembly() -> EspAssembly:
    assembly = EspAssembly(
        id="esp-educational-1a",
        name="Conjunto ESP educativo",
        stage=STAGE,
        stage_label="1A — Anatomy",
        mode="educational",
        disclaimer=(
            "Educational / Simulation Environment. "
            "Esta aplicación no está preparada para controlar una ESP real."
        ),
        capabilities=Capabilities(),
        components=sorted(build_components(), key=lambda item: item.display_order),
        flows=build_flows(),
    )
    assert_stage_1a(assembly)
    return assembly
