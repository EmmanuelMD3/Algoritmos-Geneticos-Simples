"""Demostracion reproducible de los ejemplos expuestos en 05 Hiperparametros.pdf."""
import random
from ag.cruce import uniforme, aritmetico, plano, blx_alfa, pmx, ox, cx
from ag.mutacion import intercambio, uniforme_real, no_uniforme_real
from ag.seleccion import (ruleta_probabilidades, ranking_lineal_probabilidades,
                          ranking_no_lineal_probabilidades,
                          muestreo_estocastico_universal, seleccionar)
from ag.sustitucion import steady_state, distancia


# La consola conserva su salida original. Estos casos permiten ejecutar cada
# demostracion de forma independiente desde la interfaz.
EJEMPLOS = (
    ("Ruleta proporcional", "Selección", "A=10, B=20, C=30, D=40"),
    ("Ranking lineal", "Selección", "A=10, B=20, C=30, D=40; amax=1.6"),
    ("Ranking no lineal", "Selección", "A=10, B=20, C=30, D=40; q=0.5"),
    ("Torneo binario", "Selección", "A=10, B=20, C=30, D=40; k=2"),
    ("Muestreo estocástico universal (SUS)", "Selección", "Probabilidades 0.1, 0.2, 0.3, 0.4; 4 elegidos"),
    ("Sustitución steady-state", "Sustitución", "A10, B20, C30, D40; hijos E25 y F35"),
    ("Factor de crowding", "Sustitución", "Nuevo 1011; candidatos 1010, 0010, 0101"),
    ("Cruce uniforme", "Cruce", "Padres 110010 y 001101; máscara 101010"),
    ("Cruce aritmético", "Cruce", "Padres (2, 8) y (6, 4); a=0.25"),
    ("Cruce plano", "Cruce", "Padres (2, 8) y (6, 4); semilla 42"),
    ("Cruce BLX-α", "Cruce", "Padres (2) y (6); α=0.5; semilla 42"),
    ("Cruce PMX", "Cruce", "Padres 12345678 y 37516824; cortes [3..5]"),
    ("Cruce OX", "Cruce", "Padres 12345678 y 37516824; cortes [3..5]"),
    ("Cruce CX", "Cruce", "Padres 12345678 y 37516824"),
    ("Mutación uniforme", "Mutación", "Cromosoma (2.5, 7, 1.2); límites [0, 10]; Pm=1"),
    ("Mutación no uniforme", "Mutación", "Cromosoma (4); límites [0, 10]; Pm=1; t=0 y t=90"),
    ("Mutación por intercambio", "Mutación", "Cromosoma 123456; Pm=1; semilla 42"),
)


def ejecutar_ejemplo(numero: int) -> str:
    """Ejecuta un caso de la presentación y devuelve su resultado legible."""
    if not 1 <= numero <= len(EJEMPLOS):
        raise ValueError("El número de ejemplo debe estar entre 1 y 17")
    rng = random.Random(42)
    valores = [10, 20, 30, 40]
    nombres = "ABCD"
    p1, p2 = [1, 2, 3, 4, 5, 6, 7, 8], [3, 7, 5, 1, 6, 8, 2, 4]
    if numero == 1:
        resultado = ruleta_probabilidades(valores)
    elif numero == 2:
        resultado = ranking_lineal_probabilidades(valores, amax=1.6)
    elif numero == 3:
        resultado = ranking_no_lineal_probabilidades(valores, q=0.5)
    elif numero == 4:
        indices = seleccionar(valores, 4, "torneo", True, rng, k=2)
        resultado = [nombres[i] for i in indices]
    elif numero == 5:
        indices = muestreo_estocastico_universal(ruleta_probabilidades(valores), 4, rng)
        resultado = [nombres[i] for i in indices]
    elif numero == 6:
        nuevos = steady_state([["A"], ["B"], ["C"], ["D"]], valores,
                              [["E"], ["F"]], True)
        resultado = [individuo[0] for individuo in nuevos]
    elif numero == 7:
        nuevo = [1, 0, 1, 1]
        candidatos = [[1, 0, 1, 0], [0, 0, 1, 0], [0, 1, 0, 1]]
        distancias = [distancia(nuevo, c, "binaria") for c in candidatos]
        resultado = f"Distancias: {distancias}; reemplaza {nombres[distancias.index(min(distancias))]}"
    elif numero == 8:
        resultado = uniforme([1, 1, 0, 0, 1, 0], [0, 0, 1, 1, 0, 1], rng,
                             mascara=[1, 0, 1, 0, 1, 0])
    elif numero == 9:
        resultado = aritmetico([2, 8], [6, 4], 0.25)
    elif numero == 10:
        resultado = plano([2, 8], [6, 4], rng)
    elif numero == 11:
        resultado = blx_alfa([2], [6], 0.5, rng)
    elif numero == 12:
        resultado = pmx(p1, p2, rng, cortes=(2, 5))
    elif numero == 13:
        resultado = ox(p1, p2, rng, cortes=(2, 5))
    elif numero == 14:
        resultado = cx(p1, p2)
    elif numero == 15:
        resultado = uniforme_real([2.5, 7.0, 1.2], [(0, 10)] * 3, 1, rng)
    elif numero == 16:
        inicio = no_uniforme_real([4], [(0, 10)], 1, 0, 100, random.Random(42))
        final = no_uniforme_real([4], [(0, 10)], 1, 90, 100, random.Random(42))
        resultado = f"t=0: {inicio}; t=90: {final}"
    else:
        resultado = intercambio([1, 2, 3, 4, 5, 6], 1, rng)
    return str(resultado)


