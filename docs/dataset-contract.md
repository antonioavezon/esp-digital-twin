# Contrato de datasets — etapa 2-0

Este contrato no depende de Web, Android, Linux, Windows ni de una ruta absoluta. Las dos aplicaciones pueden implementarlo por separado. No hay una biblioteca compartida en ejecución.

Identificador: `001`, `002`, `003`, … El `001` ya publicado no se renombra. El identificador no es el nombre del archivo ni una ruta.

## Dataset

Identidad del conjunto: `dataset_id`, título, estado y distribución (`public`, `private`, `unknown`).

## DatasetFile

Un archivo dentro del dataset. Conserva `original_filename`, `stored_filename`, `relative_path`, `format`, `size_bytes`, `sha256`, `imported_at` y, si no se copió de nuevo, `linked_from`.

## DatasetManifest

`manifest.json`. Responde qué archivo es, de dónde vino y si es el mismo. Lleva `schema_version` `1.0`. Los datos desconocidos van en `null`.

## StructuralProfile

Descripción de la forma: hojas o tabla o JSON, bloques, encabezados, tipos primitivos, vacíos, fórmulas contadas y no evaluadas. No asigna una variable física.

## PreprocessManifest

`preprocess.json`. Responde cómo está organizado el archivo. Incluye el perfil, `profiler.name` `esp-structural-profiler`, `profiler.version` `0.1`, `generated_at`, `generated_from_sha256` y `semantic_mapping.status` = `not_started`.

## Estados

`selected`, `validated`, `imported`, `profiled`, `ready_for_mapping`, `error`.

No forman parte de 2-0: `trained`, `predicted`, `classified`.

## Loaders

El loader se elige por el formato del archivo:

- `ExcelLoader` para `.xlsx` y `.xlsm`
- `CsvLoader`
- `TsvLoader`
- `JsonLoader`
- `TextLoader` para `.txt`

No se crea un loader por dataset.
