# Dataset 001

Fuente experimental externa, en estado crudo. Los dos libros no se modifican.

| Campo | Valor |
| --- | --- |
| Dataset ID | 001 |
| Título | Modeling Flow Pattern Transitions in Electrical Submersible Pump under Gassy Flow Conditions |
| Autor | Jianjun Zhu |
| DOI del dataset | 10.17632/fk2b4r69bs.1 |
| DOI del artículo | 10.1016/j.petrol.2019.05.059 |
| Fecha | No consta en los libros. No se infiere una fecha de publicación a partir del sistema de archivos. |
| Estado | raw |
| Tipo de fuente | experimental |

## Archivos

Los nombres se conservan tal como se recibieron:

- `Mapping Test Data_zero IPA.xlsx`
- `Surging Test Data_zero IPA.xlsx`

El tamaño, el SHA-256, las hojas y los encabezados observados están en `manifest.json`. Ese manifiesto se calcula; no se redacta a mano.

## Propósito científico

El dataset acompaña el artículo indicado por el DOI `10.1016/j.petrol.2019.05.059`, sobre transiciones de patrón de flujo en una ESP en condiciones con gas. El significado de las columnas, cuando hay evidencia, está en `data/datasets/001/metadata/mapping.json`. Estos libros siguen sin interpretación automática.

## Conservación

Estos archivos son RAW y de solo lectura. No se renombran, no se sobrescriben y no se limpian. Cualquier perfil o tabla derivada se guarda fuera de ellos, en `data/reports/001/` o, más adelante, en `data/processed/`.

## Cita recomendada

Zhu, Jianjun. Data for: “Modeling Flow Pattern Transitions in Electrical Submersible Pump under Gassy Flow Conditions”. Dataset DOI: 10.17632/fk2b4r69bs.1. Artículo asociado: 10.1016/j.petrol.2019.05.059.

## Advertencia

Un encabezado se transcribe como texto. Si el propio texto no declara una unidad, la unidad queda en null. No se infiere si una columna es caudal, head, presión de admisión, fracción de gas u otra magnitud hasta que una etapa posterior lo documente con evidencia.
