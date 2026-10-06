# Etapa 2-0 — Baseline y gobernanza de datos

Nota de la etapa 2-1: este documento conserva el cierre de 2-0. La etapa global vigente es 2-1. El modelo físico sigue siendo `hydraulics-v0.1`.

## 1. Objetivo

Congelar la fase 1 como baseline funcional y empezar la fase 2 observando una fuente experimental, sin entrenar modelos ni reinterpretar columnas.

## 2. Alcance

Entra el versionado del proyecto, la gobernanza de `data/`, la lectura de los libros en `esp-core`, la ingesta de datasets nuevos en la aplicación de escritorio y la vista `/research/`. No entra aprendizaje automático, Physics-AI, detección de anomalías, un modelo con gas ni un cambio de `hydraulics-v0.1`. El código móvil existe y no se modifica en esta pasada: el trabajo pendiente está en [mobile-ingestion-pending.md](mobile-ingestion-pending.md).

## 3. Baseline heredado

La fase 1 queda completada:

| Etapa | Capacidad | Dónde sigue |
| --- | --- | --- |
| 1A | Anatomía | `/` y `/api/v1/esp` |
| 1B | Bomba multietapa | `/pump/` |
| 1C | Hidráulica básica | `/physics/` con `hydraulics-v0.1` |
| 1D | Curvas | `/curves/` |
| 1E | Motor | explicación en `/pump/` |
| 1F | VSD/VFD | frecuencia de estudio |

Esas etiquetas nombran la capacidad. La etapa global del proyecto pasa a ser 2-0. `hydraulics-v0.1` sigue siendo el modelo monofásico estático heredado de 1C. El documento histórico de la página Acerca de sigue en `docs/stage-1c1-about.md`. El panel de estado ya no muestra esa etiqueta de créditos.

## 4. Por qué hace falta gobernanza

Sin un manifiesto y una política de solo lectura, un perfil o un modelo posterior puede alterar la fuente y volver irreproducible el resultado. La etapa 2-0 separa el archivo recibido del cálculo que lo describe.

## 5. Dataset incorporado

Dataset 001, fuente experimental externa:

- Autor: Jianjun Zhu.
- Título: Modeling Flow Pattern Transitions in Electrical Submersible Pump under Gassy Flow Conditions.
- DOI del dataset: 10.17632/fk2b4r69bs.1.
- DOI del artículo: 10.1016/j.petrol.2019.05.059.
- Archivos, con el nombre original: `Mapping Test Data_zero IPA.xlsx` y `Surging Test Data_zero IPA.xlsx`.

La fecha de publicación no está escrita en los libros y no se infiere del sistema de archivos.

## 6. Arquitectura

```text
DATASET 001
    │
XLSX RAW, solo lectura
    │
research loader
    │
data profiling
    │
esp-core  /api/v1/research
    │
esp-web   /research/
```

El camino de la fase 1 permanece aparte:

```text
esp-web → esp-core → physics/hydraulics-v0.1
```

`app/research/` no importa las ecuaciones. `app/physics/` no lee los libros.

## 7. Flujo de datos

`esp-core` lee `ESP_DATA_ROOT` (en el contenedor, `/app/data`). Compose monta `./data` solo en ese servicio. El montaje es escribible para que la ingesta pueda copiar un archivo nuevo. La inmutabilidad del RAW no depende de `:ro`: el código copia el archivo y no lo abre para escribir. En Fedora el sufijo SELinux sigue siendo `Z`. `esp-web` no monta `data/` y no perfila libros. El navegador pide una muestra de como máximo 50 filas. El tope de carga es `ESP_DATA_MAX_UPLOAD_MB` (32 por defecto).

## 8. Endpoints

