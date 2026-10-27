"""Sustitucion steady-state y por factor de crowding."""
from __future__ import annotations

import random
from typing import Callable, Sequence


def steady_state(poblacion: Sequence[list], valores: Sequence[float],
                 descendientes: Sequence[list], maximizar: bool) -> list[list]:
    cantidad = len(descendientes)
    if cantidad > len(poblacion):
        raise ValueError("Demasiados descendientes para sustitucion steady-state")
    mejores = sorted(range(len(poblacion)), key=lambda i: valores[i], reverse=maximizar)
    sobrevivientes = [list(poblacion[i]) for i in mejores[:len(poblacion) - cantidad]]
    return sobrevivientes + [list(h) for h in descendientes]


def distancia(a: Sequence, b: Sequence, representacion: str) -> float:
    if representacion == "real":
        return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
    return sum(x != y for x, y in zip(a, b))


def crowding(poblacion: Sequence[list], descendientes: Sequence[list],
             cf: int, representacion: str, rng: random.Random) -> list[list]:
    """Reemplaza al mas parecido de una muestra local, como pagina 7."""
    if cf < 1 or cf > len(poblacion):
        raise ValueError("CF debe estar entre 1 y el tamano de la poblacion")
    nueva = [list(individuo) for individuo in poblacion]
    for hijo in descendientes:
        candidatos = rng.sample(range(len(nueva)), cf)
        similar = min(candidatos, key=lambda i: distancia(nueva[i], hijo, representacion))
        nueva[similar] = list(hijo)
    return nueva
