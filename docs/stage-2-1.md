# Etapa 2-1 — Auditoría del dataset y mapeo de variables

Etapa vigente. No es un motor físico nuevo. `PHYSICS_MODEL` sigue en `hydraulics-v0.1` y `PHYSICS_MODE` en `static`. `PROJECT_STAGE` y `RESEARCH_STAGE` son `2-1`. `FOUNDATION_STAGE` sigue en `1F`.

## 1. Objetivo

Decir qué significa cada columna del dataset y con qué variable física de la ESP puede relacionarse. La cadena exigida es:

```text
RAW COLUMN → EVIDENCE → PHYSICAL VARIABLE → UNIT → CANONICAL VARIABLE
```

Si la evidencia no alcanza, `canonical` queda en null y el estado es `unmapped`.

## 2. Alcance

Entra el catálogo canónico, `mapping.json` del dataset 001, la cobertura, la API aditiva y la revisión en `/research/`. No entra Android, un APK, Machine Learning, Physics-AI, detección de anomalías, datos sintéticos, limpieza, outliers, interpolación, relleno, conversión de RAW ni un cambio de `hydraulics-v0.1`. No se ejecuta ninguna variable derivada.

## 3. Diferencia entre 2-0 y 2-1

2-0 respondió qué archivos hay, de dónde vienen, si están íntegros y cómo están organizados. Eso sigue en `manifest.json` y `preprocess.json`. 2-1 responde el significado. `preprocess.json` no se convierte en archivo semántico y conserva `semantic_mapping.status = not_started`.

```text
RAW
 ├── manifest.json     identidad y procedencia
 ├── preprocess.json   estructura técnica
 └── mapping.json      semántica física
```

## 4. Registro canónico

Vive en `services/esp-core/app/research/variables.py`. No depende del dataset 001. Cada definición trae id, símbolo, cantidad, unidad SI y, cuando corresponde, ubicación de referencia o unidad de presentación. La ubicación de referencia no se copia a una columna experimental: esa columna queda en `unknown` hasta que haya evidencia del punto.

| id | símbolo | unidad SI |
| --- | --- | --- |
| intake_pressure | P_int | Pa |
| flowing_bottomhole_pressure | P_wf | Pa |
| liquid_flow_rate | Q_L | m3/s |
| gas_flow_rate | Q_G | m3/s |
| dynamic_fluid_level | h_D | m |
| gas_volume_fraction | GVF | 1 |
| pump_head | H | m |
| pump_pressure_difference | ΔP | Pa |
| hydraulic_power | P_hyd | W |
| shaft_power | P_shaft | W |
| electrical_power | P_el | W |
| rotary_speed | N | rad/s (presentación rpm) |
| frequency | f | Hz |
| liquid_density | ρ_L | kg/m3 |

No hay una potencia genérica `P`. `P_hyd`, `P_shaft` y `P_el` son distintas. `pump_pressure_difference` exige que los dos puntos estén identificados. El rango 0–1 de GVF es documentación; no se usa para alterar datos ni para reconocer una columna.

## 5. mapping.json

Para el dataset 001 está en `data/datasets/001/metadata/mapping.json`. El RAW sigue en `data/001/`. El archivo trae `schema_version` 1.0, `mapping_version` 0.1, `dataset_id`, fechas, `status`, `variables`, `unmapped_columns`, `missing_expected_variables`, `evidence_sources`, `review_notes`, `coverage` y `derivable_relations`.

Las columnas con el mismo nombre y la misma unidad forman una firma. Cada ocurrencia conserva archivo, hoja, bloque, índice, `column_ref`, ejemplo y mínimo/máximo cuando el perfil los tiene. `column_ref` tiene la forma `001/{archivo}/{hoja}/{bloque}/c{índice}/{nombre}`. El id estable de la firma usa el nombre y la unidad, no solo el índice.

## 6. Estados

`unmapped`, `candidate`, `reviewed`, `validated`, `rejected`, `not_applicable`.

Una sugerencia determinista nunca escribe `validated`. Validar o rechazar es una revisión que entra por la API o por el formulario, con evidencia. El mapping inicial del dataset 001 no tiene filas `validated` ni `rejected`.

## 7. Evidencia

Tipos admitidos: `explicit_header`, `explicit_unit`, `dataset_documentation`, `article`, `figure`, `table`, `manual_research_review`, `derived_relationship`. Cada pieza guarda `type` y `value`. Las fuentes están en `evidence_sources`:

- E001, dataset Mendeley, DOI `10.17632/fk2b4r69bs.1`. Se cita cuando el encabezado del libro es la evidencia.
- E002, artículo, DOI `10.1016/j.petrol.2019.05.059`. Queda listado con `used: false` porque el texto del artículo no está en el repositorio y no se usa para nombrar una columna.

