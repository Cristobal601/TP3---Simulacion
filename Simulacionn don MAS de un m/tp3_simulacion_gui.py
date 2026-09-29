# -*- coding: utf-8 -*-
"""
tp3_simulacion_gui.py
======================
Interfaz gráfica (tkinter, incluido en Python estándar) para el TP N°3.
No usa la consola para nada: los parámetros se cargan en un formulario
y los resultados se muestran en tablas dentro de la misma ventana.

Para ejecutarlo:  python tp3_simulacion_gui.py
(este archivo tiene que estar en la misma carpeta que simulacion_logica.py)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from simulacion_logica import simular_n, simular_99

# Colores usados en los gráficos (los mismos que la versión web: ámbar
# para el acento general, azul para la rama A->B, naranja para C->D->E)
COLOR_ACENTO = "#c98a2e"
COLOR_RUTA1 = "#3d7fb3"
COLOR_RUTA2 = "#c9663d"
COLOR_EMPATE = "#999999"


# =====================================================================
# Valores por defecto (los mismos del enunciado / de la versión HTML)
# =====================================================================
DEFAULTS = {
    "nIter": "1000",
    "semB": "3922", "aB": "1221", "cB": "1714", "mB": "12345",
    "semD": "3923", "aD": "1221", "cD": "1714", "mD": "12345",
    "semE": "3924", "aE": "1221", "cE": "1714", "mE": "12345",
    "semF": "3925", "aF": "1221", "cF": "1714", "mF": "12345",
    "constA": "15",
    "valB1": "20", "valB2": "30", "valB3": "40",
    "probB1": "0.25", "probB2": "0.40", "probB3": "0.35",
    "constC": "5",
    "dMin": "5", "dMax": "25",
    "mediaE": "5",
    "valF1": "15", "valF2": "25",
    "probF1": "0.50", "probF2": "0.50",
    "umbral1": "60", "umbral2": "90", "amplitud": "90",
}


class AplicacionTP3:
    def __init__(self, root):
        self.root = root
        self.root.title("TP N°3 · Simulación Monte Carlo — Red logística")
        self.root.geometry("980x680")

        self.vars = {}  # guarda todos los tk.StringVar, con la misma clave que en DEFAULTS

        self._armar_layout()

    # -----------------------------------------------------------------
    # LAYOUT GENERAL: notebook con pestañas + barra de botones al pie
    # -----------------------------------------------------------------
    def _armar_layout(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.tab_generadores = ttk.Frame(self.notebook)
        self.tab_distribuciones = ttk.Frame(self.notebook)
        self.tab_umbrales = ttk.Frame(self.notebook)
        self.tab_resultados = ttk.Frame(self.notebook)
        self.tab_graficos = ttk.Frame(self.notebook)
        self.tab_99 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_generadores, text="General y generadores")
        self.notebook.add(self.tab_distribuciones, text="Distribuciones")
        self.notebook.add(self.tab_umbrales, text="Umbrales")
        self.notebook.add(self.tab_resultados, text="Resultados (N iteraciones)")
        self.notebook.add(self.tab_graficos, text="Gráficos")
        self.notebook.add(self.tab_99, text="Confianza 95% (99 corridas)")

        self._armar_tab_generadores()
        self._armar_tab_distribuciones()
        self._armar_tab_umbrales()
        self._armar_tab_resultados()
        self._armar_tab_graficos()
        self._armar_tab_99()

        barra = ttk.Frame(self.root)
        barra.pack(fill="x", padx=10, pady=10)
        ttk.Button(barra, text="Simular N iteraciones", command=self.simular_click)\
            .pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(barra, text="Simular 99 corridas (95% de confianza)", command=self.simular99_click)\
            .pack(side="left", expand=True, fill="x", padx=(5, 0))

    # -----------------------------------------------------------------
    # Helper: crea una etiqueta + un Entry, y guarda la variable en self.vars
    # -----------------------------------------------------------------
    def _campo(self, parent, clave, etiqueta, fila, columna):
        ttk.Label(parent, text=etiqueta).grid(row=fila, column=columna * 2, sticky="w", padx=6, pady=4)
        var = tk.StringVar(value=DEFAULTS[clave])
        ttk.Entry(parent, textvariable=var, width=10).grid(row=fila, column=columna * 2 + 1, padx=6, pady=4)
        self.vars[clave] = var

    # -----------------------------------------------------------------
    # PESTAÑA 1: N, y la tabla de los 4 generadores individuales
    # (cada uno con su propia semilla, a, c y ahora también su propio m)
    # -----------------------------------------------------------------
    def _armar_tab_generadores(self):
        f = self.tab_generadores

        general = ttk.LabelFrame(f, text="General")
        general.pack(fill="x", padx=10, pady=10)
        self._campo(general, "nIter", "Iteraciones a simular (N):", 0, 0)

        gens = ttk.LabelFrame(f, text="Generadores congruenciales individuales  —  Xn = (a·Xn-1 + c) mod m ; U = Xn/m")
        gens.pack(fill="x", padx=10, pady=10)
        for col, titulo in enumerate(["Variable", "Semilla", "a", "c", "m (módulo)"]):
            ttk.Label(gens, text=titulo, font=("", 9, "bold")).grid(row=0, column=col, padx=8, pady=4)
        filas = [("B", "semB", "aB", "cB", "mB"), ("D", "semD", "aD", "cD", "mD"),
                 ("E", "semE", "aE", "cE", "mE"), ("F", "semF", "aF", "cF", "mF")]
        for i, (nombre, sem, a, c, m) in enumerate(filas, start=1):
            ttk.Label(gens, text=nombre).grid(row=i, column=0, padx=8, pady=3)
            for col, clave in enumerate([sem, a, c, m], start=1):
                var = tk.StringVar(value=DEFAULTS[clave])
                ttk.Entry(gens, textvariable=var, width=10).grid(row=i, column=col, padx=8, pady=3)
                self.vars[clave] = var

        ttk.Label(
            f,
            text="A y C son deterministas (constantes): no consumen generador.\n"
                 "Cada variable tiene su propia semilla y su propio módulo (m) — no hay ningún\n"
                 "valor compartido entre generadores; podés cargar un legajo o módulo distinto en cada fila.",
            foreground="#555",
        ).pack(anchor="w", padx=14, pady=(0, 10))

    # -----------------------------------------------------------------
    # PESTAÑA 2: parámetros de cada distribución (A..F)
    # -----------------------------------------------------------------
    def _armar_tab_distribuciones(self):
        f = self.tab_distribuciones

        gA = ttk.LabelFrame(f, text="A — Verificación de pago (constante)")
        gA.pack(fill="x", padx=10, pady=6)
        self._campo(gA, "constA", "Duración fija (min):", 0, 0)

        gB = ttk.LabelFrame(f, text="B — Picking en almacén (discreta)")
        gB.pack(fill="x", padx=10, pady=6)
        ttk.Label(gB, text="Valor (min)", font=("", 9, "bold")).grid(row=0, column=0, padx=6)
        ttk.Label(gB, text="Probabilidad", font=("", 9, "bold")).grid(row=0, column=1, padx=6)
        for i, (val, prob) in enumerate([("valB1", "probB1"), ("valB2", "probB2"), ("valB3", "probB3")], start=1):
            var_val = tk.StringVar(value=DEFAULTS[val]); self.vars[val] = var_val
            var_prob = tk.StringVar(value=DEFAULTS[prob]); self.vars[prob] = var_prob
            ttk.Entry(gB, textvariable=var_val, width=10).grid(row=i, column=0, padx=6, pady=3)
            ttk.Entry(gB, textvariable=var_prob, width=10).grid(row=i, column=1, padx=6, pady=3)

        gC = ttk.LabelFrame(f, text="C — Impresión de etiqueta (constante)")
        gC.pack(fill="x", padx=10, pady=6)
        self._campo(gC, "constC", "Duración fija (min):", 0, 0)

        gD = ttk.LabelFrame(f, text="D — Packing (uniforme continua)")
        gD.pack(fill="x", padx=10, pady=6)
        self._campo(gD, "dMin", "Mínimo (min):", 0, 0)
        self._campo(gD, "dMax", "Máximo (min):", 0, 1)

        gE = ttk.LabelFrame(f, text="E — Control de calidad (exponencial)")
        gE.pack(fill="x", padx=10, pady=6)
        self._campo(gE, "mediaE", "Media 1/λ (min):", 0, 0)

        gF = ttk.LabelFrame(f, text="F — Despacho (discreta)")
        gF.pack(fill="x", padx=10, pady=6)
        ttk.Label(gF, text="Valor (min)", font=("", 9, "bold")).grid(row=0, column=0, padx=6)
        ttk.Label(gF, text="Probabilidad", font=("", 9, "bold")).grid(row=0, column=1, padx=6)
        for i, (val, prob) in enumerate([("valF1", "probF1"), ("valF2", "probF2")], start=1):
            var_val = tk.StringVar(value=DEFAULTS[val]); self.vars[val] = var_val
            var_prob = tk.StringVar(value=DEFAULTS[prob]); self.vars[prob] = var_prob
            ttk.Entry(gF, textvariable=var_val, width=10).grid(row=i, column=0, padx=6, pady=3)
            ttk.Entry(gF, textvariable=var_prob, width=10).grid(row=i, column=1, padx=6, pady=3)

    # -----------------------------------------------------------------
    # PESTAÑA 3: umbrales y amplitud del histograma
    # -----------------------------------------------------------------
    def _armar_tab_umbrales(self):
        f = self.tab_umbrales
        g = ttk.LabelFrame(f, text="Umbrales y distribución de frecuencias")
        g.pack(fill="x", padx=10, pady=10)
        self._campo(g, "umbral1", "P(Total ≤ x) — x:", 0, 0)
        self._campo(g, "umbral2", "P(Total ≥ x) — x:", 1, 0)
        self._campo(g, "amplitud", "Amplitud hasta el 10º intervalo:", 2, 0)
        ttk.Label(
            f,
            text="El intervalo 1 arranca en el tiempo mínimo teórico del proyecto; los intervalos 1 a 9\n"
                 "tienen igual ancho (amplitud/9); el 10º intervalo junta todo lo que sobra.",
            foreground="#555",
        ).pack(anchor="w", padx=14, pady=(0, 10))

    # -----------------------------------------------------------------
    # PESTAÑA 4: resultados de la corrida de N iteraciones
    # -----------------------------------------------------------------
    def _armar_tab_resultados(self):
        f = self.tab_resultados
        self.lbl_resumen = ttk.Label(f, text="Todavía no corriste ninguna simulación.", justify="left")
        self.lbl_resumen.pack(anchor="w", padx=12, pady=10)

        ttk.Label(f, text="Duración por actividad", font=("", 10, "bold")).pack(anchor="w", padx=12)
        self.tabla_actividades = ttk.Treeview(
            f, columns=("promedio", "minimo", "maximo", "desvio"), show="headings", height=6
        )
        for col, titulo in zip(("promedio", "minimo", "maximo", "desvio"), ("Promedio", "Mínimo", "Máximo", "Desvío")):
            self.tabla_actividades.heading(col, text=titulo)
            self.tabla_actividades.column(col, width=100, anchor="center")
        self.tabla_actividades.pack(fill="x", padx=12, pady=(2, 10))

        ttk.Label(f, text="Actividad crítica (cuello de botella)", font=("", 10, "bold")).pack(anchor="w", padx=12)
        self.tabla_criticidad = ttk.Treeview(
            f, columns=("veces", "proporcion"), show="headings", height=3
        )
        self.tabla_criticidad.heading("veces", text="Veces crítica")
        self.tabla_criticidad.heading("proporcion", text="Proporción")
        self.tabla_criticidad.column("veces", width=110, anchor="center")
        self.tabla_criticidad.column("proporcion", width=110, anchor="center")
        self.tabla_criticidad["show"] = "tree headings"
        self.tabla_criticidad.column("#0", width=160, anchor="w")
        self.tabla_criticidad.pack(fill="x", padx=12, pady=(2, 10))

        ttk.Label(f, text="Distribución de frecuencias (10 intervalos)", font=("", 10, "bold")).pack(anchor="w", padx=12)
        self.tabla_histograma = ttk.Treeview(
            f, columns=("frecuencia", "porcentaje"), show="headings", height=10
        )
        self.tabla_histograma.heading("frecuencia", text="Frecuencia")
        self.tabla_histograma.heading("porcentaje", text="Porcentaje")
        self.tabla_histograma["show"] = "tree headings"
        self.tabla_histograma.heading("#0", text="Intervalo (min)")
        self.tabla_histograma.column("#0", width=200, anchor="w")
        self.tabla_histograma.column("frecuencia", width=100, anchor="center")
        self.tabla_histograma.column("porcentaje", width=100, anchor="center")
        self.tabla_histograma.pack(fill="both", expand=True, padx=12, pady=(2, 10))

    # -----------------------------------------------------------------
    # PESTAÑA "Gráficos": 4 gráficos elegidos para entender mejor los
    # resultados, todos dentro de la misma ventana (una sola Figure con
    # 4 sub-gráficos, embebida en tkinter con FigureCanvasTkAgg).
    #   1) Histograma de frecuencias (10 intervalos) — lo pide el enunciado
    #   2) Duración promedio por actividad — para comparar A..F de un vistazo
    #   3) Proporción de actividad crítica — para ver qué rama domina
    #   4) Convergencia del promedio total — muestra cómo se estabiliza
    #      el resultado a medida que aumentan las iteraciones (esto
    #      también lo pide el enunciado: "obtener información sobre el
    #      comportamiento del proyecto a medida que aumenta la cantidad
    #      de iteraciones")
    # -----------------------------------------------------------------
    def _armar_tab_graficos(self):
        f = self.tab_graficos

        self.fig = Figure(figsize=(9, 6.5), dpi=100)
        self.ax_hist = self.fig.add_subplot(2, 2, 1)
        self.ax_actividades = self.fig.add_subplot(2, 2, 2)
        self.ax_criticidad = self.fig.add_subplot(2, 2, 3)
        self.ax_convergencia = self.fig.add_subplot(2, 2, 4)
        self.fig.tight_layout(pad=3.5)

        self.canvas_graficos = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas_graficos.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        for ax in (self.ax_hist, self.ax_actividades, self.ax_criticidad, self.ax_convergencia):
            ax.text(0.5, 0.5, "Todavía no corriste ninguna simulación",
                    ha="center", va="center", fontsize=9, color="#888")
            ax.set_xticks([]); ax.set_yticks([])
        self.canvas_graficos.draw()

    def _actualizar_graficos(self, p, r):
        # --- 1) Histograma de frecuencias ---------------------------------
        ax = self.ax_hist
        ax.clear()
        etiquetas = []
        for k in range(10):
            desde = r["inicio_ultimo"] if k == 9 else r["bordes"][k]
            etiquetas.append(f"{desde:.0f}+" if k == 9 else f"{desde:.0f}")
        ax.bar(etiquetas, r["histograma"], color=COLOR_ACENTO)
        ax.set_title("Distribución de frecuencias (10 intervalos)", fontsize=9)
        ax.set_xlabel("Minuto de inicio del intervalo", fontsize=8)
        ax.set_ylabel("Frecuencia", fontsize=8)
        ax.tick_params(labelsize=7)

        # --- 2) Duración promedio por actividad ---------------------------
        ax = self.ax_actividades
        ax.clear()
        nombres = ["A", "B", "C", "D", "E", "F"]
        promedios = [r["stats"][n].media() for n in nombres]
        ax.bar(nombres, promedios, color=COLOR_RUTA1)
        ax.set_title("Duración promedio por actividad", fontsize=9)
        ax.set_ylabel("Minutos", fontsize=8)
        ax.tick_params(labelsize=8)
        for i, v in enumerate(promedios):
            ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=7)

        # --- 3) Proporción de actividad crítica (torta) --------------------
        ax = self.ax_criticidad
        ax.clear()
        valores = [r["ruta1_critica"], r["ruta2_critica"], r["empate_critico"]]
        etiquetas_pie = ["A → B", "C → D → E", "Empate"]
        colores_pie = [COLOR_RUTA1, COLOR_RUTA2, COLOR_EMPATE]
        # Si alguna categoría da 0 en las tres, evitamos el gráfico vacío
        if sum(valores) > 0:
            valores_no_cero = [(v, e, c) for v, e, c in zip(valores, etiquetas_pie, colores_pie) if v > 0]
            vals, etqs, cols = zip(*valores_no_cero)
            ax.pie(vals, labels=etqs, autopct="%1.1f%%", colors=cols,
                   textprops={"fontsize": 8})
        ax.set_title("Actividad crítica (cuello de botella)", fontsize=9)

        # --- 4) Convergencia del promedio total -----------------------------
        ax = self.ax_convergencia
        ax.clear()
        iteraciones = [pt[0] for pt in r["convergencia"]]
        promedios_acum = [pt[1] for pt in r["convergencia"]]
        ax.plot(iteraciones, promedios_acum, color=COLOR_ACENTO, linewidth=1.5)
        ax.axhline(r["stats"]["Total"].media(), color=COLOR_RUTA2, linestyle="--", linewidth=1,
                   label=f"Promedio final: {r['stats']['Total'].media():.2f}")
        ax.set_title("Convergencia del promedio del tiempo total", fontsize=9)
        ax.set_xlabel("Iteración", fontsize=8)
        ax.set_ylabel("Promedio acumulado (min)", fontsize=8)
        ax.legend(fontsize=7)
        ax.tick_params(labelsize=7)

        self.fig.tight_layout(pad=3.5)
        self.canvas_graficos.draw()

    # -----------------------------------------------------------------
    # PESTAÑA 5: resultado de la corrida de 99 simulaciones
    # -----------------------------------------------------------------
    def _armar_tab_99(self):
        f = self.tab_99
        self.lbl_99 = ttk.Label(f, text="Todavía no corriste esta simulación.", justify="left", font=("", 11))
        self.lbl_99.pack(anchor="w", padx=14, pady=16)

    # -----------------------------------------------------------------
    # Traduce el formulario (self.vars) al mismo diccionario "p" que
    # usa simulacion_logica.py
    # -----------------------------------------------------------------
    def leer_parametros(self):
        v = {k: var.get() for k, var in self.vars.items()}
        # ==========================================================
        # VALIDACIÓN DE N ITERACIONES
        # Debe ser un entero mayor que 0
        # ==========================================================
        if not v["nIter"].isdigit():
            messagebox.showwarning(
                "Dato inválido",
                "La cantidad de iteraciones debe ser un número entero positivo, "
                "sin letras ni decimales."
            )
            return None

        n_iter = int(v["nIter"])

        if n_iter <= 0:
            messagebox.showwarning(
                "Dato inválido",
                "La cantidad de iteraciones debe ser mayor que 0."
            )
            return None

        # ==========================================================
        # VALIDACIÓN DE LOS MÓDULOS
        # mB, mD, mE y mF deben ser enteros mayores que 0
        # ==========================================================
        modulos = {
            "mB": "B",
            "mD": "D",
            "mE": "E",
            "mF": "F",
        }

        for clave, variable in modulos.items():

            if not v[clave].isdigit():
                messagebox.showwarning(
                    "Dato inválido",
                    f"El módulo m de la variable {variable} debe ser un número "
                    f"entero positivo, sin letras ni decimales."
                )
                return None

            modulo = int(v[clave])

            if modulo <= 0:
                messagebox.showwarning(
                    "Dato inválido",
                    f"El módulo m de la variable {variable} debe ser mayor que 0."
                )
                return None

        # ==========================================================
        # RESTO DE LOS PARÁMETROS
        # ==========================================================
        num = lambda k: float(v[k])
        entero = lambda k: int(round(num(k)))

        return {
            "n": n_iter,
            "genB": {"sem": entero("semB"), "a": entero("aB"), "c": entero("cB"), "m": entero("mB")},
            "genD": {"sem": entero("semD"), "a": entero("aD"), "c": entero("cD"), "m": entero("mD")},
            "genE": {"sem": entero("semE"), "a": entero("aE"), "c": entero("cE"), "m": entero("mE")},
            "genF": {"sem": entero("semF"), "a": entero("aF"), "c": entero("cF"), "m": entero("mF")},
            "A": num("constA"),
            "B": {"val": [num("valB1"), num("valB2"), num("valB3")],
                  "prob": [num("probB1"), num("probB2"), num("probB3")]},
            "C": num("constC"),
            "D": {"min": num("dMin"), "max": num("dMax")},
            "E": {"media": num("mediaE")},
            "F": {"val": [num("valF1"), num("valF2")], "prob": [num("probF1"), num("probF2")]},
            "umbral1": num("umbral1"), "umbral2": num("umbral2"), "amplitud": num("amplitud"),
        }

    # -----------------------------------------------------------------
    # Botón "Simular N iteraciones"
    # -----------------------------------------------------------------
    def simular_click(self):
        p = self.leer_parametros()
        if p is None:
            return
        
        r = simular_n(p)
        self._mostrar_resultados(p, r)
        self._actualizar_graficos(p, r)
        self.notebook.select(self.tab_resultados)

    def _mostrar_resultados(self, p, r):
        n = r["n"]
        total = r["stats"]["Total"]

        resumen = (
            f"Iteraciones simuladas: {n}\n"
            f"Tiempo mínimo teórico (simulacro): {r['t_min']:.2f} min\n"
            f"Duración promedio del proyecto: {total.media():.4f} min   "
            f"(desvío: {total.desvio():.4f} min)\n"
            f"Mínimo / máximo observado: {total.minimo:.2f} / {total.maximo:.2f} min\n"
            f"P(Total ≤ {p['umbral1']:.0f} min) = {r['c_umbral1']/n*100:.4f} %      "
            f"P(Total ≥ {p['umbral2']:.0f} min) = {r['c_umbral2']/n*100:.4f} %"
        )
        self.lbl_resumen.config(text=resumen)

        self.tabla_actividades.delete(*self.tabla_actividades.get_children())
        nombres = {"A": "A · Verificación de pago", "B": "B · Picking", "C": "C · Etiqueta",
                   "D": "D · Packing", "E": "E · Control de calidad", "F": "F · Despacho"}
        for clave, nombre in nombres.items():
            ac = r["stats"][clave]
            self.tabla_actividades.insert(
                "", "end", text=nombre,
                values=(f"{ac.media():.4f}", f"{ac.minimo:.4f}", f"{ac.maximo:.4f}", f"{ac.desvio():.4f}"),
            )
        self.tabla_actividades["show"] = "tree headings"
        self.tabla_actividades.heading("#0", text="Actividad")
        self.tabla_actividades.column("#0", width=200, anchor="w")

        self.tabla_criticidad.delete(*self.tabla_criticidad.get_children())
        filas = [
            ("Rama A → B", r["ruta1_critica"]),
            ("Rama C → D → E", r["ruta2_critica"]),
            ("Empate exacto", r["empate_critico"]),
        ]
        for nombre, veces in filas:
            self.tabla_criticidad.insert("", "end", text=nombre, values=(veces, f"{veces/n*100:.4f} %"))

        self.tabla_histograma.delete(*self.tabla_histograma.get_children())
        for k in range(10):
            desde = r["inicio_ultimo"] if k == 9 else r["bordes"][k]
            if k == 9:
                etiqueta = f"≥ {desde:.2f}"
            else:
                hasta = r["inicio_ultimo"] if k == 8 else r["bordes"][k + 1]
                etiqueta = f"[{desde:.2f}, {hasta:.2f})"
            freq = r["histograma"][k]
            self.tabla_histograma.insert(
                "", "end", text=etiqueta, values=(freq, f"{freq/n*100:.4f} %")
            )

    # -----------------------------------------------------------------
    # Botón "Simular 99 corridas (95% de confianza)"
    # -----------------------------------------------------------------
    def simular99_click(self):
        p = self.leer_parametros()
        if p is None:
            return
        
        r99 = simular_99(p)
        texto = (
            f"Tiempo a fijar (95% de confianza): {r99['percentil95']:.2f} min\n"
            f"   (valor N.º {r99['posicion']} de 99 ordenados)\n\n"
            f"Promedio de las 99 corridas: {r99['promedio']:.4f} min\n"
            f"Mínimo / máximo observado: {r99['minimo']:.2f} / {r99['maximo']:.2f} min\n\n"
            f"Interpretación: si repetimos el proceso, en el 95% de esas 99 corridas\n"
            f"el proyecto terminó en {r99['percentil95']:.2f} minutos o menos."
        )
        self.lbl_99.config(text=texto)
        self.notebook.select(self.tab_99)


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionTP3(root)
    root.mainloop()
