# Arquitectura — ESP Digital Twin

Etapa vigente: **1C — Hidráulica básica**. Siguen disponibles la anatomía (1A) y el interior de la bomba (1B). Este documento es el contrato de evolución del repositorio. Las etapas siguientes deben modificarlo cuando cambien una decisión, no reemplazar el sistema.

## Responsabilidades

| Pieza | Responsabilidad | No debe hacer |
| --- | --- | --- |
| `esp-core` | Dominio conceptual de la ESP, descripción de la bomba y motor físico estático | HTML, estilos y simulación temporal |
| `esp-web` | Presentación, esquema SVG e interacción didáctica | Definir de nuevo los componentes, sus funciones o los recorridos |
| `compose.yaml` | Topología de contenedores, puertos del host y healthchecks | Lógica de negocio |
| `docs/` | Decisiones y material educativo | Sustituir al código como fuente de los datos de la ESP |

Hay dos servicios porque cada uno tiene una responsabilidad distinta. No se agregan microservicios vacíos.

## Contrato entre los servicios

- La web llama a `esp-core` por HTTP, en el servidor, durante el render de la página.
- El navegador habla solo con `esp-web`. No necesita CORS en 1A.
- El identificador estable de cada componente (`motor`, `pump`, `electrical-cable`, …) es el contrato con el esquema SVG. La geometría vive en `esp-web`; el significado vive en `esp-core`.
- Si un componente nuevo entra al catálogo, aparece en la lista de la interfaz. Para verlo en el corte esquemático hay que añadir un nodo SVG con el mismo `data-component`.
- Los recorridos `energy` y `fluid` también son datos del núcleo. El SVG solo sabe dibujarlos.

URL interna, fija por el nombre del servicio en Compose:

```text
http://esp-core:8080
```

Los puertos `ESP_CORE_HOST_PORT` y `ESP_WEB_HOST_PORT` solo publican los servicios en el host Fedora. No deben usarse como URL interna: dentro de un contenedor, `localhost` es ese contenedor.

## API v1

Prefijo: `/api/v1`.

| Método | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/v1/health` | Estado del proceso. `stage` es la etapa del proyecto (`1C`) e incluye `physics.model` |
| GET | `/api/v1/esp` | Conjunto de la etapa 1A: componentes, recorridos y capacidades. Sigue en `stage` `1A` |
| GET | `/api/v1/esp/components` | Solo componentes de la anatomía |
| GET | `/api/v1/esp/flows` | Solo recorridos de la anatomía |
| GET | `/api/v1/esp/pump` | Bomba multietapa conceptual de la etapa 1B. Sigue sin magnitudes |
| GET | `/api/v1/esp/pump/stages` | Solo las etapas didácticas |
| GET | `/api/v1/esp/pump/flow-path` | Recorrido de una etapa y recorrido de las tres etapas |
| GET | `/api/v1/physics/constants` | Gravedad, unidades, experimentos y estado del laboratorio |
| POST | `/api/v1/physics/hydraulics` | ΔP, head y potencia hidráulica, con pasos |
| POST | `/api/v1/physics/charts` | Barridos de esas ecuaciones. No son curvas de bomba |
| POST | `/api/v1/physics/compare` | Mismo ΔP con dos densidades |
| GET | `/api/v1/physics/curves` | Índice de curvas verificadas, sin los puntos |
| GET | `/api/v1/physics/curves/{id}` | Una curva en unidades pedidas. `stages` escala head y potencia de eje si la ficha es por etapa |
| POST | `/api/v1/physics/curves/{id}/marker` | Compara el punto ya calculado del laboratorio. No recalcula ΔP, head ni potencia hidráulica |

La bomba no tiene servicio propio. El motor físico tampoco: vive en `esp-core`, dentro de `app/physics/`, separado de `app/domain/`. Así puede extraerse más adelante si el cálculo deja de caber aquí. Las fórmulas reciben el SI. Las conversiones están solo en `app/physics/units.py`.

`quantitative_model` del documento de la bomba sigue en `null`. Los números no se incrustan en el catálogo de 1B: salen del modelo `hydraulics-v0.1`. En esta versión, \(Q\) y \(\Delta P\) son entradas del usuario (`source: user_input`). La respuesta ya distingue `user_input`, `physics_model` y `constant`, y reserva el nombre de fuentes futuras (`sensor`, `simulation`, `ml`, `physics_ai`) sin producirlas.

El navegador no llama a `esp-core`. Django reenvía el JSON de `/physics/api/` y pinta lo que vuelve. JavaScript no evalúa \(H\) ni \(P_{hyd}\).

Reglas de evolución:

- Dentro de v1, los cambios deben ser aditivos: campos nuevos, no renombres silenciosos de `id`.
- Un cliente debe ignorar campos que no conoce.
- Un cambio incompatible (quitar un `id`, alterar el orden semántico de un recorrido ya publicado) exige `/api/v2` o una etapa que actualice a la vez núcleo, web y pruebas.
- OpenAPI queda en `/api/v1/docs` para inspección durante el desarrollo. No es una consola de operación.

## Huecos reservados

Cada componente incluye `extensions` con estas claves, todas `null` en 1A:

`variables`, `sensors`, `states`, `limits`, `equations`, `alarms`, `events`, `predictive_models`.

`capabilities` del conjunto permanece en falso:

`simulation`, `physics_engine`, `ai_model`, `control`.

`app/domain/catalog.py` contiene `assert_stage_1a()`. Esa función impide arrancar el núcleo si alguien rellena extensiones o enciende capacidades sin actualizar la etapa. Cuando una etapa posterior las active, debe relajar esa traba en el mismo cambio y cubrirlo con una prueba. No se borra el histórico: se documenta aquí.

## Qué no existe en 1A

- Base de datos. Django tiene un backend SQLite en memoria solo porque el framework lo exige; no hay modelos ni migraciones.
- Bus de mensajes, colas o autenticación.
- Valores de placa, curvas, caudales, presiones, frecuencias o resultados de un modelo.
- Inteligencia artificial.

La interfaz debe decir que esas capacidades no están habilitadas. No se simula un número para “llenar” la pantalla.

## Cómo extender sin reescribir

1. Leer el estado real del repositorio y las pruebas de contrato (`services/esp-core/tests/test_api.py` y `services/esp-web/anatomy/tests.py`).
2. Cambiar el dominio en `esp-core` si el conocimiento es de la ESP.
3. Cambiar `esp-web` solo si cambia la presentación o el esquema.
4. Mantener `/api/v1` compatible. Agregar endpoints nuevos bajo el mismo prefijo cuando el recurso sea nuevo.
5. Añadir `docs/stage-1d.md` (o la etapa que corresponda) sin borrar el contexto de 1A, 1B y 1C.
6. Añadir o ajustar pruebas de regresión antes de dar la etapa por cerrada.
7. Crear otro contenedor solo cuando tenga una responsabilidad que no quepa en estos dos.

## Ejecución

Imágenes basadas en Python 3.12. El host de desarrollo es Fedora 43, cuyo Python de sistema puede ser más nuevo que el rango soportado por Django 5.2. Las pruebas y el runtime corren dentro de los contenedores para no depender de ese intérprete.

Podman 5 en Fedora usa `podman compose`. En esta máquina el proveedor es Docker Compose v5; el paquete `podman-compose` no es necesario. El aviso de “external compose provider” no es un fallo.

Los healthchecks están en la imagen y en `compose.yaml`. `podman ps` debe mostrar `(healthy)` cuando el servicio responde.