## 8. Confianza

`high`, `medium` o `low`, separada del estado. `Rotary Speed (rpm)` puede ser `candidate` con confianza `high` porque el nombre y la unidad están escritos. `rotary speed` sin unidad es `candidate` con confianza `medium`. Una columna `unmapped` no recibe confianza.

## 9. Unidades

2-1 identifica `raw_unit` y, solo si hay variable canónica, la unidad SI del catálogo. No convierte el RAW y no crea una tabla convertida. Si la unidad no está escrita, `raw_unit` es null. Un rango numérico no deduce la unidad.

## 10. Ubicaciones

`pump_intake`, `pump_discharge`, `downhole`, `surface`, `pump`, `test_loop`, `unknown`. Las columnas del dataset 001 quedan en `unknown`. Los nombres de hoja `50psig`, `100psig` y `150psig` no son columnas. Indican una presión en psig cuyo punto no está identificado, y no crean una variable de presión.

## 11. Cobertura

`coverage` vive dentro de `mapping.json` y también en `GET .../mapping/coverage`. Cuenta firmas, ocurrencias y estados. Una variable objetivo está presente si alguna firma en `candidate`, `reviewed` o `validated` la nombra. Está mapeada si el estado es `reviewed` o `validated`. Está validada solo en `validated`. No se inventa una columna para completar la matriz.

## 12. Linaje

Cada documento guarda la versión de esquema del preprocess, la versión de esquema del mapping y el SHA-256 de cada RAW. Cada ocurrencia repite `source_sha256`. Una revisión incrementa `revision` y agrega una entrada en `history`. No hay base de datos.

## 13. Reglas para evitar inferencias

- `Pressure` fija la familia `pressure` y deja la variable canónica en null.
- `Power` fija la familia `power` y no elige `P_hyd`, `P_shaft` ni `P_el`.
- `Rotary Speed (rpm)` sugiere `rotary_speed` como `candidate`.
- `rotary speed` sin unidad sugiere lo mismo con confianza media y `raw_unit` null.
- `Flow rate` fija la familia `flow` y no elige `Q_L` ni `Q_G`.
- `DP2-3` queda `unmapped`. Los rótulos de celdas combinadas no identifican los puntos 2 y 3.
- `GVF0` queda `unmapped`. El sufijo no está definido y no hay unidad.
- Un valor entre 0 y 1 no produce GVF.
- `Qgd=…`, `Single Phase`, `0.75Qbep`, `Qbep` y `1.25Qbep` son rótulos de grupo, no columnas medidas.

## 14. API

Bajo `/api/v1/research/`, sin cambiar las rutas de 2-0:

- `GET /variables`
- `GET /datasets/{id}/mapping`
- `GET /datasets/{id}/mapping/coverage`
- `POST /datasets/{id}/mapping`
- `PATCH /datasets/{id}/mapping/{mapping_id}`

Una variable canónica desconocida, un estado desconocido o una confianza desconocida responden 422. `validated` y `rejected` exigen variable y evidencia. `unmapped` y `not_applicable` no aceptan una variable canónica.

## 15. Interfaz

`/research/` agrega la sección «Mapeo de variables» en la misma aplicación. Muestra dataset, cobertura, firmas y, al elegir una firma, archivo, hoja, bloque, columna, nombre, unidad, tipo, ejemplo, mínimo y máximo, ocurrencias, variable, símbolo, unidad SI, estado, confianza, evidencia y notas. El formulario pide variable, evidencia y confianza, y escribe el mapping solo al guardar.

## 16. Resultados del dataset 001

Seis firmas y 144 ocurrencias. Dos libros: `Mapping Test Data_zero IPA.xlsx` y `Surging Test Data_zero IPA.xlsx`. Hojas `50psig`, `100psig` y `150psig`.

| Firma | Estado | Confianza | Canónica | Unidad RAW | Dónde |
| --- | --- | --- | --- | --- | --- |
| columna vacía | not_applicable | — | — | — | solo Mapping, 24 ocurrencias |
| DP2-3 | unmapped | — | — | null | ambos libros, 48 ocurrencias |
| Flow rate | unmapped | — | familia flow | null | solo Mapping, 30 ocurrencias |
| GVF0 | unmapped | — | — | null | solo Surging, 18 ocurrencias |
| rotary speed | candidate | medium | rotary_speed | null | solo Mapping, 6 ocurrencias |
| Rotary Speed (rpm) | candidate | high | rotary_speed | rpm | solo Surging, 18 ocurrencias |

En Mapping aparecen `rotary speed`, `Flow rate` y `DP2-3`. En Surging aparecen `Rotary Speed (rpm)`, `GVF0` y `DP2-3`. En ambos aparece solo `DP2-3`, todavía sin interpretación. No hay filas `validated` ni `rejected`.

