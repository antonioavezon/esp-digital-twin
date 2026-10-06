# Fase 2 — Research / Physics-AI

La fase 1 (1A–1F) queda cerrada como baseline funcional. La etapa 2-0 queda cerrada. Esta fase observa datos experimentales y, más adelante, los contrasta con el modelo físico. Solo la etapa 2-1 está en curso. Las siguientes se describen para no mezclar su alcance con el trabajo actual.

El pipeline previsto, todavía sin implementar, es:

```text
Datos experimentales
        │
        ▼
Mapeo de variables
        │
        ▼
Baseline físico
        │
        ├──────────────────┐
        ▼                  ▼
Baseline de ML     Restricciones físicas
        │                  │
        └────────┬─────────┘
                 ▼
             Physics-AI
                 │
                 ▼
        Sensores virtuales
                 │
                 ▼
       Detección de anomalías
```

## 2-0 — Baseline & Data Governance

Estado: completada.

- Objetivo: congelar el baseline 1A–1F, separar la etapa global del modelo físico y dejar el dataset 001 como fuente cruda observable.
- Entrada: el repositorio de la fase 1 y los dos libros originales del dataset 001.
- Salida: salud del proyecto con baseline 1F, manifiesto con SHA-256, perfil estructural (`preprocess.json`), registro de datasets e importación desde `/research/`.
- Cierre: la fase 1 sigue operable, los libros no cambian, no hay un modelo de IA y las pruebas de 2-0 siguen pasando. La app móvil tiene el mismo contrato documentado y su file manager sigue pendiente.

## 2-1 — Dataset Audit & Variable Mapping

Estado: en curso.

- Objetivo: decir qué significa cada columna y con qué variable física de la ESP puede relacionarse, solo con evidencia.
- Entrada: el perfil 2-0, los encabezados reales y la documentación incorporada al proyecto.
- Salida: `mapping.json`, catálogo canónico, cobertura, condiciones de encabezado y `stage-2-1-results.json`. `preprocess.json` sigue siendo estructural.
- Cierre previsto: ninguna columna queda validada por conjetura, las variables objetivo ausentes están explícitas y no se ejecuta un cálculo derivado. El detalle está en [stage-2-1.md](stage-2-1.md).

## 2-2 — Experimental Characterization

Estado: no iniciada.

- Objetivo: describir los ensayos observados: bloques, rangos y huecos, sin corregirlos.
- Entrada: el mapa 2-1 y los libros crudos.
- Salida esperada: una caracterización reproducible de cada bloque.
- Cierre: los resultados se pueden recalcular desde el SHA-256 de la fuente.

## 2-3 — Physics Baseline under Gassy Flow

Estado: no iniciada.

- Objetivo: calcular el baseline monofásico `hydraulics-v0.1` en los puntos experimentales donde el mapa lo permita, y registrar la diferencia.
- Entrada: puntos ya mapeados y el motor actual, sin cambiar sus ecuaciones.
- Salida esperada: una comparación entre el cálculo monofásico y la medición.
- Cierre: la diferencia queda cuantificada y el modelo 0.1 no fue alterado.

## 2-4 — Gas-aware ESP Model

Estado: no iniciada.

- Objetivo: formular un modelo que reconozca la presencia de gas, como modelo nuevo y no como un parche silencioso de `hydraulics-v0.1`.
- Entrada: la diferencia medida en 2-3 y la bibliografía del artículo asociado.
- Salida esperada: ecuaciones, supuestos y límites explícitos.
- Cierre: el modelo nuevo declara qué no calcula y pasa una comparación con el baseline.

## 2-5 — Machine Learning Baseline

Estado: no iniciada.

- Objetivo: entrenar un baseline de aprendizaje sobre variables ya mapeadas.
- Entrada: la tabla caracterizada y el baseline físico.
- Salida esperada: un modelo de referencia con su partición de datos y su error.
- Cierre: el entrenamiento es reproducible y no se presenta como diagnóstico de campo.

## 2-6 — Hybrid Physics-AI Model

Estado: no iniciada.

- Objetivo: combinar el baseline físico y el baseline de aprendizaje, con las restricciones físicas a la vista.
- Entrada: las salidas de 2-4 y 2-5.
- Salida esperada: un modelo híbrido y la comparación contra ambos baselines.
- Cierre: se puede explicar qué parte viene de la física y qué parte de los datos.

## 2-7 — Sensorless Monitoring & Anomaly Detection

Estado: no iniciada.

- Objetivo: estudiar monitoreo sin sensores y detección de anomalías sobre el modelo híbrido.
- Entrada: el modelo 2-6 y las series experimentales.
- Salida esperada: una propuesta de sensores virtuales y de avisos, marcada como investigación.
- Cierre: ningún aviso se presenta como una alarma operativa validada.

## 2-8 — Validation, Results & Research Closure

Estado: no iniciada.

- Objetivo: cerrar la fase con los límites, los errores y lo que no quedó demostrado.
- Entrada: los resultados de 2-1 a 2-7.
- Salida esperada: un informe de validación y el estado de cada afirmación.
- Cierre: la fase distingue resultado medido, resultado calculado y resultado no alcanzado.
