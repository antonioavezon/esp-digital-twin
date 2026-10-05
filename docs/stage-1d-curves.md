# Curvas de desempeño

La vista **Curvas** está en `/curves/`. Es el mismo gráfico que antes estaba al final del laboratorio: una bomba, con Head, potencia de eje y eficiencia sobre el mismo caudal. El laboratorio físico, en `/physics/`, conserva un enlace visible. No sustituye el cálculo estático `hydraulics-v0.1`. El laboratorio sigue calculando un punto: ΔP, head y potencia hidráulica. Las curvas completas salen de fichas publicadas, no de ese punto.

## Cómo leer las tres curvas

Comparten el caudal en el eje horizontal. Cada magnitud tiene su propia escala vertical porque no son la misma cosa ni el mismo orden de tamaño:

- **Head**: energía por unidad de peso, dibujada como altura. En la ficha REDA el eje izquierdo está en pies, con una equivalencia de presión entre paréntesis que depende del fluido de referencia. Esta aplicación no convierte head a presión por su cuenta.
- **Shaft Power**: potencia mecánica que la bomba pide en el eje. En la ficha está en hp. No es la potencia hidráulica del laboratorio.
- **Efficiency**: relación entre la potencia entregada al líquido y la potencia de entrada a la bomba. Se muestra en porcentaje. Por dentro se guarda como fracción.

Se pueden ver una, dos o las tres a la vez. El contador dice cuántas están activas, por ejemplo `2 de 3`.

## Cómo se elige la bomba

Los selectores solo ofrecen combinaciones que existen en el catálogo verificado: fabricante, serie, modelo, y el par frecuencia/rpm de esa ficha. No se arma una velocidad que la fuente no traiga. Hoy todas las fichas cargadas son REDA Production Systems, 60 Hz y 3500 rpm, series 400, 538 y 540.

## Qué significa una curva por etapa

El encabezado de cada ficha usada dice `1 Stage(s)`. La base es **por etapa**. El head y la potencia de eje de la ficha corresponden a una etapa. El caudal no se multiplica por las etapas. La eficiencia tampoco.

Si el campo Etapas queda vacío, el gráfico muestra esa base y no compara el head total del laboratorio con la curva.

Si se escribe un entero N mayor que 1, el gráfico pasa a **Estimación de bomba completa: N etapas**:

- head mostrado = head de la ficha × N
- potencia de eje mostrada = potencia de la ficha × N
- eficiencia y caudal quedan igual

Esa estimación no es un dato certificado del fabricante. N = 1 deja la ficha tal como se publicó.

## El punto del laboratorio físico

Después de Calcular, el laboratorio guarda el caso en la sesión del navegador. La vista Curvas lo reutiliza. No hay un segundo formulario.

La marca se llama **Punto calculado en Laboratorio físico**. Es el caso calculado con las entradas del laboratorio. No es la intersección de una curva de bomba con una curva de sistema, y esta etapa no calcula esa intersección.

La marca entra en el gráfico de head solo si se indicó un número de etapas, para no mezclar un head total con una curva por etapa. Si el caudal cae fuera del tramo digitalizado, no se extrapola.

## Potencia hidráulica y potencia de eje

La potencia hidráulica del laboratorio es la que el modelo asocia al fluido:

\[
P_{hyd} = \rho g Q H = Q \Delta P
\]

La potencia de eje de la ficha es la potencia mecánica de entrada a la bomba. El Hydraulic Institute la trata como input power de la bomba y la distingue de la potencia impartida al líquido. El Departamento de Energía, al describir curvas centrífugas, separa el brake horsepower del head y de la eficiencia.

Si el caudal del laboratorio cae dentro de la curva de eficiencia, se puede mostrar una estimación aparte:

\[
P_{shaft,estimada} = P_{hyd} / \eta
\]

η es la fracción interpolada en línea recta entre puntos digitalizados. No se extrapola. Esa estimación no reemplaza la potencia de eje de la ficha y no incluye pérdidas del motor ni del variador.

## Digitalización del PDF

Archivo usado: `514839319-Pump-Curve-REDA.pdf` (57 páginas, carta horizontal, productor RAD PDF, fechas de creación y modificación del 20 de noviembre de 2016). Ese PDF no está dentro del repositorio. El catálogo no guarda la ruta del disco.