`Rotary Speed (rpm)` es una condición: 1800 rpm y 3500 rpm están en el encabezado y el cuerpo de la columna está vacío. Sigue en `candidate` con confianza `high`. `GVF0` y `DP2-3` son series medidas. Su pista RAW no las identifica.

La estructura contada desde el preprocess y el mapping es 2 archivos, 6 hojas, 12 bloques, 6 firmas y 144 ocurrencias.

## 17. Evidencia RAW y variables objetivo

Una pista no es un mapping. La cobertura separa el texto encontrado del estado canónico.

| Variable | Evidencia RAW | Estado |
| --- | --- | --- |
| rotary_speed | Rotary Speed (rpm), rotary speed | candidate, no validada |
| gas_volume_fraction | GVF0 | needs_evidence |
| liquid_flow_rate | Flow rate | needs_evidence |
| gas_flow_rate | Flow rate | needs_evidence |
| pump_pressure_difference | DP2-3 | needs_evidence |
| intake_pressure, P_wf, h_D, H, P_hyd, P_shaft, P_el, f, ρ_L | ninguna | not_found |

Las hojas `50psig`, `100psig` y `150psig` son condiciones de presión observadas. No se asignan a `P_int`, `P_wf` ni a una descarga. No se convierten a Pa.

`0.75Qbep`, `Qbep` y `1.25Qbep` siguen como rótulos. La lectura «porcentaje del caudal de mejor eficiencia» queda en hipótesis: el valor de Qbep no está en los libros.

## 18. Limitaciones

El artículo E002 no está en el repositorio, así que no respalda ninguna columna. Las celdas combinadas cubren visualmente a `DP2-3` y a `Flow rate`, pero el rótulo no define los puntos 2 y 3 ni la fase del caudal. `Qgd` es un rótulo de condición, no una serie medida. La velocidad de rotación de Surging está en la fila de encabezado (1800 y 3500) y el cuerpo de esa columna está vacío: es una condición de ensayo, no una serie. Los libros, el manifiesto, el preprocess y `mapping.json` del dataset 001 están en el repositorio, en `data/`. No hay conversión de unidades ni cálculo derivado.

Relaciones registradas con `calculation_status = not_executed` e `inputs_available = false`:

- `GVF = Q_G / (Q_G + Q_L)`
- `H = ΔP / (ρ g)`
- `P_hyd = Q ΔP`
- `P_hyd = ρ g Q H`

## 19. stage-2-1-results.json

El resumen derivado está en `data/datasets/001/metadata/stage-2-1-results.json`. Lo construye solo `build_stage_results()`. Se reescribe al guardar un mapping, al crear un mapping y al reanalizar. Si el mapping, el preprocess o los SHA cambian y el archivo no se regeneró, `is_stale()` lo detecta. Borrarlo no pierde el RAW ni el mapping: se reconstruye.

La interfaz y ese JSON usan `annotate_mapping()` y `coverage_of()`. `GET /api/v1/research/datasets/{id}/stage-2-1-results` devuelve el snapshot. En `/research/` el enlace «Descargar respaldo técnico» queda debajo de las preguntas.

La factibilidad dice si el dataset alcanza para estudiar un problema. `potentially_feasible` se muestra como «Potencialmente estudiable» y no crea un modelo. En el dataset 001, surging queda en ese estado porque el libro, las velocidades y los grupos están observados. La degradación hidráulica y la respuesta de presión quedan en `needs_mapping`. `P_wf`, el nivel dinámico, la admisión y la detección de anomalías quedan en `needs_additional_dataset`.

## 20. Criterio de cierre

2-1 puede cerrarse cuando el dataset 001 tenga `mapping.json`, el catálogo exista, cada mapping tenga evidencia o quede explícitamente sin interpretación, el estado y la confianza estén separados, las unidades RAW se conserven, la unidad SI aparezca solo con variable canónica, las presiones y las potencias no se confundan por el nombre, las ausencias estén explícitas, el RAW y la física 1C no cambien, no haya ML ni Physics-AI ni un cálculo derivado ejecutado, la interfaz permita revisar, la cobertura esté disponible, la documentación esté actualizada y las pruebas pasen. El cierre formal de la etapa queda para una revisión posterior. Esta pasada la deja en curso, con el mapeo inicial sin validaciones automáticas.

2-1 sigue en curso. Falta evidencia externa para cerrar `DP2-3`, `GVF0`, la unidad y la fase de `Flow rate`, el punto de las hojas en psig y el valor de Qbep. Hasta entonces ninguna de esas columnas pasa a `validated`.

## 21. Siguiente etapa 2-2

2-2 puede caracterizar los ensayos ya descritos, sin corregirlos y sin ejecutar las relaciones derivadas. 2-2 no está iniciada.
