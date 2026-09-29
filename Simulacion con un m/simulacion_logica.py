# -*- coding: utf-8 -*-
"""
simulacion_logica.py
=====================
Motor de la simulación Monte Carlo del TP N°3 (red logística con
precedencias). Este módulo NO dibuja nada en pantalla: solo contiene
la matemática. La interfaz gráfica vive en tp3_simulacion_gui.py y
llama a las funciones de este archivo.

Se mantiene la misma estructura que la versión en JavaScript:
  1) Generador Congruencial Mixto (uno por variable aleatoria)
  2) Transformaciones de U(0,1) a cada distribución
  3) Acumulador incremental (el "vector actual / vector anterior")
  4) Una iteración completa de la red
  5) Simulación de N iteraciones (memoria O(1))
  6) Simulación acotada de 99 corridas (percentil 95%)
"""

import math


# =====================================================================
# 1) GENERADOR CONGRUENCIAL MIXTO
#    Xn = (a * Xn-1 + c) mod m   ;   U = Xn / m   (uniforme en [0, 1))
#    Cada variable aleatoria tiene su propio objeto generador, con su
#    propia semilla inicial, para que las secuencias no se solapen.
# =====================================================================
class GeneradorCongruencial:
    def __init__(self, semilla, a, c, m):
        self.semilla = semilla  # X0 al crearlo; luego pasa a ser Xn-1, Xn, ...
        self.a = a
        self.c = c
        self.m = m

    def siguiente(self):
        """Calcula Xn a partir de Xn-1 (self.semilla) y devuelve U = Xn/m."""
        self.semilla = (self.a * self.semilla + self.c) % self.m
        return self.semilla / self.m


# =====================================================================
# 2) TRANSFORMACIONES: de U(0,1) al valor real de cada distribución
# =====================================================================
def transformar_discreta(u, valores, probabilidades):
    """Método de la transformada inversa para una distribución discreta."""
    acumulada = 0.0
    for valor, prob in zip(valores, probabilidades):
        acumulada += prob
        if u < acumulada:
            return valor
    return valores[-1]  # resguardo por redondeo de punto flotante


def transformar_uniforme(u, minimo, maximo):
    return minimo + u * (maximo - minimo)


def transformar_exponencial(u, media):
    return -media * math.log(1 - u)


# =====================================================================
# 3) ACUMULADOR INCREMENTAL
#    No guarda ningún historial: en cada iteración se actualiza el
#    "vector actual" (n, suma, suma de cuadrados, mínimo, máximo) a
#    partir del "vector anterior" (el mismo objeto, un instante antes).
# =====================================================================
class Acumulador:
    def __init__(self):
        self.n = 0
        self.suma = 0.0
        self.suma_cuadrados = 0.0
        self.minimo = float("inf")
        self.maximo = float("-inf")

    def acumular(self, x):
        self.n += 1
        self.suma += x
        self.suma_cuadrados += x * x
        if x < self.minimo:
            self.minimo = x
        if x > self.maximo:
            self.maximo = x

    def media(self):
        return self.suma / self.n if self.n else 0.0

    def varianza(self):
        if self.n < 2:
            return 0.0
        m = self.media()
        v = (self.suma_cuadrados - self.n * m * m) / (self.n - 1)
        return v if v > 0 else 0.0

    def desvio(self):
        return math.sqrt(self.varianza())


# =====================================================================
# TIEMPO MÍNIMO TEÓRICO (simulacro con el mejor caso de cada actividad)
# =====================================================================
def tiempo_minimo_teorico(p):
    b_min = min(p["B"]["val"])
    f_min = min(p["F"]["val"])
    d_min = p["D"]["min"]
    e_min = 0.0  # la exponencial no tiene cota inferior positiva: ínfimo teórico = 0
    ruta_producto = p["A"] + b_min
    ruta_empaque = p["C"] + d_min + e_min
    return max(ruta_producto, ruta_empaque) + f_min


def crear_generadores(p):
    """Un GeneradorCongruencial independiente por cada variable aleatoria."""
    return {
        "B": GeneradorCongruencial(p["genB"]["sem"], p["genB"]["a"], p["genB"]["c"], p["m"]),
        "D": GeneradorCongruencial(p["genD"]["sem"], p["genD"]["a"], p["genD"]["c"], p["m"]),
        "E": GeneradorCongruencial(p["genE"]["sem"], p["genE"]["a"], p["genE"]["c"], p["m"]),
        "F": GeneradorCongruencial(p["genF"]["sem"], p["genF"]["a"], p["genF"]["c"], p["m"]),
    }


