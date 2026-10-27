"""Mutaciones incluidas en la presentacion, mas bit-flip necesario para binarios."""
from __future__ import annotations

import random
from typing import Sequence


def uniforme_real(cromosoma: Sequence[float], limites: Sequence[tuple[float, float]],
                  probabilidad: float, rng: random.Random) -> list[float]:
    salida = list(cromosoma)
    for i, (bajo, alto) in enumerate(limites):
        if rng.random() < probabilidad:
            salida[i] = rng.uniform(bajo, alto)
    return salida


def no_uniforme_real(cromosoma: Sequence[float], limites: Sequence[tuple[float, float]],
                     probabilidad: float, generacion: int, total_generaciones: int,
                     rng: random.Random, b: float = 1.0) -> list[float]:
    """Delta = y*(1-r**((1-t/T)**b)), con direccion aleatoria."""
    if b <= 0 or total_generaciones <= 0:
        raise ValueError("b y total_generaciones deben ser positivos")
    t = max(0, min(generacion, total_generaciones))
    exponente = (1 - t / total_generaciones) ** b
    salida = list(cromosoma)
    for i, (lb, ub) in enumerate(limites):
        if rng.random() < probabilidad:
            actual = salida[i]
            subir = rng.random() < 0.5
            distancia = (ub - actual) if subir else (actual - lb)
            delta = distancia * (1 - rng.random() ** exponente)
            salida[i] = max(lb, min(ub, actual + delta if subir else actual - delta))
    return salida


def intercambio(cromosoma: Sequence[int], probabilidad: float,
                rng: random.Random) -> list[int]:
    salida = list(cromosoma)
    if len(salida) >= 2 and rng.random() < probabilidad:
        i, j = rng.sample(range(len(salida)), 2)
        salida[i], salida[j] = salida[j], salida[i]
    return salida


def inversion_bit(cromosoma: Sequence[int], probabilidad: float,
                  rng: random.Random) -> list[int]:
    return [1 - bit if rng.random() < probabilidad else bit for bit in cromosoma]
