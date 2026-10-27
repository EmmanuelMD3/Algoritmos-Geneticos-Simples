"""Funcion objetivo segura desde una expresion aritmetica de usuario.

No utiliza eval sobre texto libre: valida todos los nodos sintacticos.
"""
from __future__ import annotations

import ast
import math
from typing import Callable

FUNCIONES = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "exp": math.exp, "floor": math.floor, "ceil": math.ceil,
    "abs": abs, "min": min, "max": max, "pow": pow,
}
CONSTANTES = {"pi": math.pi, "e": math.e}

# Matriz del ejemplo de rutas, compartida por la consola y la interfaz.
MATRIZ_DISTANCIAS_EJEMPLO = [
    [0, 3, 4, 8, 9, 5],
    [3, 0, 5, 6, 7, 4],
    [4, 5, 0, 3, 6, 8],
    [8, 6, 3, 0, 2, 7],
    [9, 7, 6, 2, 0, 4],
    [5, 4, 8, 7, 4, 0],
]
BINARIOS = {
    ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b, ast.Mod: lambda a, b: a % b,
}
UNARIOS = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}


def _compilar_arbol(nodo: ast.AST, dimensiones: int) -> Callable[[list[float]], float]:
    if isinstance(nodo, ast.Expression):
        return _compilar_arbol(nodo.body, dimensiones)
    if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
        valor = float(nodo.value)
        if not math.isfinite(valor) or abs(valor) > 1e100:
            raise ValueError("Constante numerica demasiado grande")
        return lambda x, v=valor: v
    if isinstance(nodo, ast.Name):
        nombre = nodo.id
        if nombre in CONSTANTES:
            return lambda x, v=CONSTANTES[nombre]: v
        if nombre == "x" and dimensiones == 1:
            return lambda x: x[0]
        if nombre.startswith("x") and nombre[1:].isdigit():
            indice = int(nombre[1:])
            if indice < dimensiones:
                return lambda x, i=indice: x[i]
        raise ValueError(f"Variable no permitida: {nombre}")
    if isinstance(nodo, ast.Subscript) and isinstance(nodo.value, ast.Name) and nodo.value.id == "x":
        if isinstance(nodo.slice, ast.Constant) and type(nodo.slice.value) is int:
            indice = nodo.slice.value
            if 0 <= indice < dimensiones:
                return lambda x, i=indice: x[i]
        raise ValueError("Solo se permite x[0], x[1], etc. dentro de la dimension")
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in UNARIOS:
        operador = UNARIOS[type(nodo.op)]
        func = _compilar_arbol(nodo.operand, dimensiones)
        return lambda x: operador(func(x))
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in BINARIOS:
        operador = BINARIOS[type(nodo.op)]
        izquierda = _compilar_arbol(nodo.left, dimensiones)
        derecha = _compilar_arbol(nodo.right, dimensiones)
        return lambda x: operador(izquierda(x), derecha(x))
    if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id in FUNCIONES:
        if nodo.keywords:
            raise ValueError("No se permiten argumentos por nombre")
        funcion = FUNCIONES[nodo.func.id]
        args = [_compilar_arbol(arg, dimensiones) for arg in nodo.args]
        if not args:
            raise ValueError("La funcion necesita argumentos")
        return lambda x: funcion(*(f(x) for f in args))
    raise ValueError("Expresion no permitida (usa operaciones aritmeticas y funciones autorizadas)")


def crear_funcion(expresion: str, dimensiones: int) -> Callable[[list[float]], float]:
    if dimensiones < 1:
        raise ValueError("dimensiones debe ser >= 1")
    try:
        arbol = ast.parse(expresion, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Expresion invalida: {exc.msg}") from exc
    funcion = _compilar_arbol(arbol, dimensiones)
    def objetivo(coordenadas: list[float]) -> float:
        if len(coordenadas) != dimensiones:
            raise ValueError("Cantidad de variables incorrecta")
        valor = float(funcion(coordenadas))
        if not math.isfinite(valor):
            raise ValueError("Resultado no finito")
        return valor
    return objetivo


def distancia_ruta(permuta: list[int], matriz: list[list[float]]) -> float:
    """Costo total de un ciclo: ejemplo simple de objetivo para permutaciones."""
    n = len(permuta)
    if len(matriz) != n or any(len(fila) != n for fila in matriz):
        raise ValueError("La matriz de distancias no es cuadrada")
    return sum(matriz[permuta[i]][permuta[(i + 1) % n]] for i in range(n))
