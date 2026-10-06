# Etapa 1C.1 — Acerca de y créditos del proyecto

Nota de la etapa 2-0: este documento conserva el nombre histórico de la ampliación de la página Acerca de. La etapa global del proyecto es 2-0. El modelo físico sigue siendo `hydraulics-v0.1`. El panel de estado ya no muestra una fila de créditos de esta ampliación.

Etapa intermedia de presentación. No cambia el motor `hydraulics-v0.1` ni abre la etapa 1D.

## Propósito

`/about/` explica para qué existe ESP Digital Twin, en qué trabajo académico se desarrolla y quién es el autor del software. Es contenido de `esp-web`. No hay un servicio nuevo.

## Qué muestra

- Descripción del proyecto como plataforma educativa y experimental, de desarrollo incremental.
- Contexto de la Virtual Research Internship y el título del proyecto de investigación, en inglés y en español.
- Objetivo de investigación: conocimiento físico, datos e inteligencia artificial, como dirección posterior. Esas capacidades no se presentan como ya implementadas.
- Filosofía Understand → Model → Simulate → Measure → Predict → Hybridize.
- Autoría de Antonio Ralph Avezon Saavedra: ingeniero en informática y estudiante del magíster. El magíster no se presenta como título obtenido.
- Contexto académico: Universidad Andrés Bello (Chile) como institución de origen y Universidad de los Andes (Colombia) como universidad que dirige y supervisa el estudio, junto con Hemispheric University Consortium (HUC), Virtual Research Internship Program y el profesor supervisor Nicolás Rios Ratkovich.
- Tecnologías presentes en el repositorio y, aparte, capacidades de investigación previstas.
- Etapa técnica vigente, leída de la salud de `esp-core` cuando responde, y el modelo físico. Si el núcleo no responde, se usan los valores de respaldo de `anatomy/project_metadata.py`. Al escribir esta ampliación eran la etapa 1C y `hydraulics-v0.1`. Desde la etapa global 2-0 el respaldo de esa etapa es 2-0; el modelo sigue siendo `hydraulics-v0.1`.
- Hoja de ruta discreta. Las etapas posteriores quedan como previstas.
- Aviso de uso académico: no está certificada para controlar una ESP industrial.

## Ruta y navegación

La ruta es `/about/`. El enlace **Acerca de** vive en `anatomy/templates/anatomy/includes/global_nav.html`, incluido desde el conjunto, la bomba, el laboratorio y esta página. El pie común está en `includes/site_footer.html`.

Desde Acerca de se vuelve al conjunto con **Volver a ESP Digital Twin**.

## Metadatos

`services/esp-web/anatomy/project_metadata.py` concentra nombre, año, autor, contexto académico, stack, hoja de ruta y los valores de respaldo de etapa y modelo. El procesador `anatomy.context_processors.project` los entrega a las plantillas. La vista `about` superpone etapa y modelo con `GET /api/v1/health`.

La anatomía sigue publicando `stage: "1A"` y la bomba `stage: "1B"`. Esas etiquetas describen cada documento, no el estado del proyecto. En esta ampliación el cromo de la portada usaba la etapa global de entonces (1C) y el modelo `hydraulics-v0.1`. Desde 2-0 la portada identifica la anatomía como capacidad 1A; la etapa global se muestra en Acerca de y en Investigación.

## Privacidad

La página solo muestra información pública del proyecto. No incluye variables de entorno, secretos, rutas del host, nombres de contenedores ni datos personales distintos del nombre y la afiliación académica indicados. El repositorio no define una licencia; los créditos son de desarrollo, año 2026.
