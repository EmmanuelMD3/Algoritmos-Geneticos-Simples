"""Ejecutar: python main.py (menu) o python main.py --ejemplos."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ag.motor import ConfigAG, ejecutar_ag
from ag.objetivos import crear_funcion, distancia_ruta, MATRIZ_DISTANCIAS_EJEMPLO
from ejemplos import ejecutar_ejemplos

BASE = Path(__file__).resolve().parent


def guardar_csv(historial, nombre: str = "historial.csv") -> Path:
    ruta = BASE / nombre
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=["generacion", "mejor_generacion", "mejor_historico", "promedio"])
        escritor.writeheader()
        escritor.writerows(historial)
    return ruta


def imprimir_resultado(resultado, config, archivo: str):
    print("\n" + "=" * 65)
    print("RESULTADO DEL ALGORITMO GENETICO")
    print("Representacion:", config.representacion)
    print("Objetivo:", "MAXIMIZAR" if config.maximizar else "MINIMIZAR")
    print("Poblacion:", config.tam_poblacion, "Generaciones:", config.generaciones)
    print("Seleccion:", config.seleccion, "Cruce:", config.cruce)
    print("Mutacion:", config.mutacion, "Sustitucion:", config.sustitucion)
    print("Mejor solucion:", [round(float(x), 6) for x in resultado.mejor_solucion])
    print("Mejor valor f(x):", round(resultado.mejor_valor, 10))
    print("\nEvolucion (cada ~10% de las generaciones):")
    paso = max(1, config.generaciones // 10)
    for fila in resultado.historial:
        if fila["generacion"] % paso == 0 or fila["generacion"] == config.generaciones:
            print(f" Gen {fila['generacion']:>4} | Mejor historico: {fila['mejor_historico']:.8f}"
                  f" | Promedio: {fila['promedio']:.8f}")
    print("Historial exportado:", guardar_csv(resultado.historial, archivo))
    print("=" * 65)


def ejemplo_ruta():
    config = ConfigAG(representacion="permutacion", num_elementos=6,
                      seleccion="torneo", cruce="ox", mutacion="intercambio",
                      sustitucion="generacional", maximizar=False, semilla=42,
                      prob_mutacion=0.25, generaciones=80)
    resultado = ejecutar_ag(lambda p: distancia_ruta(p, MATRIZ_DISTANCIAS_EJEMPLO), config)
    imprimir_resultado(resultado, config, "historial_permutacion.csv")
    print("Ruta usando indices de ciudad 0-5; regresa a la primera.")


def correr_numerica(expresion: str, dim: int, limites: list[tuple[float, float]],
                    representacion: str = "real", maximizar: bool = False,
                    seleccion: str = "torneo", cruce: str | None = None,
                    mutacion: str | None = None, sustitucion: str = "generacional",
                    poblacion: int = 80, generaciones: int = 120,
                    prob_cruce: float = 0.85, prob_mutacion: float = 0.10,
                    semilla: int = 42, k_torneo: int = 3, elitismo: int = 1,
                    amax: float = 1.6, q: float = 0.5, alfa_blx: float = 0.5,
                    a_aritmetico: float = 0.25, cf: int = 3,
                    reemplazos: int = 10):
    funcion = crear_funcion(expresion, dim)
    if representacion == "real":
        cruce = cruce or "blx"
        mutacion = mutacion or "no_uniforme"
    else:
        cruce = cruce or "uniforme"
        mutacion = mutacion or "bitflip"
    config = ConfigAG(representacion=representacion, tam_poblacion=poblacion,
                      generaciones=generaciones, maximizar=maximizar, limites=limites,
                      seleccion=seleccion, cruce=cruce, mutacion=mutacion,
                      sustitucion=sustitucion, prob_cruce=prob_cruce,
                      prob_mutacion=prob_mutacion, semilla=semilla,
                      k_torneo=k_torneo, elitismo=elitismo, amax=amax, q=q,
                      alfa_blx=alfa_blx, a_aritmetico=a_aritmetico,
                      factor_crowding=cf, cantidad_reemplazos=reemplazos)
    print(f"\nFuncion: {expresion}")
    resultado = ejecutar_ag(funcion, config)
    imprimir_resultado(resultado, config, "historial_numerico.csv")
    return resultado


def preguntar(texto: str, defecto: str) -> str:
    valor = input(f"{texto} [{defecto}]: ").strip()
    return valor if valor else defecto


def configuracion_interactiva():
    print("\nOPTIMIZACION DE CUALQUIER FUNCION CON UN OBJETIVO")
    print("Expresiones: (x-3)**2+2, sin(x)+x**2, x0**2+x1**2")
    dim = int(preguntar("Numero de variables (dimensiones)", "1"))
    if dim < 1:
        raise ValueError("Se requiere al menos una dimension")
    ejemplo = "(x-3)**2+2" if dim == 1 else "+".join(f"x{i}**2" for i in range(dim))
    expresion = preguntar("Funcion objetivo", ejemplo)
    inf = float(preguntar("Limite inferior comun", "-10"))
    sup = float(preguntar("Limite superior comun", "10"))
    limites = [(inf, sup) for _ in range(dim)]
    print("Se admiten dominios diferentes por variable, si modificas limites en el codigo.")
    modo = preguntar("Objetivo (min/max)", "min").lower()
    representacion = preguntar("Representacion (real/binaria)", "real").lower()
    if representacion not in ("real", "binaria") or modo not in ("min", "max"):
        raise ValueError("Modo o representacion no valido")
    print("Seleccion: ruleta, ranking_lineal, ranking_no_lineal, torneo, sus")
    seleccion = preguntar("Metodo seleccion", "torneo").lower()
    print("Cruce real: uniforme, aritmetico, plano, blx | binaria: uniforme")
    cruce = preguntar("Cruce", "blx" if representacion == "real" else "uniforme").lower()
    print("Mutacion real: uniforme, no_uniforme | binaria: bitflip")
    mutacion = preguntar("Mutacion", "no_uniforme" if representacion == "real" else "bitflip").lower()
    sustitucion = preguntar("Sustitucion (generacional/steady_state/crowding)", "generacional").lower()
    poblacion = int(preguntar("Tamano poblacion", "80"))
    generaciones = int(preguntar("Numero de generaciones", "120"))
    pc = float(preguntar("Probabilidad de cruce Pc (0..1)", "0.85"))
    pm = float(preguntar("Probabilidad de mutacion Pm (0..1)", "0.10"))
    semilla = int(preguntar("Semilla aleatoria", "42"))
    k = int(preguntar("Torneo k", "3")) if seleccion == "torneo" else 3
    amax = float(preguntar("Ranking lineal amax", "1.6")) if seleccion == "ranking_lineal" else 1.6
    q = float(preguntar("Ranking no lineal q", "0.5")) if seleccion == "ranking_no_lineal" else 0.5
    a_aritmetico = float(preguntar("Peso del cruce aritmetico", "0.25")) if cruce == "aritmetico" else 0.25
    alfa_blx = float(preguntar("BLX alfa", "0.5")) if cruce == "blx" else 0.5
    cf = int(preguntar("Factor crowding CF", "3")) if sustitucion == "crowding" else 3
    reemplazos = (int(preguntar("Cuantos individuos sustituir en cada generacion", "10"))
                  if sustitucion != "generacional" else 10)
    correr_numerica(expresion, dim, limites, representacion, modo == "max",
                   seleccion, cruce, mutacion, sustitucion, poblacion, generaciones,
                   pc, pm, semilla, k, 1, amax, q, alfa_blx, a_aritmetico,
                   cf, reemplazos)


def menu():
    while True:
        print("\n======== ALGORITMO GENETICO SIMPLE ========")
        print("1. Ejecutar los 17 ejemplos de la presentacion")
        print("2. Optimizar cualquier funcion numerica (1 o varias variables)")
        print("3. Ejemplo de permutaciones / ruta (PMX, OX, CX)")
        print("0. Salir")
        opcion = input("Elige una opcion: ").strip()
        try:
            if opcion == "1":
                ejecutar_ejemplos()
            elif opcion == "2":
                configuracion_interactiva()
            elif opcion == "3":
                ejemplo_ruta()
            elif opcion == "0":
                break
            else:
                print("Opcion no valida")
        except (ValueError, EOFError) as exc:
            print("Error:", exc)


def main():
    parser = argparse.ArgumentParser(description="Algoritmo genetico simple configurable")
    parser.add_argument("--ejemplos", action="store_true", help="Mostrar ejemplos de la presentacion")
    parser.add_argument("--ruta", action="store_true", help="Optimizar una ruta de ejemplo")
    parser.add_argument("--funcion", type=str, help="Funcion objetivo, p.ej. '(x-3)**2+2'")
    parser.add_argument("--dim", type=int, default=1, help="Cantidad de variables")
    parser.add_argument("--minimo", type=float, default=-10, help="Limite inferior de cada variable")
    parser.add_argument("--maximo", type=float, default=10, help="Limite superior de cada variable")
    parser.add_argument("--objetivo", choices=["min", "max"], default="min")
    parser.add_argument("--representacion", choices=["real", "binaria"], default="real")
    parser.add_argument("--seleccion", choices=["ruleta", "ranking_lineal", "ranking_no_lineal", "torneo", "sus"], default="torneo")
    parser.add_argument("--cruce", choices=["uniforme", "aritmetico", "plano", "blx"], default=None)
    parser.add_argument("--mutacion", choices=["uniforme", "no_uniforme", "bitflip"], default=None)
    parser.add_argument("--sustitucion", choices=["generacional", "steady_state", "crowding"], default="generacional")
    parser.add_argument("--poblacion", type=int, default=80)
    parser.add_argument("--generaciones", type=int, default=120)
    parser.add_argument("--pc", type=float, default=0.85)
    parser.add_argument("--pm", type=float, default=0.10)
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args()
    if args.ejemplos:
        ejecutar_ejemplos()
    elif args.ruta:
        ejemplo_ruta()
    elif args.funcion:
        correr_numerica(args.funcion, args.dim,
                        [(args.minimo, args.maximo)] * args.dim,
                        args.representacion, args.objetivo == "max", args.seleccion,
                        args.cruce, args.mutacion, args.sustitucion,
                        args.poblacion, args.generaciones, args.pc, args.pm,
                        args.semilla)
    else:
        menu()


if __name__ == "__main__":
    main()
