# Motor y VSD/VFD

La vista **Bomba** (`/pump/`) muestra el motor a la izquierda, la bomba en el centro y el variador a la derecha. En pantallas estrechas esas zonas quedan en ese mismo orden, una debajo de otra.

El laboratorio físico conserva dos resúmenes por encima del enlace a Curvas. El de la derecha edita la misma frecuencia que la vista Bomba. El valor vive en `localStorage`, clave `esp-study-hz`. No hay una copia distinta en cada página.

## Qué está calculado

Nada nuevo de hidráulica. El motor de `hydraulics-v0.1` sigue igual. La frecuencia de estudio no entra en ΔP, head, potencia hidráulica ni en las curvas REDA.

## Qué falta para un resultado físico

- Potencia, corriente, tensión, número de polos y eficiencia del motor. Sin polos no se evalúa \(n = 120 f / p\).
- Curva de la bomba a una frecuencia distinta de los 60 Hz / 3500 rpm de la ficha.
- Curva del sistema. Sin ella, la frecuencia no determina un caudal.

El rango 30–90 Hz es un límite de estudio, no la placa de un variador. El valor inicial es 60 Hz, la condición de las fichas REDA. Cambiarlo no desplaza esas curvas y la animación de la bomba no cambia con él. Una entrada vacía o fuera de rango no reemplaza el último valor válido.

La potencia hidráulica del laboratorio y la potencia de eje de una ficha siguen siendo magnitudes distintas. La primera se calcula en `/physics/`. La segunda solo aparece en `/curves/` cuando la ficha la trae.
