# Etapa 1B — Bomba centrífuga multietapa

## Objetivo

La etapa 1A mostró el conjunto ESP y el lugar de la bomba. Esta etapa entra en ese componente y explica, de forma cualitativa, qué ocurre dentro de una bomba centrífuga de varias etapas.

Al terminarla se debe poder explicar:

1. Qué es una etapa.
2. Qué es un impulsor y qué es un difusor.
3. Cuál gira y cuál permanece fijo.
4. Qué función cumple cada uno.
5. Cómo entra el fluido, cómo atraviesa una etapa y cómo pasa a la siguiente.
6. Por qué una ESP usa varias etapas.
7. Cómo, en términos conceptuales, aumenta la capacidad de elevar el fluido.

No hay modelo matemático. No hay presiones, caudales ni velocidades reales.

## Bomba centrífuga ESP

En el conjunto de fondo, la bomba queda por encima de la admisión. El eje que sale del motor la atraviesa. Cada etapa toma fluido, le entrega energía mecánica a través del impulsor y lo conduce, ya guiado por el difusor, hacia la etapa siguiente. La descarga de la última etapa entrega el fluido al tubing.

La vista interna vive en `/pump/`. Se abre desde el esquema general, al seleccionar la bomba y seguir **Explore Pump Internals**. **Back to ESP Overview** vuelve al conjunto de la etapa 1A.

La jerarquía que muestra la interfaz es:

```text
ESP SYSTEM
    └── PUMP
          └── STAGES
                 ├── IMPELLER
                 └── DIFFUSER
```

## Stage

Una etapa es el par impulsor + difusor:

```text
1 etapa = impulsor + difusor.
```

```text
STAGE 1
 ├── Impeller
 └── Diffuser
```

Las etapas se encadenan:

```text
STAGE 1
    ↓
STAGE 2
    ↓
STAGE 3
    ↓
...
    ↓
STAGE N
```

La interfaz dibuja tres etapas. Esa cantidad es didáctica. Una ESP real puede tener muchas más, o menos, según el diseño y la aplicación. La pantalla lo dice de forma explícita: **Educational representation — real ESP stage count depends on design.**

## Impeller

El impulsor es la pieza que gira. La interfaz lo marca con la etiqueta **GIRA · ROTATING**, con álabes y con una animación de giro. Esa animación no es una velocidad de giro medida.

### Explicación simple

El impulsor gira y entrega energía al fluido.

### Explicación técnica

El impulsor es el elemento rotativo de la etapa centrífuga. Está unido al eje, recibe de él energía mecánica y la transfiere al fluido. El fluido entra cerca del centro y el giro lo dirige hacia la salida del impulsor, donde lo recoge el difusor.

## Diffuser

El difusor no gira. La interfaz lo marca con la etiqueta **FIJO · STATIONARY**, con álabes fijos y con un candado. No depende solo del color para distinguirlo del impulsor.

### Explicación simple

El difusor permanece fijo y guía el fluido hacia la siguiente etapa.

### Explicación técnica

El difusor es estacionario. Recibe el fluido que sale del impulsor y lo conduce hacia la entrada de la etapa siguiente. La transferencia de energía y la conversión entre formas de esa energía ocurren en el conjunto de la etapa, impulsor y difusor, no en una sola de las dos piezas.

## Flujo

Dentro de una etapa el recorrido conceptual es:

```text
Admisión
   ↓
Impulsor
   ↓
Difusor
   ↓
Etapa siguiente
```

En el conjunto de la bomba, la vista de tres etapas recorre:

```text
Admisión
   ↓
Etapa 1
   ↓
Etapa 2
   ↓
Etapa 3
   ↓
Descarga
```

**Show Fluid Path** dibuja ese paso con flechas. No representa la velocidad real del fluido. **Play** y **Pause** solo arrancan o detienen la animación del impulsor. La leyenda es **Conceptual animation — not physical RPM**. Esos botones no son el arranque ni la parada de una ESP.

**Step Through Pump**, con **Previous** y **Next**, y los botones de etapa 1, 2 y 3, permiten seguir el recorrido despacio. Al elegir una etapa se ven su entrada, el impulsor, el difusor, la salida y qué viene después.

## Multistage

Una sola etapa aporta energía, pero esa contribución es limitada para llevar el fluido desde el fondo hasta la superficie. Por eso la bomba de una ESP encadena etapas. Cada una repite el mismo esquema: un impulsor que gira con el eje y un difusor que permanece fijo y entrega el fluido a la etapa siguiente.

No hay un número universal de etapas. El diseño y la aplicación deciden cuántas hacen falta.

## Transferencia de energía

Cada etapa agrega energía al fluido. La interfaz lo muestra con una barra de bloques (`█`, `██`, `███`, `████`). La descarga repite el último tramo: no es una etapa más.

Esa barra lleva la leyenda **Conceptual energy representation**. No es presión, no es head y no es potencia. Las magnitudes numéricas viven en el motor de la etapa 1C (`/physics/`). Este documento de la bomba sigue sin incrustarlas: `quantitative_model` permanece en `null`.

## Qué todavía NO estamos calculando

Esta etapa no calcula ni muestra:

- presión diferencial;
- Head;
- caudal;
- velocidad real;
- potencia hidráulica;
- eficiencia;
- curvas H-Q;
- BEP;
- RPM;
- leyes de afinidad;
- cavitación;
- comportamiento multifásico.

Tampoco hay frecuencia de variador, control, sensores, alarmas ni modelos de aprendizaje automático. El panel de estado lo deja escrito: simulación conceptual, motor físico apagado, control en tiempo real apagado, modelo de IA apagado.