| Método | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/v1/health` | Sigue respondiendo. Agrega `phase`, `foundation_stage` y `research` |
| GET | `/api/v1/research/status` | Investigación activa, IA apagada, datasets presentes o `dataset_unavailable` |
| GET | `/api/v1/research/datasets` | Índice |
| GET | `/api/v1/research/datasets/001` | Metadatos, procedencia, hojas y encabezados |
| GET | `/api/v1/research/datasets/001/profile` | Estadísticas por bloque y columna |
| GET | `/api/v1/research/datasets/001/preview` | Muestra acotada. Exige el nombre exacto del archivo |
| POST | `/api/v1/research/intake` | Analiza archivos sin crear un dataset |
| GET | `/api/v1/research/intake/{id}` | Revisión previa |
| POST | `/api/v1/research/intake/{id}/cancel` | Descarta la revisión |
| POST | `/api/v1/research/datasets/import` | Copia el RAW, escribe manifest y preprocess |
| GET | `/api/v1/research/datasets/{id}/manifest` | Identidad, hash y procedencia |
| GET | `/api/v1/research/datasets/{id}/preprocess` | Estructura descubierta |
| POST | `/api/v1/research/datasets/{id}/reprofile` | Regenera preprocess.json sin tocar el RAW |

## 9. Raw y processed

`data/001/` es crudo y sigue en esa ruta. No se duplica dentro de `datasets/001/raw/`. La metadata nueva del mismo dataset vive en `data/datasets/001/metadata/`. `data/processed/` queda vacío. `data/reports/001/` guarda `profile.json` y `schema.json`, derivados anteriores. El perfil que sirve `GET .../profile` se calcula al leer. `preprocess.json` es la instantánea estructural de la ingesta.

## Dataset ingestion architecture

La aplicación de escritorio y la aplicación móvil son entidades separadas. Comparten el contrato de [dataset-contract.md](dataset-contract.md). No comparten disco ni se consultan en ejecución.

```text
WEB
External Source
      ↓
File Picker
      ↓
Import Validation
      ↓
RAW
      ↓
Manifest
      ↓
Structural Profiler
      ↓
Preprocess JSON
      ↓
Dataset Registry

MOBILE  (pendiente; el fuente existe y no se implementa en esta pasada)
Document Provider
      ↓
Android File Picker
      ↓
Private RAW Copy
      ↓
Manifest
      ↓
Structural Profiler
      ↓
Preprocess JSON
      ↓
Mobile Dataset Registry
```

El escritorio pide el archivo con el selector del navegador. Seleccionar no importa. El orden de la pantalla es Seleccionar archivos, Analizar, Importar. Analizar deja el archivo en `data/inbox/` y devuelve nombre, tamaño, tipo, SHA-256, estado y advertencias. Importar asigna el identificador, copia el RAW y escribe los JSON.

```text
data/                         el dataset 001 publicado sí entra a git; inbox e importaciones nuevas no
    001/
    datasets/
        001/metadata/             manifest.json y preprocess.json
        001/derived/
        NNN/raw/
        NNN/metadata/
        NNN/derived/
    inbox/
    reports/