# =====================================================================
# 4) UNA ITERACIÓN DE LA RED
# =====================================================================
def correr_iteracion(p, gens):
    u_b = gens["B"].siguiente()
    B = transformar_discreta(u_b, p["B"]["val"], p["B"]["prob"])

    u_d = gens["D"].siguiente()
    D = transformar_uniforme(u_d, p["D"]["min"], p["D"]["max"])

    u_e = gens["E"].siguiente()
    E = transformar_exponencial(u_e, p["E"]["media"])

    u_f = gens["F"].siguiente()
    F = transformar_discreta(u_f, p["F"]["val"], p["F"]["prob"])

    ruta_producto = p["A"] + B          # rama A -> B
    ruta_empaque = p["C"] + D + E       # rama C -> D -> E
    convergencia = max(ruta_producto, ruta_empaque)
    total = convergencia + F

    return {
        "A": p["A"], "B": B, "C": p["C"], "D": D, "E": E, "F": F,
        "ruta_producto": ruta_producto, "ruta_empaque": ruta_empaque,
        "total": total,
    }


# =====================================================================
# 5) SIMULACIÓN PRINCIPAL: N ITERACIONES, MEMORIA O(1)
# =====================================================================
def simular_n(p):
    gens = crear_generadores(p)

    stats = {k: Acumulador() for k in ("A", "B", "C", "D", "E", "F", "Total")}
    ruta1_critica = ruta2_critica = empate_critico = 0
    c_umbral1 = c_umbral2 = 0

    t_min = tiempo_minimo_teorico(p)
    ancho = p["amplitud"] / 9
    bordes = [t_min + k * ancho for k in range(9)]   # inicio de los intervalos 1..9
    inicio_ultimo = t_min + p["amplitud"]             # inicio del intervalo 10 (sin cota superior)
    histograma = [0] * 10

    def ubicar_bin(total):
        if total >= inicio_ultimo:
            return 9
        for k in range(8, -1, -1):
            if total >= bordes[k]:
                return k
        return 0

    # -----------------------------------------------------------------
    # Puntos de control para el gráfico de convergencia (Ley de los
    # Grandes Números). NO es una tabla con las N iteraciones: es una
    # lista chica y de tamaño fijo (a lo sumo ~200 puntos) sin importar
    # si N es 1.000 o 10.000.000. La idea es la misma que ya usaban los
    # programas de ejemplo de la cátedra: mostrar el progreso cada 10%
    # (o cada 20.000 iteraciones), en vez de guardar cada resultado.
    # -----------------------------------------------------------------


    checkpoint_cada = max(1, p["n"] // 200) ## VER ESTO 



    convergencia = []  # lista de (iteración, promedio acumulado hasta ahí)

    for i in range(p["n"]):
        it = correr_iteracion(p, gens)

        stats["A"].acumular(it["A"])
        stats["B"].acumular(it["B"])
        stats["C"].acumular(it["C"])
        stats["D"].acumular(it["D"])
        stats["E"].acumular(it["E"])
        stats["F"].acumular(it["F"])
        stats["Total"].acumular(it["total"])

        if it["ruta_producto"] > it["ruta_empaque"]:
            ruta1_critica += 1
        elif it["ruta_empaque"] > it["ruta_producto"]:
            ruta2_critica += 1
        else:
            empate_critico += 1

        if it["total"] <= p["umbral1"]:
            c_umbral1 += 1
        if it["total"] >= p["umbral2"]:
            c_umbral2 += 1

        histograma[ubicar_bin(it["total"])] += 1

        if (i + 1) % checkpoint_cada == 0 or i == p["n"] - 1:
            convergencia.append((i + 1, stats["Total"].media()))

    return {
        "stats": stats,
        "ruta1_critica": ruta1_critica, "ruta2_critica": ruta2_critica, "empate_critico": empate_critico,
        "c_umbral1": c_umbral1, "c_umbral2": c_umbral2,
        "histograma": histograma, "t_min": t_min, "bordes": bordes, "inicio_ultimo": inicio_ultimo,
        "convergencia": convergencia,
        "n": p["n"],
    }


# =====================================================================
# 6) CORRIDA ACOTADA DE 99 SIMULACIONES (percentil 95%)
#    Único lugar del programa donde se guarda un arreglo con resultados
#    individuales: es chico (99 valores) y de tamaño fijo, muy distinto
#    de guardar la tabla completa de una corrida de N iteraciones.
# =====================================================================
def simular_99(p):
    gens = crear_generadores(p)
    totales = [correr_iteracion(p, gens)["total"] for _ in range(99)]
    totales.sort()

    posicion = math.ceil(0.95 * 99)  # 95° valor de 99 ordenados (1-indexado)
    percentil95 = totales[posicion - 1]

    return {
        "percentil95": percentil95,
        "posicion": posicion,
        "minimo": totales[0],
        "maximo": totales[-1],
        "promedio": sum(totales) / 99,
        "totales": totales,
    }
