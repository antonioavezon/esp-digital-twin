"""Catálogo de datasets de investigación.

Los nombres, DOI y archivos salen de la ficha del dataset. Este módulo no
interpreta columnas ni asigna unidades que el encabezado no escriba.
"""

TOOL_VERSION = "research-profile-2-0"
RESEARCH_STAGE = "2-1"

DATASETS = {
    "001": {
        "dataset_id": "001",
        "title": (
            "Modeling Flow Pattern Transitions in Electrical Submersible "
            "Pump under Gassy Flow Conditions"
        ),
        "short_title": "ESP under Gassy Flow Conditions",
        "author": "Jianjun Zhu",
        "dataset_doi": "10.17632/fk2b4r69bs.1",
        "article_doi": "10.1016/j.petrol.2019.05.059",
        "source_type": "experimental",
        "processing_status": "raw",
        "files": (
            "Mapping Test Data_zero IPA.xlsx",
            "Surging Test Data_zero IPA.xlsx",
        ),
    }
}
