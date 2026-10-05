# Etapa 1A — Anatomía y principio de funcionamiento de una ESP

## Objetivo

Esta etapa construye el primer entregable visual del ESP Digital Twin y el vocabulario compartido del proyecto.

Al terminarla se debe poder explicar, sin números de operación:

1. Qué es una ESP (Electrical Submersible Pump, bomba electrosumergible).
2. Para qué se utiliza.
3. Dónde queda dentro de un pozo.
4. Cuáles son sus componentes principales.
5. Cómo se relacionan.
6. Cuál es el recorrido básico de la energía.
7. Cuál es el recorrido básico del fluido.

Una ESP es un sistema de levantamiento artificial. Se instala dentro del pozo, por debajo del nivel del fluido, y eleva ese fluido hasta la superficie. Se usa cuando el pozo no entrega por sí solo el caudal que se necesita en superficie. El conjunto de fondo cuelga de la tubería de producción; la energía eléctrica se genera y acondiciona arriba, y baja por un cable hasta un motor situado en el extremo inferior.

Esta etapa no calcula si el conjunto puede levantar el fluido. Solo fija la anatomía sobre la que después se apoyarán la hidráulica, el motor, el variador y el control.

## Anatomía de la ESP

El orden físico del conjunto de fondo, de abajo hacia arriba, es: motor, protector, admisión, bomba y, por encima, el tubing. El cable no entra a la bomba: llega al motor.

### Power Supply

Alimentación eléctrica en superficie. Es el origen del recorrido energético. En esta etapa no representa un tablero, una tensión ni un generador concretos.

### VSD/VFD

Variador de velocidad (Variable Speed Drive) o variador de frecuencia (Variable Frequency Drive). Está entre la alimentación y el cable. Más adelante se estudiará cómo la frecuencia cambia la velocidad del motor. Aquí solo ocupa su lugar en la cadena: acondiciona la energía que viajará al fondo. No hay mando de frecuencia.

### Cable

Cable de potencia. Baja por el espacio entre el revestimiento del pozo y el tubing, y termina en el motor. Separa dos ideas que conviene no mezclar: la energía eléctrica viaja por el cable; el fluido viaja por dentro del tubing.

### Motor

Motor eléctrico de fondo, en la parte más baja del conjunto. Transforma la energía eléctrica en rotación del eje. Acciona la bomba, pero no lo hace por un cable conectado a la bomba, sino por el eje común.

### Protector

También llamado seal section. Está entre el motor y la admisión. Aísla el motor —que lleva su propio fluido dieléctrico— del fluido del pozo, y deja pasar el eje hacia arriba. No se calculan presiones ni volúmenes de aceite.

### Intake

Admisión. Por aquí el fluido que está en el pozo entra al conjunto, antes de la bomba. El eje la atraviesa, pero su papel en el recorrido del fluido es ser la puerta de entrada.

### Pump

Bomba centrífuga de varias etapas, en la parte superior del conjunto de fondo. Recibe la rotación del eje y empuja el fluido hacia el tubing. Decir “multietapa” describe la clase de máquina; no fija un número de etapas ni una curva.

### Tubing

Tubería de producción. Cuelga desde el cabezal y lleva el fluido desde la descarga de la bomba hasta la superficie. No se elige un diámetro ni se calcula fricción.

### Well

El pozo es el conducto que contiene todo lo anterior. El cabezal (wellhead) marca el límite con la superficie. El esquema lo muestra como referencia visual del pozo, no como un equipo distinto del catálogo.

### Reservoir

El reservorio es el origen conceptual del fluido. No hay modelo de yacimiento, presión de formación ni índice de productividad.

### Surface

La superficie agrupa lo que queda fuera del pozo: alimentación, variador y llegada del fluido producido. El flujo de producción no es un equipo; es el tramo conceptual en el que el fluido ya elevado pasa a las instalaciones de superficie.

## Flujo energético

```text
Alimentación eléctrica
        ↓
      VSD / VFD
        ↓
   Cable eléctrico
        ↓
   Motor eléctrico
        ↓
  Rotación mecánica (eje)
        ↓
       Bomba
```

La energía entra como electricidad en superficie, baja por el cable y se convierte en movimiento en el motor. El eje lleva ese movimiento a través del protector y la admisión hasta la bomba. La bomba es el punto en el que ese movimiento pasa a actuar sobre el fluido.

No hay potencia, corriente, voltaje, par ni velocidad. El impulsor del esquema gira solo cuando se activa el recorrido, para señalar la idea de rotación. No representa una velocidad real.

## Flujo del fluido

```text
Reservorio
    ↓
   Pozo
    ↓
 Admisión
    ↓
  Bomba
    ↓
  Tubing
    ↓
Superficie
```

El fluido sale de la formación al interior del pozo, entra por la admisión, la bomba lo impulsa y sube por el tubing hasta el cabezal. En el esquema, el tramo inferior de ese recorrido va por el espacio anular —por fuera del motor— hasta la admisión, y solo después ocupa el centro de la bomba y del tubing. Así se ve que el motor no “traga” el fluido de producción.

No hay caudal, presión ni pérdidas.

## Conceptos que todavía no estamos estudiando

Estas ideas aparecen en el roadmap y se incorporarán en etapas posteriores. No forman parte del modelo ni de la interfaz de 1A:

- Head, o altura de energía que entrega la bomba
- Curvas H-Q (altura frente a caudal)
- BEP (Best Efficiency Point, punto de mejor eficiencia)
- Eficiencia
- Presión diferencial
- Leyes de afinidad
- Cavitación
- Interferencia por gas (gas interference)
- Anomalías de operación
- Machine learning
- PINN (Physics-Informed Neural Networks) u otros modelos Physics-AI

Tampoco hay arranque, parada ni consigna de frecuencia. El panel de control reserva esos mandos y los marca como etapa futura. Pulsarlos no hace nada: están deshabilitados.

## Qué debe quedar verdadero en pantalla

- El entorno es educativo. No sirve para operar una ESP instalada.
- Simulación, motor físico y modelo de IA figuran como no habilitados.
- El texto de cada componente sale de `GET /api/v1/esp`, no de una segunda definición en Django.