```

El registro lee `data/datasets/*/metadata/manifest.json`. Si el 001 todavía no tiene ese manifiesto, reconoce los dos libros de `data/001/` para no perderlos. Un directorio incompleto, oculto o con JSON inválido se informa y no tumba el servicio.

Los loaders dependen del formato, no del dataset: `ExcelLoader`, `CsvLoader`, `TsvLoader`, `JsonLoader` y `TextLoader`. El dataset 001 usa el mismo `ExcelLoader` que un Excel posterior. No hay `Dataset001Loader`.

`manifest.json` responde qué archivo es, de dónde vino, cuándo se registró y cuál es su hash. `preprocess.json` responde cómo está organizado. Los dos llevan `schema_version` `1.0`. El profiler se identifica como `esp-structural-profiler` `0.1`, con `generated_at` y `generated_from_sha256`. Reanalizar vuelve a escribir solo el preprocess.

Un valor que no se conoce queda en `null`. No se escribe `unknown` salvo en `distribution`, cuyo valor inicial de una importación es `unknown` (`public`, `private` o `unknown`). El dataset 001 queda `public` porque su fuente tiene DOI. Los libros, el manifiesto, el preprocess y el mapping de 001 están en el repositorio, en las mismas carpetas. El inbox y las copias RAW de una importación nueva siguen fuera de git. Su licencia no está en los libros y sigue en `null`.

El encabezado se guarda como `raw_name`. Una forma `flow_rate` es solo para identificar el texto. `canonical_variable` queda en `null` y `mapping_status` en `pending`. `semantic_mapping.status` queda en `not_started`. Una unidad se anota solo si el encabezado la escribe entre paréntesis. No se convierten unidades.

SHA-256 repetido no crea otra copia. La respuesta dice que el archivo ya existe en un dataset y la importación espera cancelar o vincular. El vínculo guarda `linked_from` y no duplica bytes.

`.gitignore` deja fuera el inbox, el lock de datasets y `datasets/*/raw/`. El dataset 001 publicado no está ignorado. El móvil no debe llevar esos RAW dentro del APK.

Estados de esta etapa: `selected`, `validated`, `imported`, `profiled`, `ready_for_mapping`, `error`. No se usan `trained`, `predicted` ni `classified`.

## 10. Procedencia

Las procedencias que el modelo físico produce siguen siendo `user_input`, `physics_model` y `constant`. Siguen reservadas `sensor`, `simulation`, `ml` y `physics_ai`. Se agrega `experimental`: una medición de ensayo o banco. No es un sensor de pozo, ni una simulación, ni un modelo de aprendizaje, ni Physics-AI. `hydraulics-v0.1` no la produce.

## 11. Reproducibilidad

El manifiesto guarda tamaño y SHA-256. El perfil y el esquema guardan `generated_from`, `source_sha256`, `generated_at` y `tool_version` (`research-profile-2-0`). Volver a leer el mismo libro produce el mismo hash. La fecha de análisis cambia porque es la de la ejecución.

## 12. Integridad

Un libro que no abre responde `unreadable_workbook` (HTTP 422). Un nombre de archivo distinto del catálogo responde `unknown_file` y no se resuelve como ruta. Si falta `ESP_DATA_ROOT` o el dataset, el núcleo sigue en pie: la salud responde y la investigación informa `dataset_unavailable`.

## 13. Lo que se observó sin interpretarlo

Cada hoja se llama `50psig`, `100psig` y `150psig` en los dos libros. Dentro de una hoja hay más de un bloque: una fila en blanco y otro par de encabezados separan regiones. Esos bloques no se fusionan ni se rellenan.

La única unidad escrita entre paréntesis en un encabezado es `rpm`, en el texto `Rotary Speed (rpm)`. El resto de las unidades queda en null. Los nombres repetidos (`Flow rate`, `DP2-3`, `GVF0`) se conservan y se marcan como duplicados. En varias columnas de velocidad las celdas de datos están vacías: el número aparece en la fila de encabezado del bloque y no se copia hacia abajo.

## 14. Limitaciones

No hay entrenamiento, ni predicción, ni corrección de head por gas, ni modelo multifásico. La pantalla no dice que una columna sea una magnitud física si el encabezado no lo escribe. La aplicación sigue siendo un entorno educativo y de investigación. La fase 2, en esta etapa, no controla una ESP real ni ofrece un diagnóstico operativo.

La etiqueta de imagen es `2-0`. El esquema de etiquetas OCI admite el guion (`[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}`), así que no hizo falta usar `2.0` ni `phase2-0`.

## 15. Tareas siguientes

La etapa 2-1 puede auditar variables y proponer un mapa. No empieza hasta revisar esta etapa. El detalle está en [phase-2-roadmap.md](phase-2-roadmap.md).

## 16. Criterios de aceptación

- La fase 1 queda documentada como baseline completado y sus rutas siguen respondiendo.
- El proyecto informa fase 2 y etapa 2-0, con baseline 1F y modelo `hydraulics-v0.1`.
- Las referencias históricas 1A–1F y `1C.1` se conservan.
- Los dos libros se detectan, su SHA-256 es estable y el perfil no los modifica.
- `/research/` muestra el gestor de datos, el estado, los archivos y una muestra por hoja.
- Un dataset nuevo se importa sin tocar el RAW y aparece en el registro.
- Si los datos no están, la web avisa y no responde HTTP 500.
- No hay un módulo de aprendizaje ni de Physics-AI.
- El mapeo semántico permanece en `not_started`.
- La app móvil no recibió un file manager en esta pasada. El pendiente está escrito.