def ejecutar_ejemplos() -> None:
    rng = random.Random(42)
    print("\n" + "=" * 73)
    print("EJEMPLOS DE LA PRESENTACION: 05 HIPERPARAMETROS (PAGINAS 1-16)")
    print("=" * 73)
    valores = [10, 20, 30, 40]  # A, B, C, D
    nombres = ["A", "B", "C", "D"]

    print("\n[1] Ruleta proporcional (pag. 1)")
    print("A=10 B=20 C=30 D=40 ->", ruleta_probabilidades(valores))
    print("Con r=0.52 se elige C (acumuladas: 0.10, 0.30, 0.60, 1.00).")

    print("\n[2] Ranking lineal (pag. 2)")
    p = ranking_lineal_probabilidades(valores, amax=1.6)
    print("D, C, B, A ->", [round(p[i], 4) for i in (3, 2, 1, 0)])
    print("Nota: el PDF propone 0.40,0.32,0.23,0.15; suman 1.10.")
    print("Se implementa la formula normalizada habitual (amin=2-amax).")

    print("\n[3] Ranking no lineal (pag. 3)")
    p = ranking_no_lineal_probabilidades(valores, q=0.5)
    print("D, C, B, A ->", [round(p[i], 4) for i in (3, 2, 1, 0)])

    print("\n[4] Torneo binario (pag. 4)")
    print("Torneo A(10) vs C(30) -> C; B(20) vs D(40) -> D")
    print("El motor tambien sortea competidores al azar y admite k variable.")

    print("\n[5] Muestreo estocastico universal (pag. 5)")
    seleccionados = muestreo_estocastico_universal(ruleta_probabilidades(valores), 4, rng)
    print("Cuatro punteros espaciados 1/4 ->", [nombres[i] for i in seleccionados])

    print("\n[6] Sustitucion steady-state (pag. 6)")
    nueva = steady_state([["A"], ["B"], ["C"], ["D"]], valores, [["E"], ["F"]], True)
    print("A10,B20,C30,D40 + E25,F35 ->", [x[0] for x in nueva])

    print("\n[7] Factor de crowding (pag. 7)")
    nuevo = [1, 0, 1, 1]
    candidatos = [[1, 0, 1, 0], [0, 0, 1, 0], [0, 1, 0, 1]]
    print("N=1011; distancias Hamming con A,B,C:",
          [distancia(nuevo, c, "binaria") for c in candidatos], "-> reemplaza A")

    print("\n[8] Cruce uniforme (pag. 8)")
    h1, h2 = uniforme([1, 1, 0, 0, 1, 0], [0, 0, 1, 1, 0, 1], rng,
                      mascara=[1, 0, 1, 0, 1, 0])
    print("Mascara=101010 -> H1=", "".join(map(str, h1)), "H2=", "".join(map(str, h2)))

    print("\n[9] Cruce aritmetico (pag. 9)")
    print("P1=(2,8), P2=(6,4), a=0.25 ->", aritmetico([2, 8], [6, 4], 0.25))

    print("\n[10] Cruce plano (pag. 10)")
    print("P1=(2,8), P2=(6,4) -> gen1 en [2,6], gen2 en [4,8]")
    print("Un hijo valido mostrado en clase: (3.1,7.2)")

    print("\n[11] Cruce BLX-alfa (pag. 11)")
    print("p1=2, p2=6, alfa=0.5 -> I=4, intervalo [0,8], p.ej. h=7.1")

    print("\n[12] Cruce PMX (pag. 12)")
    p1, p2 = [1, 2, 3, 4, 5, 6, 7, 8], [3, 7, 5, 1, 6, 8, 2, 4]
    h1, h2 = pmx(p1, p2, rng, cortes=(2, 5))
    print("P1=", p1, "P2=", p2)
    print("Cortes [3..5] -> H1=", h1, "H2=", h2)
    print("Correccion: la diapositiva repite el 5; el hijo valido inicia con 6.")

    print("\n[13] OX (pag. 16, listado sin desarrollo)")
    print("Ejemplo adicional con los padres anteriores ->", ox(p1, p2, rng, cortes=(2, 5)))

    print("\n[14] CX (pag. 16, listado sin desarrollo)")
    print("Ejemplo adicional con los padres anteriores ->", cx(p1, p2))

    print("\n[15] Mutacion uniforme (pag. 13)")
    print("(2.5,7.0,1.2), mutar gen 2 a 3.4 -> (2.5,3.4,1.2)")

    print("\n[16] Mutacion no uniforme (pag. 14)")
    delta_ini = 6 * (1 - 0.5 ** (1 - 0 / 100))
    delta_fin = 6 * (1 - 0.5 ** (1 - 90 / 100))
    print(f"x=4; t=0 -> x'={4+delta_ini:.3f}; t=90 -> x'={4+delta_fin:.3f}")

    print("\n[17] Mutacion por intercambio (pag. 15)")
    datos = [1, 2, 3, 4, 5, 6]
    datos[1], datos[4] = datos[4], datos[1]
    print("Intercambiar posiciones 2 y 5 ->", datos)
    print("\nOperador extra: inversion de bit para completar un AG con binarios.")
    print("=" * 73 + "\n")
