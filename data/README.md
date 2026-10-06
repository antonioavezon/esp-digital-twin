# Datos de investigación

Este directorio guarda las fuentes experimentales del ESP Digital Twin y los derivados que se calculan a partir de ellas. No forma parte del motor `hydraulics-v0.1`.

## Raw y processed

- `001/` es la fuente cruda del dataset 001. Los libros `.xlsx` se leen y no se editan. Siguen en esta carpeta y están en el repositorio para poder clonarlos.
- `datasets/001/metadata/` guarda `manifest.json`, `preprocess.json` y `mapping.json` de ese mismo dataset. No hay una segunda copia de los libros.
- `datasets/<id>/raw/` es la copia exacta de una importación nueva. Esos archivos no entran a git.
- `inbox/` guarda la revisión previa y tampoco entra a git.
- `processed/` queda reservado para tablas derivadas de una etapa posterior. En 2-0 está vacío.
- `reports/` guarda perfiles y esquemas generados. Esos JSON no sustituyen a los libros.

## Política de fuentes

No se renombra, no se sobrescribe y no se limpia un archivo crudo. Un derivado nuevo se escribe en `processed/` o en `reports/` e indica de qué archivo y de qué SHA-256 salió.

## Trazabilidad y reproducibilidad

Cada dataset tiene un identificador (`001`) y un `manifest.json` con el tamaño, el SHA-256 y la estructura observada de cada libro. El mismo perfil se puede volver a calcular con `esp-core` sin modificar el original. La fecha de análisis del manifest es la de esa ejecución, no una fecha de publicación inventada.

## Procedencia

Los libros de `001/` son una fuente experimental externa. Su autor, su DOI de dataset y su DOI de artículo están en `001/README.md`. No son entradas del usuario, ni salidas del modelo físico, ni lecturas de un sensor de pozo.

## Licencias

Los libros no traen un archivo de licencia propio. El uso y cualquier redistribución deben seguir las condiciones publicadas con el DOI `10.17632/fk2b4r69bs.1`. Este repositorio no asigna otra licencia a esa fuente.

## Derivados

Un derivado debe conservar `generated_from`, `source_sha256`, `generated_at` y `tool_version`. Si el SHA-256 del libro cambia, el derivado queda obsoleto y hay que generarlo de nuevo. No se escribe dentro del `.xlsx`.

## Identificación

El identificador es el nombre de la carpeta (`001`, `002`, …). El índice lo publica `GET /api/v1/research/datasets`.
