# ESP Digital Twin — Android

Aplicación Android autocontenida. El APK lleva el catálogo del conjunto, la descripción de la bomba, las curvas REDA ya digitalizadas y el motor `hydraulics-v0.1`. No consulta un servidor para calcular ni para mostrar esas pantallas.

Esta carpeta es la aplicación Android dentro del mismo repositorio. La web no cambia. Los datos embebidos salen de ese proyecto: `esp.json` y `pump.json` son el catálogo educativo, y `reda.json` es el mismo archivo de curvas.

## Requisitos para compilar

En este equipo (Fedora Linux 43):

- Android SDK en `$HOME/Android/Sdk`, con plataforma `android-36` y build-tools.
- JDK 21. El `java` por defecto puede ser más nuevo (en este equipo hay Java 25) y el complemento de Android Gradle no compila con él. Hay que apuntar `JAVA_HOME` al OpenJDK 21.

`local.properties` debe contener la ruta del SDK, por ejemplo:

```
sdk.dir=/home/antonio/Android/Sdk
```

Ese archivo no se publica con contraseñas ni tokens. No hay firma de producción.

## Compilar

Desde `android/`, en Fedora 43:

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export ANDROID_HOME="$HOME/Android/Sdk"
./gradlew test assembleDebug
```

El wrapper descarga Gradle 8.11.1 la primera vez. Hace falta red solo para esa descarga y para las dependencias de AndroidX. La aplicación ya compilada no la necesita.

## APK

La copia publicada, para descargar e instalar, es [`esp-digital-twin.apk`](esp-digital-twin.apk). En GitHub también está en la sección [Android 0.1](https://github.com/antonioavezon/esp-digital-twin/releases/download/android-0.1/esp-digital-twin.apk).

Al compilar en esta máquina, Gradle deja otra copia en:

`android/app/build/outputs/apk/debug/app-debug.apk`

Es un APK de depuración. Lo firma el almacén de debug que genera Android Gradle en la máquina de compilación. No sirve para una tienda. Para instalarlo hay que permitir aplicaciones de este origen. Si más adelante se instala un APK firmado con otra clave, hay que desinstalar antes esta versión de prueba.

En Fedora 43, con el teléfono en depuración USB o con un emulador ya creado:

```bash
adb install -r esp-digital-twin.apk
```

No hace falta configurar una URL. En el emulador y en el teléfono el comportamiento es el mismo, porque no hay backend.

## Qué hay en la aplicación

- ESP: componentes, recorridos de energía y de fluido, e iniciar/parar como esquema. No controla un equipo.
- Bomba: etapas, impulsor y difusor (solo uno marcado a la vez), recorrido ilustrativo y animación conceptual.
- Motor: texto cualitativo. Potencia, corriente, tensión, polos y eficiencia siguen pendientes de datos.
- VSD/VFD: frecuencia de estudio de 30 a 90 Hz, valor inicial 60 Hz. No calcula caudal, head ni potencia, y no mueve las curvas ni la animación.
- Laboratorio físico: los tres experimentos, el cálculo estático y la comparación de dos fluidos.
- Curvas: una ficha, head, potencia de eje y eficiencia sobre el mismo caudal, con escalas independientes. Unidades iniciales bpd, ft y hp.
- Configuración: idioma español o inglés, y tema oscuro o claro.
- Acerca de: el mismo encuadre del proyecto. La etapa técnica del motor sigue siendo Stage 1C, modelo `hydraulics-v0.1`, modo estático.

El caso de referencia del laboratorio, con entrada 100 psi, descarga 300 psi, densidad 1000 kg/m3, caudal 500 m3/day y 1 etapa, muestra ΔP 200 psi, head 140.614 m y potencia hidráulica 7.98004 kW.

## Límites

- No hay simulación dinámica, curva del sistema, punto de operación ni modelo de inteligencia artificial.
- La frecuencia de estudio no desplaza las curvas REDA, publicadas a 60 Hz y 3500 rpm.
- Las curvas son una digitalización aproximada, no una certificación del fabricante.
- La potencia hidráulica del laboratorio no es la potencia de eje de la ficha.
- La vista de bomba no tiene modelo cuantitativo. Los números están en el laboratorio.
- El texto de la bomba sale del catálogo en español. En inglés cambian la interfaz y los textos del conjunto ESP.
- El selector de etapas del laboratorio va de 1 a 120. Es el mismo techo didáctico de la aplicación web, no un dato de fabricante.
- No se inventan puntos fuera del tramo digitalizado de una curva.

## Pruebas

`./gradlew test` ejecuta las pruebas del motor en la JVM: el caso hidráulico de referencia, el rechazo de entradas inválidas, la comparación de fluidos y el BEP de la ficha D5800N incluida en el APK.
