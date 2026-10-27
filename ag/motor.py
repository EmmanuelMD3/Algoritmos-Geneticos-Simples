"""Motor configurable: maximiza o minimiza una sola funcion objetivo."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Callable

from .cruce import cruzar
from .mutacion import uniforme_real, no_uniforme_real, intercambio, inversion_bit
from .seleccion import seleccionar
from .sustitucion import steady_state, crowding


@dataclass
class ConfigAG:
    representacion: str = "real"      # real, binaria, permutacion
    tam_poblacion: int = 80
    generaciones: int = 120
    maximizar: bool = False
    limites: list[tuple[float, float]] = field(default_factory=lambda: [(-10.0, 10.0)])
    num_elementos: int = 6           # usado en permutaciones
    bits_por_variable: int = 12      # usado en binaria
    seleccion: str = "torneo"
    cruce: str = "blx"
    mutacion: str = "no_uniforme"
    sustitucion: str = "generacional"  # generacional, steady_state, crowding
    prob_cruce: float = 0.85
    prob_mutacion: float = 0.10
    elitismo: int = 1
    k_torneo: int = 3
    amax: float = 1.6
    q: float = 0.5
    a_aritmetico: float = 0.25
    alfa_blx: float = 0.5
    b_mutacion: float = 1.0
    factor_crowding: int = 3
    cantidad_reemplazos: int = 10
    semilla: int = 42

    def validar(self):
        if self.representacion not in ("real", "binaria", "permutacion"):
            raise ValueError("Representacion no reconocida")
        if self.tam_poblacion < 2 or self.generaciones < 1:
            raise ValueError("La poblacion debe ser >= 2 y las generaciones >= 1")
        if not 0 <= self.prob_cruce <= 1 or not 0 <= self.prob_mutacion <= 1:
            raise ValueError("Las probabilidades deben estar entre 0 y 1")
        if not 0 <= self.elitismo < self.tam_poblacion:
            raise ValueError("Elitismo debe estar entre 0 y tam_poblacion-1")
        if self.seleccion not in ("ruleta", "ranking_lineal", "ranking_no_lineal", "torneo", "sus"):
            raise ValueError("Seleccion no valida")
        if self.sustitucion not in ("generacional", "steady_state", "crowding"):
            raise ValueError("Sustitucion no valida")
        compatibles = {
            "real": ({"uniforme", "aritmetico", "plano", "blx"}, {"uniforme", "no_uniforme"}),
            "binaria": ({"uniforme"}, {"bitflip"}),
            "permutacion": ({"pmx", "ox", "cx"}, {"intercambio"}),
        }
        cruces, mutaciones = compatibles[self.representacion]
        if self.cruce not in cruces or self.mutacion not in mutaciones:
            raise ValueError(f"Cruce/mutacion incompatible con {self.representacion}. "
                             f"Cruces: {sorted(cruces)}; mutaciones: {sorted(mutaciones)}")
        if self.representacion in ("real", "binaria"):
            if not self.limites or any(lb >= ub or not math.isfinite(lb + ub)
                                       for lb, ub in self.limites):
                raise ValueError("Cada variable requiere limites finitos LB < UB")
        if self.representacion == "permutacion" and self.num_elementos < 2:
            raise ValueError("Se requieren al menos 2 elementos")
        if self.representacion == "binaria" and not 1 <= self.bits_por_variable <= 30:
            raise ValueError("bits_por_variable debe estar en [1, 30]")
        if not 1 <= self.k_torneo <= self.tam_poblacion:
            raise ValueError("k_torneo fuera de rango")
        if not 1 <= self.factor_crowding <= self.tam_poblacion:
            raise ValueError("factor_crowding fuera de rango")
        if not 1 <= self.cantidad_reemplazos <= self.tam_poblacion:
            raise ValueError("cantidad_reemplazos fuera de rango")
        if not 1 <= self.amax <= 2 or not 0 < self.q <= 1:
            raise ValueError("amax o q fuera de rango")
        if not 0 <= self.a_aritmetico <= 1 or self.alfa_blx < 0 or self.b_mutacion <= 0:
            raise ValueError("Parametros de cruce/mutacion invalidos")


@dataclass
class ResultadoAG:
    mejor_cromosoma: list
    mejor_solucion: list
    mejor_valor: float
    historial: list[dict]
    poblacion_final: list[list]
    valores_finales: list[float]


def decodificar(cromosoma: list, config: ConfigAG) -> list:
    if config.representacion != "binaria":
        return list(cromosoma)
    bits = config.bits_por_variable
    denominador = (1 << bits) - 1
    solucion = []
    for i, (lb, ub) in enumerate(config.limites):
        segmento = cromosoma[i * bits:(i + 1) * bits]
        entero = 0
        for bit in segmento:
            entero = (entero << 1) | bit
        solucion.append(lb + (ub - lb) * entero / denominador)
    return solucion


def _inicializar(config: ConfigAG, rng: random.Random) -> list:
    if config.representacion == "real":
        return [rng.uniform(lb, ub) for lb, ub in config.limites]
    if config.representacion == "binaria":
        return [rng.randint(0, 1) for _ in range(len(config.limites) * config.bits_por_variable)]
    return rng.sample(range(config.num_elementos), config.num_elementos)


def _mutar(cromosoma, config: ConfigAG, generacion: int, rng: random.Random) -> list:
    if config.mutacion == "uniforme":
        return uniforme_real(cromosoma, config.limites, config.prob_mutacion, rng)
    if config.mutacion == "no_uniforme":
        return no_uniforme_real(cromosoma, config.limites, config.prob_mutacion,
                               generacion, config.generaciones, rng, config.b_mutacion)
    if config.mutacion == "intercambio":
        return intercambio(cromosoma, config.prob_mutacion, rng)
    if config.mutacion == "bitflip":
        return inversion_bit(cromosoma, config.prob_mutacion, rng)
    raise ValueError("Mutacion no reconocida")


def _es_mejor(a: float, b: float, maximizar: bool) -> bool:
    return a > b if maximizar else a < b


def ejecutar_ag(funcion_objetivo: Callable[[list], float], config: ConfigAG) -> ResultadoAG:
    """La funcion recibe un vector real (o una permutacion) y devuelve un escalar."""
    config.validar()
    rng = random.Random(config.semilla)
    poblacion = [_inicializar(config, rng) for _ in range(config.tam_poblacion)]
    penalizacion = -1e100 if config.maximizar else 1e100

    def evaluar(individuo: list) -> float:
        try:
            valor = float(funcion_objetivo(decodificar(individuo, config)))
            return valor if math.isfinite(valor) else penalizacion
        except (ValueError, ZeroDivisionError, OverflowError, TypeError):
            return penalizacion

    historial = []
    mejor_cromosoma = None
    mejor_valor = penalizacion

    def registrar(generacion: int, puntajes: list[float]):
        nonlocal mejor_cromosoma, mejor_valor
        indice = (max if config.maximizar else min)(range(len(puntajes)), key=lambda i: puntajes[i])
        valor = puntajes[indice]
        if mejor_cromosoma is None or _es_mejor(valor, mejor_valor, config.maximizar):
            mejor_valor = valor
            mejor_cromosoma = list(poblacion[indice])
        validos = [p for p in puntajes if p != penalizacion]
        historial.append({
            "generacion": generacion,
            "mejor_generacion": valor,
            "mejor_historico": mejor_valor,
            "promedio": sum(validos) / len(validos) if validos else penalizacion,
        })

    puntajes = [evaluar(c) for c in poblacion]
    if all(v == penalizacion for v in puntajes):
        raise ValueError("La funcion objetivo no produjo valores validos en la poblacion inicial")
    registrar(0, puntajes)

    for g in range(1, config.generaciones + 1):
        orden = sorted(range(len(poblacion)), key=lambda i: puntajes[i], reverse=config.maximizar)
        if config.sustitucion == "generacional":
            cantidad_hijos = config.tam_poblacion - config.elitismo
        else:
            cantidad_hijos = config.cantidad_reemplazos
        hijos = []
        while len(hijos) < cantidad_hijos:
            i, j = seleccionar(puntajes, 2, config.seleccion, config.maximizar, rng,
                              k=config.k_torneo, amax=config.amax, q=config.q)
            p1, p2 = poblacion[i], poblacion[j]
            if rng.random() < config.prob_cruce:
                h1, h2 = cruzar(p1, p2, config.cruce, rng,
                                a=config.a_aritmetico, alfa=config.alfa_blx,
                                limites=config.limites if config.representacion == "real" else None)
            else:
                h1, h2 = list(p1), list(p2)
            hijos.append(_mutar(h1, config, g, rng))
            if len(hijos) < cantidad_hijos:
                hijos.append(_mutar(h2, config, g, rng))

        if config.sustitucion == "generacional":
            elites = [list(poblacion[i]) for i in orden[:config.elitismo]]
            nueva = elites + hijos
        elif config.sustitucion == "steady_state":
            nueva = steady_state(poblacion, puntajes, hijos, config.maximizar)
        else:
            nueva = crowding(poblacion, hijos, config.factor_crowding,
                             config.representacion, rng)
            # Si se solicito elitismo, recuperar a los mejores del ciclo previo.
            for indice in orden[:config.elitismo]:
                elite = poblacion[indice]
                if elite not in nueva:
                    nuevos_puntajes = [evaluar(c) for c in nueva]
                    peor = (min if config.maximizar else max)(range(len(nueva)), key=lambda i: nuevos_puntajes[i])
                    if _es_mejor(puntajes[indice], nuevos_puntajes[peor], config.maximizar):
                        nueva[peor] = list(elite)
        poblacion = nueva
        puntajes = [evaluar(c) for c in poblacion]
        registrar(g, puntajes)

    return ResultadoAG(
        mejor_cromosoma=mejor_cromosoma,
        mejor_solucion=decodificar(mejor_cromosoma, config),
        mejor_valor=mejor_valor,
        historial=historial,
        poblacion_final=poblacion,
        valores_finales=puntajes,
    )
