# ESP Digital Twin

Simulador educativo de una bomba electrosumergible (ESP, Electrical Submersible Pump). El objetivo de largo plazo es un gemelo operacional y visual, con modelos físicos y, más adelante, modelos Physics-AI.

**Etapa actual: 1F** — motor y variador de frecuencia, junto con la anatomía, la bomba, el laboratorio físico y las curvas. El cálculo hidráulico sigue siendo el modelo estático `hydraulics-v0.1`. No hay simulación temporal ni inteligencia artificial.

## Aplicación Android

La misma aplicación, para el teléfono, está en [`android/`](android/). No depende de la API: el APK lleva el catálogo, las curvas y el cálculo. Es una compilación de depuración, no una publicación de tienda.

**[Descargar esp-digital-twin.apk](https://github.com/antonioavezon/esp-digital-twin/releases/download/android-0.1/esp-digital-twin.apk)**

El archivo también está en el repositorio: [`android/esp-digital-twin.apk`](android/esp-digital-twin.apk). Cómo compilarlo e instalarlo está en [`android/README.md`](android/README.md).

## 1. Objetivo del proyecto

Comprender y, en etapas posteriores, simular el conjunto ESP dentro de un pozo: alimentación, variador, cable, motor, protector, admisión, bomba, tubing, pozo, reservorio y superficie.

La etapa 1A deja la base visual. La etapa 1B entra en la bomba. La etapa 1C calcula la primera hidráulica estática sin sustituir esas dos. La etapa 1D muestra las curvas de catálogo. Las etapas 1E y 1F explican el motor y el variador. La etapa actual es la 1F. El variador guarda una frecuencia de estudio y no calcula un punto de operación. El material está en [docs/stage-1a.md](docs/stage-1a.md), [docs/stage-1b.md](docs/stage-1b.md), [docs/stage-1c.md](docs/stage-1c.md), [docs/stage-1d-curves.md](docs/stage-1d-curves.md) y [docs/stage-1e-1f.md](docs/stage-1e-1f.md). Las reglas de evolución están en [docs/architecture.md](docs/architecture.md).

## 2. Estado actual: etapa 1F

| Capacidad | Estado |
| --- | --- |
| Anatomía del conjunto (etapa 1A) | Disponible en `/` |
| Interior de la bomba (etapa 1B) | Disponible en `/pump/` |
| Laboratorio físico (etapa 1C) | Disponible en `/physics/` |
| Curvas de desempeño (etapa 1D) | Disponible en `/curves/` |
| Motor (etapa 1E) | Explicación en `/pump/`. Potencia, corriente, tensión, polos y eficiencia siguen pendientes de datos |
| VSD/VFD (etapa 1F) | Frecuencia de estudio en `/pump/` y en el laboratorio. No calcula caudal, head ni potencia |
| Cálculo hidráulico | `hydraulics-v0.1`, estático, en `/physics/` |
| Simulación dinámica | No habilitada |
| Modelo de IA | No habilitado |
| Frecuencia de estudio | Control de 30 a 90 Hz, valor inicial 60 Hz. No desplaza las curvas ni calcula un punto de operación |

La aplicación es un entorno educativo. No está preparada para controlar una ESP real. Play y Pause, en la vista de la bomba, solo mueven la animación del impulsor. Calculate, en el laboratorio, pide un cálculo estático a `esp-core`.

## 3. Arquitectura

```text
navegador  →  esp-web (Django, :8000)  →  esp-core (API, :8080)
```

- `esp-core` describe la ESP en JSON (`/api/v1`). Es el único dueño del catálogo.
- `esp-web` dibuja el pozo y consume ese JSON. No repite las definiciones.

Los dos contenedores comparten la red `esp-digital-twin`. Dentro de esa red la web usa `http://esp-core:8080`. Los puertos del archivo `.env` solo aplican al host.

## 4. Requisitos

Probado como objetivo en **Fedora Linux 43 (Workstation)** con **Podman 5**.

- Podman
- `podman compose` (en Fedora 43 suele delegar en el plugin Docker Compose; no hace falta instalar `podman-compose`)
- curl, para las comprobaciones de los scripts
- Un navegador

No hace falta un intérprete Python en el host. Las imágenes usan Python 3.12.

## 5. Instrucciones en Fedora

Desde el directorio del proyecto:

```bash
cd esp-digital-twin
cp -n .env.example .env
```

`./scripts/start.sh` copia `.env.example` si `.env` no existe. Revise los puertos si 8000 o 8080 ya están ocupados en su máquina:

```bash
ESP_WEB_HOST_PORT=8000
ESP_CORE_HOST_PORT=8080
```

## 6. Construcción de contenedores

```bash
podman compose --env-file .env build
```

`./scripts/start.sh` también construye antes de arrancar.

## 7. Inicio

```bash
./scripts/start.sh
```

El script espera a que respondan la API y la web. Al terminar indica las URLs.

## 8. Detención

```bash
./scripts/stop.sh
```

Elimina los contenedores de esta composición. No borra las imágenes ni el código. No usa comandos destructivos sobre volúmenes: el proyecto no tiene base de datos.

## 9. Verificación

```bash
./scripts/status.sh
podman ps
```

En `podman ps`, `esp-core` y `esp-web` deben figurar como `healthy`.

Comprobación manual:

```bash
curl -fsS http://127.0.0.1:8080/api/v1/health
curl -fsS http://127.0.0.1:8000/health/
```

Si cambió los puertos en `.env`, use esos valores.

Para ver las curvas de desempeño: abra `http://127.0.0.1:8000/curves/`, elija fabricante, serie y modelo, y deje marcadas Head, potencia de eje y eficiencia. El contador debe decir `3 de 3`. Calcule un caso en el laboratorio y, si quiere comparar ese head con la curva, escriba el número de etapas: sin ese número la ficha sigue por etapa y el punto del laboratorio no se superpone. El material está en [docs/stage-1d-curves.md](docs/stage-1d-curves.md) y [docs/stage-1e-1f.md](docs/stage-1e-1f.md).

## 10. Logs

```bash
podman logs esp-core
podman logs esp-web
podman compose --env-file .env logs -f
```

Al arrancar debería aparecer algo equivalente a:

```text
ESP-CORE | API started
ESP-WEB  | Connected to esp-core
ESP-WEB  | GET /
```

La última línea se escribe cuando un navegador abre la página principal. Los healthchecks no se registran, para no llenar el log.

## 11. Pruebas

```bash
./scripts/test.sh
```

Ejecuta pytest en la imagen `esp-core` y `manage.py test` en la imagen `esp-web`. Comprueban la anatomía 1A, la bomba 1B, la hidráulica 1C (ΔP, head, potencia, unidades, validaciones y gráficos), la página `/about/` y que la web reenvía el cálculo al núcleo. El doble HTTP de las pruebas de Django no calcula física.

## 12. URL web

```text
http://localhost:8000/
http://localhost:8000/pump/
http://localhost:8000/physics/
http://localhost:8000/curves/
http://localhost:8000/about/
http://localhost:8000/config/
```

El menú sigue el idioma elegido en Configuración. En español: ESP, Bomba, Laboratorio físico, Curvas, Configuración y Acerca de.

En `/pump/`, Play y Pause animan el impulsor. Esa animación no es una velocidad física. El recorrido del fluido es ilustrativo. Una etapa y la vista multietapa cambian el dibujo. Anterior y Siguiente recorren admisión, tres etapas y descarga. A la izquierda se explica el motor con los datos que el modelo todavía no tiene. A la derecha, el variador guarda una frecuencia de estudio.

En `/physics/`:

- Las entradas son presión de intake, presión de descarga, densidad, caudal y, si se quiere, un número de etapas.
- **Calculate** envía esos datos a `esp-core`. ΔP, head y potencia hidráulica vuelven calculados.
- **Show Calculation** muestra la ecuación, la sustitución y las unidades que devolvió la API.
- **Compare Fluids** compara dos densidades con las presiones y el caudal que haya en el formulario.
- Los tres experimentos cargan casos educativos. No son datos de una ESP comercial.
- Las unidades internas son del SI. La pantalla puede usar psi, bar, kPa, m³/day, bpd y kW. El factor de conversión está solo en el núcleo.

Limitación del cálculo estático: fluido monofásico, incompresible y de densidad constante. No hay tiempo ni sensores. Las curvas de catálogo viven en `/curves/` y no salen de ese cálculo. El detalle está en [docs/stage-1c.md](docs/stage-1c.md) y [docs/stage-1d-curves.md](docs/stage-1d-curves.md).

## Variables de entorno

Copie `.env.example` a `.env`. No suba `.env` al repositorio. Los valores de ejemplo no son secretos de producción.

| Variable | Uso |
| --- | --- |
| `ESP_CORE_HOST_PORT` | Puerto del host para la API. Dentro de la red de contenedores el servicio sigue en el puerto 8080. |
| `ESP_WEB_HOST_PORT` | Puerto del host para la web. Dentro del contenedor sigue en el puerto 8000. |
| `DJANGO_SECRET_KEY` | Clave de Django. Cambie el valor de ejemplo si expone el servicio fuera de su máquina. |
| `DJANGO_DEBUG` | `0` en el ejemplo. No active depuración en una máquina accesible por otros. |
| `DJANGO_ALLOWED_HOSTS` | Hosts aceptados por Django, separados por coma. |
| `ESP_CORE_TIMEOUT` | Segundos que la web espera al núcleo. |
| `LOG_LEVEL` | Nivel de log del núcleo y de la web. |

La web llama al núcleo por `http://esp-core:8080`. Ese nombre es el del servicio en Compose. No lo reemplace por `localhost` dentro del contenedor.

## Limitaciones de esta versión

- La etapa actual es la 1F. El cálculo de presión, head y potencia hidráulica sigue siendo `hydraulics-v0.1`, estático.
- La frecuencia de estudio no desplaza las curvas ni calcula un caudal, un head o una potencia nuevos. Faltan el número de polos, la curva de la bomba a otra frecuencia y la curva del sistema.
- El motor no tiene potencia, corriente, tensión ni eficiencia de placa. Esos datos se muestran como pendientes.
- Las curvas disponibles son las fichas REDA ya digitalizadas, a 60 Hz y 3500 rpm, por etapa. El PDF de origen no está en el repositorio. No se extrapola.
- La potencia hidráulica del laboratorio no es la potencia de eje de la ficha.
- No hay simulación dinámica ni modelo de inteligencia artificial.
- La aplicación no controla una ESP real.

## 13. Endpoints API

Publicados en el host, por defecto en el puerto 8080:

```text
GET  /api/v1/health
GET  /api/v1/esp
GET  /api/v1/esp/components
GET  /api/v1/esp/flows
GET  /api/v1/esp/pump
GET  /api/v1/esp/pump/stages
GET  /api/v1/esp/pump/flow-path
GET  /api/v1/physics/constants
POST /api/v1/physics/hydraulics
POST /api/v1/physics/charts
POST /api/v1/physics/compare
GET  /api/v1/physics/curves
GET  /api/v1/physics/curves/{id}
POST /api/v1/physics/curves/{id}/marker
```

`/api/v1/health` informa el modelo hidráulico `hydraulics-v0.1` en modo estático. `/api/v1/esp` es la anatomía de la etapa 1A. `/api/v1/esp/pump` es la bomba de la etapa 1B.

Documentación interactiva de desarrollo: `http://127.0.0.1:8080/api/v1/docs`.

Ejemplos:

```bash
curl -sS http://127.0.0.1:8080/api/v1/health
curl -sS http://127.0.0.1:8080/api/v1/esp
curl -sS http://127.0.0.1:8080/api/v1/esp/pump
curl -sS http://127.0.0.1:8080/api/v1/physics/constants
curl -sS -X POST http://127.0.0.1:8080/api/v1/physics/hydraulics \
  -H 'Content-Type: application/json' \
  -d '{"intake_pressure":{"value":100,"unit":"psi"},"discharge_pressure":{"value":300,"unit":"psi"},"density":{"value":1000,"unit":"kg/m3"},"flow_rate":{"value":500,"unit":"m3/day"}}'
```

## 14. Troubleshooting

**Aviso `external compose provider`.** En Fedora 43 es normal: Podman está usando Docker Compose como proveedor. No indica que el arranque haya fallado.

**`podman.sock: no such file or directory`.** El proveedor Compose necesita el socket de la API de Podman. En Fedora 43 ese socket de usuario no arranca solo. `./scripts/start.sh` ejecuta `systemctl --user start podman.socket` si el archivo no existe. No lo deja habilitado de forma permanente. Si quiere que sobreviva al cierre de sesión, puede activarlo usted con `systemctl --user enable --now podman.socket`.

**El puerto ya está en uso.** Cambie `ESP_WEB_HOST_PORT` o `ESP_CORE_HOST_PORT` en `.env`, ejecute `./scripts/stop.sh` y vuelva a `./scripts/start.sh`.

**`esp-web` no pasa a healthy.** Su healthcheck consulta a `esp-core`. Revise `podman logs esp-core` y `podman logs esp-web`. La URL interna debe seguir siendo `http://esp-core:8080`; no la sustituya por `localhost` dentro del contenedor.

**La página abre pero dice que no obtuvo la definición.** El contenedor web no alcanzó el núcleo. El esquema sigue visible; el texto didáctico no se inventa en el navegador.

**SELinux.** Esta etapa no monta volúmenes del home dentro de los contenedores, así que no necesita `:Z`. Si más adelante se monta código para desarrollo, ese montaje sí debe considerarse.

**Reconstruir desde cero las imágenes**, sin borrar otros contenedores del sistema:

```bash
podman compose --env-file .env build --no-cache
```

Evite `podman system prune` salvo que sepa qué más hay en la máquina: borra recursos que no pertenecen a este proyecto.
