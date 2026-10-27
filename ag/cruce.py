"""Cruces binarios/reales y de permutaciones."""
from __future__ import annotations

import random
from typing import Sequence


def uniforme(p1: Sequence, p2: Sequence, rng: random.Random,
             mascara: Sequence[int] | None = None) -> tuple[list, list]:
    if len(p1) != len(p2):
        raise ValueError("Los cromosomas deben medir lo mismo")
    if mascara is None:
        mascara = [rng.randint(0, 1) for _ in p1]
    if len(mascara) != len(p1):
        raise ValueError("Longitud de mascara incorrecta")
    h1 = [a if m else b for a, b, m in zip(p1, p2, mascara)]
    h2 = [b if m else a for a, b, m in zip(p1, p2, mascara)]
    return h1, h2


def aritmetico(p1: Sequence[float], p2: Sequence[float], a: float) -> tuple[list[float], list[float]]:
    if not 0 <= a <= 1:
        raise ValueError("a debe estar en [0,1]")
    h1 = [a * x + (1 - a) * y for x, y in zip(p1, p2)]
    h2 = [a * y + (1 - a) * x for x, y in zip(p1, p2)]
    return h1, h2


def plano(p1: Sequence[float], p2: Sequence[float], rng: random.Random) -> tuple[list[float], list[float]]:
    def hijo():
        return [rng.uniform(min(x, y), max(x, y)) for x, y in zip(p1, p2)]
    return hijo(), hijo()


def blx_alfa(p1: Sequence[float], p2: Sequence[float], alfa: float,
             rng: random.Random, limites: Sequence[tuple[float, float]] | None = None
             ) -> tuple[list[float], list[float]]:
    if alfa < 0:
        raise ValueError("alfa debe ser >= 0")
    def hijo():
        out = []
        for i, (x, y) in enumerate(zip(p1, p2)):
            bajo, alto = min(x, y), max(x, y)
            longitud = alto - bajo
            valor = rng.uniform(bajo - alfa * longitud, alto + alfa * longitud)
            if limites is not None:
                lb, ub = limites[i]
                valor = max(lb, min(ub, valor))
            out.append(valor)
        return out
    return hijo(), hijo()


def _verificar_permutaciones(p1: Sequence[int], p2: Sequence[int]):
    if len(p1) != len(p2) or len(p1) < 2 or len(set(p1)) != len(p1) or set(p1) != set(p2):
        raise ValueError("Se requieren dos permutaciones validas con los mismos elementos")


def _cortes(n: int, rng: random.Random, cortes: tuple[int, int] | None):
    if cortes is None:
        a, b = sorted(rng.sample(range(n + 1), 2))
        if a == b:
            b = min(n, a + 1)
        return a, b
    a, b = cortes
    if not (0 <= a < b <= n):
        raise ValueError("Los cortes deben cumplir 0 <= a < b <= n")
    return a, b


def _pmx_un_hijo(p1: Sequence[int], p2: Sequence[int], a: int, b: int) -> list[int]:
    n = len(p1)
    hijo = [None] * n
    hijo[a:b] = p1[a:b]
    posicion_p2 = {valor: i for i, valor in enumerate(p2)}
    for i in range(a, b):
        valor = p2[i]
        if valor in hijo:
            continue
        posicion = i
        while True:
            posicion = posicion_p2[p1[posicion]]
            if hijo[posicion] is None:
                hijo[posicion] = valor
                break
    for i in range(n):
        if hijo[i] is None:
            hijo[i] = p2[i]
    return hijo


def pmx(p1: Sequence[int], p2: Sequence[int], rng: random.Random,
        cortes: tuple[int, int] | None = None) -> tuple[list[int], list[int]]:
    _verificar_permutaciones(p1, p2)
    a, b = _cortes(len(p1), rng, cortes)
    return _pmx_un_hijo(p1, p2, a, b), _pmx_un_hijo(p2, p1, a, b)


def _ox_un_hijo(p1: Sequence[int], p2: Sequence[int], a: int, b: int) -> list[int]:
    n = len(p1)
    hijo = [None] * n
    hijo[a:b] = p1[a:b]
    faltantes = [valor for valor in (list(p2[b:]) + list(p2[:b])) if valor not in hijo]
    posicion = b % n
    for valor in faltantes:
        while hijo[posicion] is not None:
            posicion = (posicion + 1) % n
        hijo[posicion] = valor
    return hijo


def ox(p1: Sequence[int], p2: Sequence[int], rng: random.Random,
       cortes: tuple[int, int] | None = None) -> tuple[list[int], list[int]]:
    _verificar_permutaciones(p1, p2)
    a, b = _cortes(len(p1), rng, cortes)
    return _ox_un_hijo(p1, p2, a, b), _ox_un_hijo(p2, p1, a, b)


def cx(p1: Sequence[int], p2: Sequence[int]) -> tuple[list[int], list[int]]:
    """Cycle crossover; alterna la procedencia de cada ciclo."""
    _verificar_permutaciones(p1, p2)
    n = len(p1)
    h1, h2 = [None] * n, [None] * n
    indice_p1 = {valor: i for i, valor in enumerate(p1)}
    vistos = set()
    numero_ciclo = 0
    for inicio in range(n):
        if inicio in vistos:
            continue
        posicion = inicio
        while posicion not in vistos:
            vistos.add(posicion)
            if numero_ciclo % 2 == 0:
                h1[posicion], h2[posicion] = p1[posicion], p2[posicion]
            else:
                h1[posicion], h2[posicion] = p2[posicion], p1[posicion]
            posicion = indice_p1[p2[posicion]]
        numero_ciclo += 1
    return h1, h2


def cruzar(p1, p2, metodo: str, rng: random.Random, a: float = 0.25,
           alfa: float = 0.5, limites=None):
    if metodo == "uniforme":
        return uniforme(p1, p2, rng)
    if metodo == "aritmetico":
        return aritmetico(p1, p2, a)
    if metodo == "plano":
        return plano(p1, p2, rng)
    if metodo == "blx":
        return blx_alfa(p1, p2, alfa, rng, limites)
    if metodo == "pmx":
        return pmx(p1, p2, rng)
    if metodo == "ox":
        return ox(p1, p2, rng)
    if metodo == "cx":
        return cx(p1, p2)
    raise ValueError(f"Cruce no reconocido: {metodo}")
