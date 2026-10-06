"""Contrato de datasets de la etapa 2-0.

Neutral respecto de Web, Android, Linux, Windows y de la ruta física.
El identificador no es una ruta absoluta. La web y el móvil pueden
implementarlo por separado; no hay dependencia de ejecución entre ambos.
"""

SCHEMA_VERSION = "1.0"
PROFILER_NAME = "esp-structural-profiler"
PROFILER_VERSION = "0.1"

# Estados de ingesta. No incluyen trained, predicted ni classified.
STATES = (
    "selected",
    "validated",
    "imported",
    "profiled",
    "ready_for_mapping",
    "error",
)

DISTRIBUTIONS = ("public", "private", "unknown")

ALLOWED_EXTENSIONS = {
    ".xlsx": "xlsx",
    ".xlsm": "xlsm",
    ".csv": "csv",
    ".tsv": "tsv",
    ".json": "json",
    ".txt": "txt",
}