El texto de cada ficha trae fabricante, modelo, 60 Hz, 3500 rpm, serie, una etapa, gravedad específica 1,00, Optimum Operating Range, revisión y el BEP (Q, H, P, E). Los trazos no vienen como tabla. Están en el PDF como segmentos vectoriales. El script `services/esp-core/tools/digitize_reda.py` los lee con poppler (`pdftotext` y `pdftocairo`), endereza el eje vertical y calibra cada escala con las marcas impresas de caudal, head, hp y eficiencia.

Una ficha entra al catálogo solo si, en el caudal del BEP impreso, las tres trazas quedan cerca de H, P y E publicados (hasta 1,5 ft, 0,2 hp y 4 puntos de eficiencia). Ese residuo se guarda en la curva. No es una precisión certificada: el campo de precisión declarada queda vacío a propósito.

Quedaron 46 curvas. No entraron las páginas 47 y 48, porque no tenían dos marcas utilizables en alguna escala, ni las páginas 49 a 57, que casi no tienen texto de ficha. Esas bombas no aparecen en los selectores.

Cada curva cargada queda marcada como digitalización aproximada y educativa, no como curva certificada. El Hydraulic Institute distingue la curva publicada de la curva certificada: esta última corresponde a la bomba e impulsor concretos ensayados, no a la línea general del catálogo.

El nombre **Optimum Operating Range** se conserva como está en la ficha. No se renombra a POR ni a AOR.

## BEP y rango

El BEP dibujado es el de la ficha (`origin: sheet`), no un máximo buscado sobre los puntos digitalizados. Si una ficha no lo trae, no se inventa. El rango sombreado usa el nombre y los caudales impresos. No se multiplica por el número de etapas.

## Unidades

Por dentro: m³/s, m, W y eficiencia en fracción. En pantalla se puede pasar el caudal a bpd, m³/day o m³/s; el head a ft o m; la potencia de eje a hp o kW. Los factores están solo en `app/physics/units.py` (pie internacional 0,3048 m; hp 745,6998715822702 W).

La gravedad específica de referencia de estas fichas es 1,00. El head no se pasa a presión. Si la densidad del laboratorio se aleja más de un 2 % de 1000 kg/m³, aparece un aviso: la curva no se corrige por viscosidad y no se presenta como válida para otro fluido.

## Lo que esta sección no hace

- No fabrica curvas sintéticas.
- No usa el punto del laboratorio para dibujar una curva.
- No calcula la curva del sistema ni el punto de operación por intersección.
- No aplica las leyes de afinidad para cambiar la velocidad: solo se ofrecen los 60 Hz / 3500 rpm de la ficha.
- No modela el motor ni el variador.

## Fuentes

Consulta del 4 de octubre de 2026.

- REDA Production Systems, fichas del archivo `514839319-Pump-Curve-REDA.pdf`, 57 páginas, revisión indicada en cada ficha (la primera, D5800N, es Rev. -B). Uso: metadatos, BEP, Optimum Operating Range y trazos vectoriales de las 46 curvas cargadas. No hay URL de publicación en el archivo.
- Hydraulic Institute, [Pump Curves](https://datatool.pumps.org/pump-fundamentals/pump-curves.html), actualización citada en la página: 19 de julio de 2024. Uso: head como energía por unidad de peso independiente de la densidad; eficiencia \(\eta_p = P_w / P_p\); potencia de entrada \(P_p = P_w / \eta_p\); BEP como caudal de máxima eficiencia a una velocidad dada; aviso de que la viscosidad altera head, caudal, eficiencia y potencia.
- Hydraulic Institute, [Pump FAQs](https://www.pumps.org/resources/pump-faqs/). Uso: la curva certificada no es la curva publicada ni la carta de selección; corresponde a la bomba e impulsor ensayados. También distingue la potencia medida en el eje de la potencia eléctrica de entrada al accionamiento.
- U.S. Department of Energy, [Improving Pumping System Performance: A Sourcebook for Industry](https://www.energy.gov/sites/prod/files/2014/05/f16/pump.pdf), Second Edition. Uso: la curva centrífuga relaciona caudal y head; el BEP es el punto de mayor eficiencia; el brake horsepower es una curva de la bomba, distinta del head.

No se usaron números del PDF público Centrilift Performance Series 400P60ER de Baker Hughes. Ese documento sirve para reconocer una ficha ESP por etapa, pero sus valores no corresponden a los modelos REDA de este catálogo.
