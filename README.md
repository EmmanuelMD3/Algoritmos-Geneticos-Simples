# Algoritmo genético simple — Cómputo evolutivo

Proyecto didáctico en **Python 3.10 o superior**. Implementa los métodos de la presentación *05 Hiperparámetros.pdf* y un motor de optimización de **un objetivo** (minimizar o maximizar), para funciones con una o varias variables. La ejecución por consola no requiere paquetes externos; la interfaz gráfica usa Matplotlib.

## Estructura

- `main.py`: menú, configuración y ejecución del algoritmo genético
- `gui.py`: interfaz de escritorio con Tkinter/ttk y gráficas integradas
- `gui_logic.py`: validación de parámetros de la interfaz
- `ejemplos.py`: demostraciones numeradas de los 17 métodos de la presentación
- `ag/seleccion.py`: 5 métodos de selección
- `ag/cruce.py`: 7 métodos de cruce
- `ag/mutacion.py`: 3 métodos de mutación + inversión de bit para binarios
- `ag/sustitucion.py`: steady-state y crowding
- `ag/objetivos.py`: funciones personalizadas sin usar `eval()` libre; ejemplo de rutas
- `ag/motor.py`: ciclo de evolución, población, decodificación binaria, evaluación, elitismo, estadísticas
- `tests/`: pruebas de operadores e integración de la interfaz con el motor

## Interfaz gráfica (Windows 11)

Tkinter/ttk viene con la instalación habitual de Python para Windows. Instala la única dependencia externa de la interfaz y ábrela desde la carpeta del proyecto:

```powershell
python -m pip install -r requirements.txt
python gui.py
```

La pestaña **Optimización** permite escribir una función, elegir mínimo o máximo, representación, operadores e hiperparámetros. Para varias variables usa `x0`, `x1`, etc. Por ejemplo, `x0**2+x1**2`. Si todas comparten dominio, rellena los límites comunes. Para dominios distintos, escribe en **Límites por variable** un par por variable separado por punto y coma, como `-10:10; -5:5`; esos pares sustituyen los límites comunes. Cambiar a representación binaria actualiza automáticamente los cruces y mutaciones compatibles.

La pestaña **Ejemplos (17)** permite seleccionar y ejecutar un método o ejecutar los 17. Muestra el tipo de operador, los datos de entrada y el resultado reproducible. **Permutaciones / rutas** optimiza el ciclo de seis ciudades con la matriz de distancias del proyecto y permite comparar PMX, OX y CX; la mutación es por intercambio.

Tras cada ejecución se muestran la mejor solución, el valor objetivo, los operadores, la curva de convergencia y la tabla de estadísticas por generación. **Exportar historial a CSV** guarda las cuatro columnas de `resultado.historial` en la ruta elegida. La ejecución del motor se realiza en un hilo para mantener la ventana disponible. La semilla predeterminada `42` permite repetir una demostración.

## Cómo correr (Windows 11)

1. Descomprimir este ZIP.
2. Abrir PowerShell o terminal de VS Code en la carpeta `Algoritmo_Genetico_Simple`.
3. Ejecutar `py main.py` (o `python main.py`).
4. Elegir una opción:
   - **1:** ejemplos explicados en clase, por orden de página
   - **2:** resolver una función objetivo elegida por el usuario
   - **3:** optimizar una ruta con representación por permutación

La versión por consola no requiere `pip install` y sigue disponible sin abrir la interfaz.

También se puede ejecutar directamente:

```powershell
py main.py --ejemplos
py main.py --funcion "(x-3)**2+2" --objetivo min --minimo -10 --maximo 10
py main.py --funcion "-(x-2)**2+8" --objetivo max --generaciones 100
py main.py --funcion "x0**2+x1**2" --dim 2 --objetivo min
py main.py --funcion "sin(x)+0.05*x**2" --minimo -10 --maximo 10
py main.py --funcion "x0**2+x1**2" --dim 2 --representacion binaria --cruce uniforme
py main.py --ruta
```

**Importante:** si una expresión tiene varias variables, utiliza `x0`, `x1`, `x2`, etc. También se admite `x[0]`, `x[1]`. Para una única variable, `x` o `x0`. Operadores admitidos: `+`, `-`, `*`, `/`, `**`, `%`; funciones `sin`, `cos`, `tan`, `sqrt`, `log`, `exp`, `abs`, `min`, `max`, etc.; constantes `pi`, `e`. Introduce la expresión sin prefijo `f(x)=`.

## Configuración del AG

Cada ejecución tiene: número de generaciones, tamaño de población, probabilidad de cruce **Pc**, probabilidad de mutación **Pm**, selección, cruce, mutación, sustitución, elitismo y semilla aleatoria. El archivo `ag/motor.py` contiene `ConfigAG`, por si necesitas variar más parámetros.

| Representación | Cruces compatibles | Mutaciones compatibles |
|---|---|---|
| Real | uniforme, aritmético, plano, BLX-α | uniforme, no uniforme |
| Binaria | uniforme | inversión de bit (extra) |
| Permutación | PMX, OX, CX | por intercambio |

No todos los cruces son compatibles con todas las representaciones. Por ejemplo, el cruce aritmético no preserva permutaciones. Para permutaciones, la función objetivo se define como una función Python de la lista (ver `distancia_ruta` en `ag/objetivos.py`).

**Sustitución:** se incluye reemplazo *generacional* básico además de los dos operadores de sustitución de clase. El método `crowding` reemplaza al individuo más parecido de una muestra `CF`, sin exigir que el hijo sea más apto, como explica la presentación; el elitismo opcional protege individuos destacados.

## Explicación del ciclo

1. Se crea una población aleatoria de cromosomas, dentro de los límites.
2. Se decodifica cada cromosoma a la solución representada y se evalúa `f`.
3. La selección elige padres (ruleta, ranking lineal/no lineal, torneo o SUS).
4. Con probabilidad **Pc** se cruzan los padres, obteniendo descendientes.
5. Se mutan los descendientes según **Pm** y tipo de representación.
6. Se sustituye total/parcialmente la población (generacional, steady-state, crowding).
7. Se conserva el mejor resultado encontrado y se repite hasta completar las generaciones.
8. Se imprime el mejor resultado y se exporta `historial_numerico.csv` o `historial_permutacion.csv`.

Nota: en representación real, `Pm` se aplica **por gen**; en permutaciones se aplica **por cromosoma** (intercambio de dos posiciones). En binario se aplica **por bit**.

## Dos errores de los ejemplos impresos

- **Página 2, ranking lineal:** las probabilidades impresas `0.40, 0.32, 0.23, 0.15` suman **1.10**, no 1. Implementación: variante de ranking lineal normalizada con `amin=2-amax`, en la que `amax=1.6`, `m=4` da `0.4, 0.3, 0.2, 0.1`. Se conserva el concepto (depender del rango, no de la magnitud).
- **Página 12, PMX:** el hijo impreso `5 7 [3 4 5] 8 2 1` repite el 5, así que no es una permutación válida. Aplicando PMX con los mismos padres y cortes, el hijo correcto es `6 7 [3 4 5] 8 2 1`.
- **OX y CX:** solo aparecen en la lista de la **página 16**, sin explicación o ejemplo desarrollado. Se añadieron demostraciones con algoritmos estándar, marcadas como ejemplos adicionales.

## Pruebas

Desde la carpeta del proyecto:

```powershell
py -m unittest discover -s tests -v
```

