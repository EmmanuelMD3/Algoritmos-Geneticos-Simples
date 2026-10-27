"""Integración de las entradas de la GUI con el motor existente."""
import unittest

from ag.motor import ejecutar_ag
from ejemplos import EJEMPLOS, ejecutar_ejemplo
from gui_logic import interpretar_limites, preparar_optimizacion, preparar_ruta


BASE = {
    "expresion": "(x-3)**2+2", "objetivo": "min", "dim": "1",
    "inferior": "-10", "superior": "10", "especificos": "",
    "representacion": "real", "bits": "12", "poblacion": "24",
    "generaciones": "12", "seleccion": "torneo", "cruce": "blx",
    "mutacion": "no_uniforme", "sustitucion": "generacional",
    "pc": "0.85", "pm": "0.10", "k": "3", "amax": "1.6", "q": "0.5",
    "a_aritmetico": "0.25", "alfa_blx": "0.5", "b_mutacion": "1.0",
    "elitismo": "1", "cf": "3", "reemplazos": "10", "semilla": "42",
}

RUTA = {
    "seleccion": "torneo", "cruce": "ox", "sustitucion": "generacional",
    "poblacion": "24", "generaciones": "12", "pc": "0.85", "pm": "0.25",
    "k": "3", "elitismo": "1", "cf": "3", "reemplazos": "10", "semilla": "42",
}


class PruebasIntegracionGUI(unittest.TestCase):
    def test_optimizacion_real(self):
        funcion, config = preparar_optimizacion(BASE)
        resultado = ejecutar_ag(funcion, config)
        self.assertEqual(len(resultado.historial), 13)
        self.assertEqual(len(resultado.mejor_solucion), 1)
        self.assertEqual(resultado.historial[-1]["mejor_historico"], resultado.mejor_valor)

    def test_binaria_y_limites_por_variable(self):
        campos = {**BASE, "expresion": "x0**2+x1**2", "dim": "2",
                  "especificos": "-5:5; -2:2", "representacion": "binaria",
                  "cruce": "uniforme", "mutacion": "bitflip"}
        funcion, config = preparar_optimizacion(campos)
        resultado = ejecutar_ag(funcion, config)
        self.assertEqual(config.limites, [(-5, 5), (-2, 2)])
        self.assertEqual(len(resultado.mejor_solucion), 2)

    def test_validacion_gui(self):
        with self.assertRaisesRegex(ValueError, "exactamente 2"):
            interpretar_limites(2, "-10", "10", "-5:5")
        with self.assertRaisesRegex(ValueError, "inferior menor"):
            interpretar_limites(1, "10", "-10", "")
        with self.assertRaisesRegex(ValueError, "incompatible"):
            preparar_optimizacion({**BASE, "representacion": "binaria"})
        with self.assertRaisesRegex(ValueError, "Probabilidad de cruce"):
            preparar_optimizacion({**BASE, "pc": "inf"})

    def test_ruta_usa_matriz_para_los_tres_cruces(self):
        for cruce in ("pmx", "ox", "cx"):
            funcion, config = preparar_ruta({**RUTA, "cruce": cruce})
            resultado = ejecutar_ag(funcion, config)
            self.assertEqual(sorted(resultado.mejor_solucion), list(range(6)))
            self.assertEqual(funcion(resultado.mejor_solucion), resultado.mejor_valor)

    def test_los_17_ejemplos_independientes(self):
        self.assertEqual(len(EJEMPLOS), 17)
        for numero in range(1, 18):
            with self.subTest(numero=numero):
                self.assertTrue(ejecutar_ejemplo(numero))
        with self.assertRaises(ValueError):
            ejecutar_ejemplo(18)


if __name__ == "__main__":
    unittest.main()
