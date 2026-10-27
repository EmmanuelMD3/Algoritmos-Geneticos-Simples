import math
import random
import unittest

from ag.cruce import uniforme, aritmetico, pmx, ox, cx, blx_alfa, plano
from ag.motor import ConfigAG, decodificar, ejecutar_ag
from ag.mutacion import intercambio, no_uniforme_real, uniforme_real, inversion_bit
from ag.objetivos import crear_funcion, distancia_ruta
from ag.seleccion import (ruleta_probabilidades, ranking_lineal_probabilidades,
                           ranking_no_lineal_probabilidades,
                           muestreo_estocastico_universal, seleccionar)
from ag.sustitucion import steady_state, crowding


class PruebasDeOperadores(unittest.TestCase):
    def test_ruleta_pag1(self):
        self.assertEqual(ruleta_probabilidades([10, 20, 30, 40]), [0.1, 0.2, 0.3, 0.4])

    def test_ranking_lineal_normalizado(self):
        p = ranking_lineal_probabilidades([10, 20, 30, 40], amax=1.6)
        self.assertAlmostEqual(sum(p), 1)
        self.assertEqual([round(p[i], 2) for i in (3, 2, 1, 0)], [0.4, 0.3, 0.2, 0.1])

    def test_ranking_no_lineal_pag3(self):
        p = ranking_no_lineal_probabilidades([10, 20, 30, 40], q=0.5)
        self.assertAlmostEqual(sum(p), 1)
        self.assertEqual([round(p[i], 4) for i in (3, 2, 1, 0)],
                         [0.5333, 0.2667, 0.1333, 0.0667])

    def test_torneo_y_sus(self):
        rng = random.Random(3)
        inds = seleccionar([10, 20, 30, 40], 10, "torneo", True, rng, k=4)
        self.assertEqual(inds, [3] * 10)
        sus = muestreo_estocastico_universal([0.1, 0.2, 0.3, 0.4], 4, rng)
        self.assertEqual(len(sus), 4)
        self.assertTrue(all(0 <= i < 4 for i in sus))

    def test_steady_state_pag6(self):
        poblacion = [[10], [20], [30], [40]]
        nueva = steady_state(poblacion, [10, 20, 30, 40], [[25], [35]], True)
        self.assertEqual(set(x[0] for x in nueva), {25, 30, 35, 40})

    def test_crowding_pag7(self):
        nueva = crowding([[1, 0, 1, 0], [0, 0, 1, 0], [0, 1, 0, 1]],
                         [[1, 0, 1, 1]], 3, "binaria", random.Random(0))
        self.assertEqual(nueva[0], [1, 0, 1, 1])

    def test_cruce_uniforme_pag8(self):
        a, b = uniforme([1, 1, 0, 0, 1, 0], [0, 0, 1, 1, 0, 1],
                        random.Random(0), [1, 0, 1, 0, 1, 0])
        self.assertEqual(a, [1, 0, 0, 1, 1, 1])
        self.assertEqual(b, [0, 1, 1, 0, 0, 0])

    def test_aritmetico_pag9(self):
        self.assertEqual(aritmetico([2, 8], [6, 4], .25), ([5., 5.], [3., 7.]))

    def test_plano_y_blx(self):
        a, b = plano([2, 8], [6, 4], random.Random(7))
        self.assertTrue(all(2 <= hijo[0] <= 6 and 4 <= hijo[1] <= 8 for hijo in (a, b)))
        a, b = blx_alfa([2], [6], .5, random.Random(7))
        self.assertTrue(all(0 <= hijo[0] <= 8 for hijo in (a, b)))

    def test_pmx_pag12_corregido(self):
        p1 = [1, 2, 3, 4, 5, 6, 7, 8]
        p2 = [3, 7, 5, 1, 6, 8, 2, 4]
        h1, h2 = pmx(p1, p2, random.Random(0), (2, 5))
        self.assertEqual(h1, [6, 7, 3, 4, 5, 8, 2, 1])
        self.assertEqual(sorted(h1), sorted(p1))
        self.assertEqual(sorted(h2), sorted(p1))

    def test_ox_cx_preservan_permutaciones(self):
        rng = random.Random(13)
        for _ in range(40):
            a = rng.sample(range(10), 10)
            b = rng.sample(range(10), 10)
            for fun in (ox, pmx, cx):
                if fun == cx:
                    h1, h2 = fun(a, b)
                else:
                    h1, h2 = fun(a, b, rng)
                self.assertEqual(set(h1), set(a))
                self.assertEqual(set(h2), set(a))
                self.assertEqual(len(set(h1)), len(a))
                self.assertEqual(len(set(h2)), len(a))

    def test_mutaciones(self):
        self.assertEqual(sorted(intercambio([1, 2, 3, 4], 1, random.Random(0))), [1, 2, 3, 4])
        self.assertEqual(inversion_bit([1, 1, 0, 0], 1, random.Random(0)), [0, 0, 1, 1])
        a = uniforme_real([1, 2], [(0, 10), (0, 10)], 1, random.Random(0))
        self.assertTrue(all(0 <= x <= 10 for x in a))
        b = no_uniforme_real([1, 2], [(0, 10), (0, 10)], 1, 30, 100, random.Random(0))
        self.assertTrue(all(0 <= x <= 10 for x in b))

    def test_funcion_objetivo_y_rechazo_codigo(self):
        f = crear_funcion("(x-3)**2+2", 1)
        self.assertEqual(f([3]), 2)
        g = crear_funcion("x0**2+x1**2+sin(pi/2)", 2)
        self.assertAlmostEqual(g([0, 0]), 1)
        h = crear_funcion("x[0]**2+x[1]**2", 2)
        self.assertEqual(h([1, 2]), 5)
        for expresion in ('__import__("os")', 'x.__class__', '[1,2]', 'open("archivo")'):
            with self.assertRaises(ValueError):
                crear_funcion(expresion, 1)

    def test_optimiza_en_una_dimension(self):
        f = crear_funcion("(x-3)**2+2", 1)
        config = ConfigAG(generaciones=75, tam_poblacion=50, semilla=42)
        r = ejecutar_ag(f, config)
        self.assertLess(r.mejor_valor - 2, 0.1)
        self.assertEqual(len(r.historial), 76)
        self.assertTrue(all(r.historial[i]["mejor_historico"] <= r.historial[i-1]["mejor_historico"]
                            for i in range(1, len(r.historial))))

    def test_optimiza_maximo(self):
        f = crear_funcion("-(x-2)**2+8", 1)
        config = ConfigAG(generaciones=75, tam_poblacion=50, semilla=42, maximizar=True)
        r = ejecutar_ag(f, config)
        self.assertGreater(r.mejor_valor, 7.9)

    def test_real_sustituciones_y_selecciones(self):
        f = crear_funcion("x0**2+x1**2", 2)
        for seleccion in ("ruleta", "ranking_lineal", "ranking_no_lineal", "torneo", "sus"):
            for sustitucion in ("generacional", "steady_state", "crowding"):
                c = ConfigAG(tam_poblacion=16, generaciones=8, limites=[(-5, 5), (-5, 5)],
                             seleccion=seleccion, sustitucion=sustitucion, cantidad_reemplazos=5,
                             factor_crowding=3, semilla=33)
                r = ejecutar_ag(f, c)
                self.assertEqual(len(r.poblacion_final), 16)
                self.assertEqual(len(r.mejor_solucion), 2)

    def test_binaria_multivariables(self):
        f = crear_funcion("x0**2+x1**2", 2)
        c = ConfigAG(representacion="binaria", seleccion="torneo", cruce="uniforme",
                     mutacion="bitflip", limites=[(-5, 5), (-5, 5)], tam_poblacion=50,
                     generaciones=60, prob_mutacion=.03)
        r = ejecutar_ag(f, c)
        self.assertLess(r.mejor_valor, 0.4)
        self.assertEqual(len(r.mejor_cromosoma), 24)
        self.assertEqual(len(r.mejor_solucion), 2)

    def test_rutas_tres_cruces(self):
        matriz = [[0, 2, 5, 9], [2, 0, 6, 4], [5, 6, 0, 3], [9, 4, 3, 0]]
        for cruce in ("pmx", "ox", "cx"):
            c = ConfigAG(representacion="permutacion", num_elementos=4,
                         cruce=cruce, mutacion="intercambio", tam_poblacion=30,
                         generaciones=20, prob_mutacion=.2)
            r = ejecutar_ag(lambda x: distancia_ruta(x, matriz), c)
            self.assertEqual(sorted(r.mejor_solucion), list(range(4)))
            self.assertEqual(len(r.poblacion_final), 30)


if __name__ == "__main__":
    unittest.main()
