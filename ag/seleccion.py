"""Cinco operadores de seleccion de la presentacion."""
from __future__ import annotations

from bisect import bisect_left
import random
from typing import Sequence


def _normalizar(pesos: Sequence[float]) -> list[float]:
    total = sum(pesos)
    if total <= 0:
        return [1.0 / len(pesos)] * len(pesos)
    return [p / total for p in pesos]


def ruleta_probabilidades(valores: Sequence[float], maximizar: bool = True) -> list[float]:
    """En maximo con aptitudes >= 0 usa exactamente p_i=f_i/suma(f).

    En otros casos realiza una transformacion a pesos no negativos.
    """
    if not valores:
        raise ValueError("Se requiere una poblacion no vacia")
    if maximizar and min(valores) >= 0 and sum(valores) > 0:
        pesos = list(valores)
    elif maximizar:
        minimo = min(valores)
        pesos = [v - minimo + 1.0 for v in valores]
    else:
        maximo = max(valores)
        pesos = [maximo - v + 1.0 for v in valores]
    return _normalizar(pesos)


def ranking_lineal_probabilidades(
    valores: Sequence[float], maximizar: bool = True, amax: float = 1.6
) -> list[float]:
    """Ranking lineal normalizado. amin=2-amax, 1<=amax<=2.

    La pagina 2 de la presentacion tiene probabilidades que suman 1.10;
    aqui se usa la variante matematicamente valida que suma 1.
    """
    if not (1.0 <= amax <= 2.0):
        raise ValueError("amax debe estar en [1, 2]")
    m = len(valores)
    if not m:
        raise ValueError("Se requiere una poblacion no vacia")
    if m == 1:
        return [1.0]
    orden = sorted(range(m), key=lambda i: valores[i], reverse=maximizar)
    salida = [0.0] * m
    for rango, indice in enumerate(orden):
        salida[indice] = (amax - 2 * (amax - 1) * rango / (m - 1)) / m
    return _normalizar(salida)


def ranking_no_lineal_probabilidades(
    valores: Sequence[float], maximizar: bool = True, q: float = 0.5
) -> list[float]:
    if not (0 < q <= 1):
        raise ValueError("q debe estar en (0, 1]")
    if not valores:
        raise ValueError("Se requiere una poblacion no vacia")
    orden = sorted(range(len(valores)), key=lambda i: valores[i], reverse=maximizar)
    pesos = [0.0] * len(valores)
    for rango, indice in enumerate(orden):
        pesos[indice] = q * (1 - q) ** rango
    return _normalizar(pesos)


def muestreo_estocastico_universal(
    probabilidades: Sequence[float], cantidad: int, rng: random.Random
) -> list[int]:
    if cantidad < 1:
        raise ValueError("cantidad debe ser positiva")
    probs = _normalizar(probabilidades)
    acumulados = []
    s = 0.0
    for p in probs:
        s += p
        acumulados.append(s)
    salto = 1.0 / cantidad
    inicio = rng.random() * salto
    return [min(bisect_left(acumulados, inicio + i * salto), len(probs) - 1)
            for i in range(cantidad)]


def seleccionar(
    valores: Sequence[float], cantidad: int, metodo: str, maximizar: bool,
    rng: random.Random, k: int = 2, amax: float = 1.6, q: float = 0.5
) -> list[int]:
    """Devuelve indices, que pueden repetirse entre sorteos."""
    if not valores or cantidad < 1:
        raise ValueError("Se requieren individuos y cantidad positiva")
    if metodo == "torneo":
        if not 1 <= k <= len(valores):
            raise ValueError("k debe estar entre 1 y el tamano poblacional")
        indices = []
        for _ in range(cantidad):
            competidores = rng.sample(range(len(valores)), k)
            ganador = (max if maximizar else min)(competidores, key=lambda i: valores[i])
            indices.append(ganador)
        return indices
    if metodo == "ruleta":
        p = ruleta_probabilidades(valores, maximizar)
    elif metodo == "ranking_lineal":
        p = ranking_lineal_probabilidades(valores, maximizar, amax)
    elif metodo == "ranking_no_lineal":
        p = ranking_no_lineal_probabilidades(valores, maximizar, q)
    elif metodo == "sus":
        p = ruleta_probabilidades(valores, maximizar)
        return muestreo_estocastico_universal(p, cantidad, rng)
    else:
        raise ValueError(f"Seleccion no reconocida: {metodo}")
    return rng.choices(range(len(valores)), weights=p, k=cantidad)
