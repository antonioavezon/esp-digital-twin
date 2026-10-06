# Ingesta móvil — pendiente de la etapa 2-0

La aplicación de escritorio ya importa datasets. La móvil no. El fuente sí está en el workspace y no se modificó en esta pasada.

Hay dos copias del mismo proyecto Kotlin con Jetpack Compose:

- `esp-digital-twin/android/`
- `/home/antonio/projects/ESPSIMULADOR/ESP-Movil`

No se creó un proyecto Android nuevo. No se reconstruyó el APK. El APK publicado no debe incorporar los RAW de investigación.

Cuando se retome, la móvil implementa el mismo contrato de `docs/dataset-contract.md` con su propio almacenamiento. No lee `data/` de la web.

## Pendiente

- Gestor de datos en Investigación: importar archivo, listado, detalle y estructura. La presentación es de teléfono, no una copia de las tablas de escritorio.
- Selector con Storage Access Framework / document picker. No pedir acceso global al almacenamiento. No usar rutas fijas como `/sdcard/Download`.
- Aceptar xlsx, xlsm sin ejecutar macros, csv, tsv y json desde el proveedor que el sistema ofrezca (almacenamiento local, Descargas, Drive, OneDrive u otro DocumentProvider).
- Copiar el archivo al almacenamiento privado de la app:

```text
research/datasets/<dataset_id>/raw/
research/datasets/<dataset_id>/metadata/manifest.json
research/datasets/<dataset_id>/metadata/preprocess.json
research/datasets/<dataset_id>/derived/
```

- Guardar una ruta relativa o un identificador, no una ruta absoluta del dispositivo.
- Calcular SHA-256, conservar el RAW intacto y avisar si el hash ya existe.
- Generar manifest y preprocess con `schema_version` `1.0` y el profiler `esp-structural-profiler` `0.1`.
- Dejar `semantic_mapping.status` en `not_started`. No mapear variables ni convertir unidades.
- Registro que descubra datasets por su manifiesto y no se caiga si uno está incompleto.
- Errores controlados, sin cerrar la app: archivo vacío, corrupto, extensión incorrecta, JSON inválido, duplicado.
- Pruebas del stack real: selección de documento, copia privada, manifest, preprocess, duplicado, archivo inválido y persistencia después de reiniciar.
- `distribution` por defecto `unknown`.
