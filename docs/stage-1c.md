# Etapa 1C — Hidráulica básica

## Presión

La presión dice cuánta fuerza empuja el fluido por cada unidad de área. En este modelo se mide, por dentro, en pascales (Pa). La pantalla también acepta kPa, bar y psi. Un pascal es un newton por metro cuadrado.

No hace falta imaginar todavía el pozo completo. Aquí la presión es un dato del experimento: la fija quien usa el laboratorio.

## Presión de intake

Es la presión a la entrada de la bomba, antes de que el fluido atraviese las etapas. En la cadena del conjunto, el fluido llega desde la admisión. En esta etapa no calculamos cómo se formó esa presión en el reservorio: es una entrada.

## Presión de discharge

Es la presión a la salida de la bomba, hacia el tubing. Si la bomba está aportando energía al fluido en el sentido esperado del laboratorio, esta presión es mayor que la de entrada.

## ΔP

La presión diferencial es la resta entre salida y entrada:

\[
\Delta P = P_d - P_i
\]

| Símbolo | Qué es | Unidad interna |
| --- | --- | --- |
| \(P_d\) | Presión de descarga | Pa |
| \(P_i\) | Presión de entrada | Pa |
| \(\Delta P\) | Incremento de presión | Pa |

Importa porque resume, con las simplificaciones actuales, cuánto subió la presión entre los dos extremos de la bomba. Si la descarga no supera a la entrada, el laboratorio no se cae: avisa de que ese caso no es el escenario educativo de una bomba impulsando fluido, y aun así muestra el número.

## Head

El head es energía por unidad de peso. Se escribe como una altura equivalente de columna de fluido:

\[
H = \frac{\Delta P}{\rho g}
\]

| Símbolo | Qué es | Unidad interna |
| --- | --- | --- |
| \(H\) | Head | m |
| \(\Delta P\) | Presión diferencial | Pa |
| \(\rho\) | Densidad | kg/m³ |
| \(g\) | Gravedad estándar, 9.80665 | m/s² |

Un head de 140 m no significa que haya un tubo vertical de 140 m parado encima de la bomba. Significa que el aumento de presión equivale, para ese fluido y esa gravedad, a la columna de esa altura.

## Pressure vs Head

No son sinónimos. La presión es fuerza por área. El head es esa diferencia de presión repartida por el peso específico del fluido, \(\rho g\).

Si dos fluidos sufren el mismo \(\Delta P\) y uno es menos denso, su head es mayor: la misma fuerza por área sostiene una columna más alta cuando el fluido pesa menos. El modo Compare Fluids enseña exactamente eso.

## Densidad

La densidad es la masa por unidad de volumen. El valor sugerido para agua educativa es 1000 kg/m³, pero entra como dato. No está escondido dentro de la fórmula. Cambiarla, con el mismo \(\Delta P\), cambia el head y, si el caudal se mantiene, también la potencia hidráulica.

## Caudal

El caudal volumétrico, \(Q\), es el volumen de fluido que pasa por unidad de tiempo. Por dentro se usa m³/s. La pantalla acepta m³/day y bpd.

En esta etapa \(Q\) es una entrada del experimento. Todavía no sale de una curva de bomba ni de un punto de operación.

## Potencia hidráulica

Es la rapidez con la que el modelo asocia energía hidráulica al fluido:

\[
P_{hyd} = \rho g Q H
\]

Con las hipótesis de este modelo (fluido incompresible y densidad constante) esa expresión coincide con:

\[
P_{hyd} = Q \Delta P
\]

| Símbolo | Qué es | Unidad interna |
| --- | --- | --- |
| \(P_{hyd}\) | Potencia hidráulica | W |
| \(Q\) | Caudal | m³/s |

La pantalla también la muestra en kW. No es la potencia eléctrica del motor y no incluye eficiencia.

## Energía

La bomba, en esta lección, toma energía mecánica del eje y la entrega al fluido como energía hidráulica. Esa energía se ve en el conjunto presión, head y caudal. El reparto eléctrico, las pérdidas del motor y la eficiencia quedan para más adelante.

Si se indica un número de etapas \(N\), el laboratorio puede mostrar \(H/N\). Es un reparto ideal para aprender. No afirma que cada etapa real produzca el mismo head en cualquier condición.

## Ejemplo resuelto

Caso educativo de agua. No es la placa de una ESP comercial. Los números salen del motor `hydraulics-v0.1`.

Entradas:

```text
P_intake    = 100 psi
P_discharge = 300 psi
ρ           = 1000 kg/m³
Q           = 500 m³/day
g           = 9.80665 m/s²
N           = 3   (opcional)
```

Conversiones internas:

```text
100 psi = 689475.7293168361 Pa
300 psi = 2068427.1879505082 Pa
500 m³/day = 0.005787037037037037 m³/s
```

Paso 1:

```text
ΔP = P_discharge − P_intake
ΔP = 2.06843e+06 Pa − 689476 Pa
ΔP = 1.37895e+06 Pa (200 psi)
```

Paso 2:

```text
H = ΔP / (ρ · g)
H = 1.37895e+06 Pa / (1000 kg/m³ · 9.80665 m/s²)
H = 140.614 m
```

Paso 3:

```text
P_hyd = ρ · g · Q · H
P_hyd = 1000 kg/m³ · 9.80665 m/s² · 0.00578704 m³/s · 140.614 m
P_hyd = 7980.04 W (7.98004 kW)
```

La forma equivalente \(Q \Delta P\) da el mismo valor: 7980.043163389305 W.

Paso opcional, solo si se piden 3 etapas:

```text
H_etapa = 140.614 m / 3 = 46.8713 m
```

## Qué todavía no modela

Curva H-Q, eficiencia, curva de potencia de la bomba, BEP, punto de operación, curva del sistema, RPM, frecuencia del variador, leyes de afinidad, motor, temperatura, sensores, ruido, fallas, gas, cavitación, viscosidad avanzada y cualquier modelo de aprendizaje automático. Tampoco hay tiempo: cada cálculo es estático.
