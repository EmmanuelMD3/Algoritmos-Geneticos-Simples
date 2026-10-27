"""Validación de entradas de la interfaz; independiente de Tkinter."""
from __future__ import annotations

import math

from ag.motor import ConfigAG
from ag.objetivos import crear_funcion, distancia_ruta, MATRIZ_DISTANCIAS_EJEMPLO


CRUCES = {"real": ("uniforme", "aritmetico", "plano", "blx"),
          "binaria": ("uniforme",), "permutacion": ("pmx", "ox", "cx")}
MUTACIONES = {"real": ("uniforme", "no_uniforme"),
              "binaria": ("bitflip",), "permutacion": ("intercambio",)}


def _entero(campos: dict[str, str], clave: str, etiqueta: str) -> int:
    try:
        return int(campos[clave].strip())
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{etiqueta}: escribe un número entero válido") from exc


def _real(campos: dict[str, str], clave: str, etiqueta: str) -> float:
    try:
        valor = float(campos[clave].strip())
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{etiqueta}: escribe un número válido") from exc
    if not math.isfinite(valor):
        raise ValueError(f"{etiqueta}: se requiere un número finito")
    return valor


def interpretar_limites(dim: int, inferior: str, superior: str,
                        especificos: str) -> list[tuple[float, float]]:
    """Acepta límites comunes o pares 'inferior:superior' separados por ;."""
    if dim < 1:
        raise ValueError("El número de variables debe ser al menos 1")
    if especificos.strip():
        partes = [p.strip() for p in especificos.split(";")]
        if len(partes) != dim:
            raise ValueError(f"Escribe exactamente {dim} pares de límites, separados por ;")
        limites = []
        for i, parte in enumerate(partes):
            trozos = parte.split(":")
            if len(trozos) != 2:
                raise ValueError(f"Límites de x{i}: usa el formato inferior:superior")
            try:
                lb, ub = (float(t.strip()) for t in trozos)
            except ValueError as exc:
                raise ValueError(f"Límites de x{i}: escribe números válidos") from exc
            limites.append((lb, ub))
    else:
        try:
            lb, ub = float(inferior.strip()), float(superior.strip())
        except ValueError as exc:
            raise ValueError("Escribe límites inferior y superior válidos") from exc
        limites = [(lb, ub)] * dim
    for i, (lb, ub) in enumerate(limites):
        if not (math.isfinite(lb) and math.isfinite(ub) and lb < ub):
            raise ValueError(f"Límites de x{i}: deben ser finitos y el inferior menor que el superior")
    return limites


def preparar_optimizacion(campos: dict[str, str]):
    """Devuelve (función, configuración) tras validar todos los controles."""
    dim = _entero(campos, "dim", "Número de variables")
    if dim < 1:
        raise ValueError("El número de variables debe ser al menos 1")
    expresion = campos.get("expresion", "").strip()
    if not expresion:
        raise ValueError("Escribe una función objetivo")
    funcion = crear_funcion(expresion, dim)
    limites = interpretar_limites(dim, campos.get("inferior", ""),
                                  campos.get("superior", ""),
                                  campos.get("especificos", ""))
    config = ConfigAG(
        representacion=campos["representacion"],
        tam_poblacion=_entero(campos, "poblacion", "Población"),
        generaciones=_entero(campos, "generaciones", "Generaciones"),
        maximizar=campos["objetivo"] == "max",
        limites=limites,
        bits_por_variable=_entero(campos, "bits", "Bits por variable"),
        seleccion=campos["seleccion"], cruce=campos["cruce"],
        mutacion=campos["mutacion"], sustitucion=campos["sustitucion"],
        prob_cruce=_real(campos, "pc", "Probabilidad de cruce"),
        prob_mutacion=_real(campos, "pm", "Probabilidad de mutación"),
        elitismo=_entero(campos, "elitismo", "Elitismo"),
        k_torneo=_entero(campos, "k", "Tamaño de torneo"),
        amax=_real(campos, "amax", "Ranking lineal amax"),
        q=_real(campos, "q", "Ranking no lineal q"),
        a_aritmetico=_real(campos, "a_aritmetico", "Peso aritmético"),
        alfa_blx=_real(campos, "alfa_blx", "Alfa BLX"),
        b_mutacion=_real(campos, "b_mutacion", "Exponente de mutación"),
        factor_crowding=_entero(campos, "cf", "Factor de crowding"),
        cantidad_reemplazos=_entero(campos, "reemplazos", "Cantidad de reemplazos"),
        semilla=_entero(campos, "semilla", "Semilla"),
    )
    config.validar()
    return funcion, config


def preparar_ruta(campos: dict[str, str]):
    config = ConfigAG(
        representacion="permutacion", num_elementos=len(MATRIZ_DISTANCIAS_EJEMPLO),
        seleccion=campos["seleccion"], cruce=campos["cruce"],
        mutacion="intercambio", sustitucion=campos["sustitucion"],
        tam_poblacion=_entero(campos, "poblacion", "Población"),
        generaciones=_entero(campos, "generaciones", "Generaciones"),
        prob_cruce=_real(campos, "pc", "Probabilidad de cruce"),
        prob_mutacion=_real(campos, "pm", "Probabilidad de mutación"),
        elitismo=_entero(campos, "elitismo", "Elitismo"),
        k_torneo=_entero(campos, "k", "Tamaño de torneo"),
        factor_crowding=_entero(campos, "cf", "Factor de crowding"),
        cantidad_reemplazos=_entero(campos, "reemplazos", "Cantidad de reemplazos"),
        semilla=_entero(campos, "semilla", "Semilla"),
    )
    config.validar()
    return lambda ruta: distancia_ruta(ruta, MATRIZ_DISTANCIAS_EJEMPLO), config
