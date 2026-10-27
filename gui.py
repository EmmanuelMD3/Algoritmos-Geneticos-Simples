"""Interfaz gráfica del Algoritmo Genético Simple. Ejecutar: python gui.py."""
from __future__ import annotations

import csv
from pathlib import Path
from queue import Empty, Queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ag.motor import ejecutar_ag
from ag.objetivos import MATRIZ_DISTANCIAS_EJEMPLO
from ejemplos import EJEMPLOS, ejecutar_ejemplo
from gui_logic import preparar_optimizacion, preparar_ruta


OPCIONES = {
    "objetivo": {"Minimizar": "min", "Maximizar": "max"},
    "representacion": {"Real": "real", "Binaria": "binaria"},
    "seleccion": {"Ruleta": "ruleta", "Ranking lineal": "ranking_lineal",
                  "Ranking no lineal": "ranking_no_lineal", "Torneo": "torneo", "SUS": "sus"},
    "cruce": {"Uniforme": "uniforme", "Aritmético": "aritmetico",
               "Plano": "plano", "BLX-α": "blx", "PMX": "pmx", "OX": "ox", "CX": "cx"},
    "mutacion": {"Uniforme": "uniforme", "No uniforme": "no_uniforme",
                  "Inversión de bit": "bitflip", "Intercambio": "intercambio"},
    "sustitucion": {"Generacional": "generacional", "Estado estable": "steady_state",
                     "Crowding": "crowding"},
}

VALORES_INICIALES = {
    "expresion": "(x-3)**2+2", "objetivo": "Minimizar", "dim": "1",
    "inferior": "-10", "superior": "10", "especificos": "",
    "representacion": "Real", "bits": "12", "poblacion": "80",
    "generaciones": "120", "seleccion": "Torneo", "cruce": "BLX-α",
    "mutacion": "No uniforme", "sustitucion": "Generacional",
    "pc": "0.85", "pm": "0.10", "k": "3", "amax": "1.6", "q": "0.5",
    "a_aritmetico": "0.25", "alfa_blx": "0.5", "b_mutacion": "1.0",
    "elitismo": "1", "cf": "3", "reemplazos": "10", "semilla": "42",
}

RUTA_INICIAL = {
    "seleccion": "Torneo", "cruce": "OX", "mutacion": "Intercambio",
    "sustitucion": "Generacional",
    "poblacion": "80", "generaciones": "80", "pc": "0.85", "pm": "0.25",
    "k": "3", "elitismo": "1", "cf": "3", "reemplazos": "10", "semilla": "42",
}


def _codigo(clave: str, etiqueta: str) -> str:
    return OPCIONES[clave][etiqueta]


def _etiqueta(clave: str, codigo: str) -> str:
    return next((nombre for nombre, valor in OPCIONES[clave].items() if valor == codigo), codigo)


class MarcoDesplazable(ttk.Frame):
    def __init__(self, padre):
        super().__init__(padre)
        lienzo = tk.Canvas(self, highlightthickness=0, bg="#f5f7fb")
        barra = ttk.Scrollbar(self, orient="vertical", command=lienzo.yview)
        lienzo.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        lienzo.pack(side="left", fill="both", expand=True)
        self.interior = ttk.Frame(lienzo, padding=14)
        ventana = lienzo.create_window((0, 0), window=self.interior, anchor="nw")
        self.interior.bind("<Configure>", lambda e: lienzo.configure(scrollregion=lienzo.bbox("all")))
        lienzo.bind("<Configure>", lambda e: lienzo.itemconfigure(ventana, width=e.width))

        def desplazar(evento):
            if not lienzo.winfo_ismapped() or not evento.delta:
                return
            x, y = lienzo.winfo_pointerxy()
            izquierda, arriba = lienzo.winfo_rootx(), lienzo.winfo_rooty()
            if izquierda <= x < izquierda + lienzo.winfo_width() and arriba <= y < arriba + lienzo.winfo_height():
                lienzo.yview_scroll(-1 if evento.delta > 0 else 1, "units")
        lienzo.bind_all("<MouseWheel>", desplazar, add="+")


class PanelResultados(ttk.Frame):
    COLUMNAS = ("generacion", "mejor_generacion", "mejor_historico", "promedio")

    def __init__(self, padre):
        super().__init__(padre, padding=12)
        self.resultado = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=3)
        self.rowconfigure(3, weight=2)

        cabecera = ttk.Frame(self)
        cabecera.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(cabecera, text="Resultados", style="Titulo.TLabel").pack(side="left")
        self.boton_exportar = ttk.Button(cabecera, text="Exportar historial a CSV",
                                          command=self.exportar, state="disabled")
        self.boton_exportar.pack(side="right", padx=(8, 0))
        ttk.Button(cabecera, text="Limpiar", command=self.limpiar).pack(side="right")

        self.resumen = tk.Text(self, height=6, wrap="word", relief="flat",
                               bg="#edf4f8", fg="#173044", padx=12, pady=8,
                               font=("Segoe UI", 10), state="disabled")
        self.resumen.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.figura = Figure(figsize=(6, 3), dpi=100, facecolor="#ffffff")
        self.ejes = self.figura.add_subplot(111)
        self.lienzo = FigureCanvasTkAgg(self.figura, master=self)
        self.lienzo.get_tk_widget().grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        tabla_marco = ttk.LabelFrame(self, text="Estadísticas por generación", padding=5)
        tabla_marco.grid(row=3, column=0, sticky="nsew")
        tabla_marco.columnconfigure(0, weight=1)
        tabla_marco.rowconfigure(0, weight=1)
        self.tabla = ttk.Treeview(tabla_marco, columns=self.COLUMNAS,
                                  show="headings", height=7)
        for clave, titulo, ancho in (
            ("generacion", "Generación", 90),
            ("mejor_generacion", "Mejor generación", 135),
            ("mejor_historico", "Mejor histórico", 135),
            ("promedio", "Promedio", 120),
        ):
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=ancho, minwidth=75, anchor="center", stretch=True)
        barra = ttk.Scrollbar(tabla_marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.limpiar()

    def _texto(self, contenido: str):
        self.resumen.configure(state="normal")
        self.resumen.delete("1.0", "end")
        self.resumen.insert("1.0", contenido)
        self.resumen.configure(state="disabled")

    def limpiar(self):
        self.resultado = None
        self.boton_exportar.configure(state="disabled")
        self._texto("Configura los parámetros y pulsa Ejecutar.")
        self.tabla.delete(*self.tabla.get_children())
        self.ejes.clear()
        self.ejes.set_title("Convergencia")
        self.ejes.set_xlabel("Generación")
        self.ejes.set_ylabel("Valor de la función")
        self.ejes.grid(alpha=0.2)
        self.figura.tight_layout()
        self.lienzo.draw_idle()

    def mostrar(self, resultado, config, contexto: str):
        self.resultado = resultado
        solucion = resultado.mejor_solucion
        if config.representacion == "permutacion":
            detalle = " → ".join(map(str, solucion + [solucion[0]]))
            rotulo = "Mejor ruta (ciclo)"
            valor = "Distancia total"
        else:
            detalle = ", ".join(f"x{i}={float(x):.6g}" for i, x in enumerate(solucion))
            rotulo = "Mejor solución"
            valor = "Mejor valor de f"
        self._texto(
            f"{contexto}\n{rotulo}: {detalle}\n{valor}: {resultado.mejor_valor:.10g}\n"
            f"Población: {config.tam_poblacion}  ·  Generaciones: {config.generaciones}  ·  "
            f"Representación: {dict(real='Real', binaria='Binaria', permutacion='Permutación')[config.representacion]}\n"
            f"Selección: {_etiqueta('seleccion', config.seleccion)}  ·  "
            f"Cruce: {_etiqueta('cruce', config.cruce)}  ·  "
            f"Mutación: {_etiqueta('mutacion', config.mutacion)}  ·  "
            f"Sustitución: {_etiqueta('sustitucion', config.sustitucion)}"
        )
        self.tabla.delete(*self.tabla.get_children())
        for fila in resultado.historial:
            self.tabla.insert("", "end", values=(
                fila["generacion"],
                f"{fila['mejor_generacion']:.8g}",
                f"{fila['mejor_historico']:.8g}",
                f"{fila['promedio']:.8g}",
            ))
        self.ejes.clear()
        generaciones = [fila["generacion"] for fila in resultado.historial]
        for clave, titulo, color in (
            ("mejor_historico", "Mejor histórico", "#0a8f78"),
            ("mejor_generacion", "Mejor generación", "#3478bf"),
            ("promedio", "Promedio", "#d18a27"),
        ):
            self.ejes.plot(generaciones, [fila[clave] for fila in resultado.historial],
                           label=titulo, color=color, linewidth=1.7)
        self.ejes.set_title("Convergencia")
        self.ejes.set_xlabel("Generación")
        self.ejes.set_ylabel("Valor de la función")
        self.ejes.grid(alpha=0.2)
        self.ejes.legend(loc="best", fontsize=8)
        self.figura.tight_layout()
        self.lienzo.draw_idle()
        self.boton_exportar.configure(state="normal")

    def exportar(self):
        if self.resultado is None:
            return
        ruta = filedialog.asksaveasfilename(
            parent=self, title="Guardar historial", defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")], initialfile="historial_ag.csv",
        )
        if not ruta:
            return
        try:
            with Path(ruta).open("w", encoding="utf-8-sig", newline="") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=self.COLUMNAS)
                escritor.writeheader()
                escritor.writerows(self.resultado.historial)
        except OSError as exc:
            messagebox.showerror("No se pudo exportar", str(exc), parent=self)
            return
        messagebox.showinfo("Historial exportado", f"Archivo guardado en:\n{ruta}", parent=self)


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Algoritmo Genético Simple · Cómputo Evolutivo")
        ancho = min(1280, self.winfo_screenwidth() - 60)
        alto = min(820, self.winfo_screenheight() - 90)
        self.geometry(f"{max(760, ancho)}x{max(550, alto)}")
        self.minsize(760, 550)
        self.configure(bg="#f5f7fb")
        self._estilo()
        self.cola = Queue()
        self.ocupado = False
        self.botones_ejecutar = []
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        cabecera = tk.Frame(self, bg="#173044", padx=22, pady=14)
        cabecera.pack(fill="x")
        tk.Label(cabecera, text="Algoritmo Genético Simple", bg="#173044",
                 fg="white", font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(cabecera, text="Optimización · operadores · rutas", bg="#173044",
                 fg="#b9d5df", font=("Segoe UI", 10)).pack(anchor="w")

        self.estado = tk.StringVar(value="Listo para ejecutar")
        ttk.Label(self, textvariable=self.estado, style="Estado.TLabel",
                  anchor="w", padding=(16, 5)).pack(side="bottom", fill="x")
        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=12, pady=(10, 4))
        self._crear_optimizacion()
        self._crear_ejemplos()
        self._crear_rutas()
        self.after(100, self._procesar_cola)

    def _estilo(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("TFrame", background="#f5f7fb")
        estilo.configure("TLabel", background="#f5f7fb", foreground="#173044",
                         font=("Segoe UI", 10))
        estilo.configure("Titulo.TLabel", font=("Segoe UI Semibold", 15))
        estilo.configure("Nota.TLabel", foreground="#536b7b", font=("Segoe UI", 9))
        estilo.configure("Estado.TLabel", background="#e9eff4", foreground="#355365")
        estilo.configure("TLabelframe", background="#f5f7fb", bordercolor="#d7e1e8")
        estilo.configure("TLabelframe.Label", background="#f5f7fb",
                         foreground="#173044", font=("Segoe UI Semibold", 10))
        estilo.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        estilo.configure("Accion.TButton", foreground="white", background="#087e75")
        estilo.map("Accion.TButton", background=[("active", "#0a9a8e"),
                                                 ("disabled", "#a5c3c0")])
        estilo.configure("TNotebook", background="#f5f7fb")
        estilo.configure("TNotebook.Tab", font=("Segoe UI Semibold", 10), padding=(18, 9))
        estilo.configure("Treeview", rowheight=25, font=("Segoe UI", 9))

    def _grupo(self, padre, titulo):
        grupo = ttk.LabelFrame(padre, text=titulo, padding=10)
        grupo.pack(fill="x", pady=(0, 10))
        grupo.columnconfigure(1, weight=1)
        return grupo

    def _fila(self, grupo, fila, titulo, variable, opciones=None, rango=None):
        ttk.Label(grupo, text=titulo).grid(row=fila, column=0, sticky="w", padx=(0, 8), pady=4)
        if opciones is not None:
            control = ttk.Combobox(grupo, textvariable=variable, values=opciones,
                                   state="readonly", width=20)
        elif rango is not None:
            control = ttk.Spinbox(grupo, textvariable=variable, from_=rango[0],
                                   to=rango[1], increment=rango[2], width=18)
        else:
            control = ttk.Entry(grupo, textvariable=variable, width=22)
        control.grid(row=fila, column=1, sticky="ew", pady=4)
        return control

    def _panel_doble(self, titulo):
        pagina = ttk.Frame(self.pestanas)
        self.pestanas.add(pagina, text=titulo)
        division = ttk.PanedWindow(pagina, orient="horizontal")
        division.pack(fill="both", expand=True)
        desplazable = MarcoDesplazable(division)
        resultados = PanelResultados(division)
        division.add(desplazable, weight=1)
        division.add(resultados, weight=2)
        def ubicar_divisor(evento):
            if evento.width < 760:
                return
            division.unbind("<Configure>")
            division.after_idle(lambda: division.sashpos(
                0, min(460, max(345, division.winfo_width() // 3))))
        division.bind("<Configure>", ubicar_divisor)
        return desplazable.interior, resultados

    def _crear_optimizacion(self):
        formulario, self.resultados_opt = self._panel_doble("Optimización")
        self.opt = {clave: tk.StringVar(value=valor) for clave, valor in VALORES_INICIALES.items()}
        ttk.Label(formulario, text="Configurar optimización", style="Titulo.TLabel").pack(anchor="w", pady=(0, 12))

        grupo = self._grupo(formulario, "Función objetivo y dominio")
        self._fila(grupo, 0, "Función f(x)", self.opt["expresion"])
        self._fila(grupo, 1, "Objetivo", self.opt["objetivo"], list(OPCIONES["objetivo"]))
        self._fila(grupo, 2, "Número de variables", self.opt["dim"], rango=(1, 100, 1))
        self._fila(grupo, 3, "Límite inferior común", self.opt["inferior"])
        self._fila(grupo, 4, "Límite superior común", self.opt["superior"])
        self._fila(grupo, 5, "Límites por variable", self.opt["especificos"])
        ttk.Label(grupo, text="Opcional: -10:10; -5:5 para x0 y x1",
                  style="Nota.TLabel").grid(row=6, column=0, columnspan=2, sticky="w")

        grupo = self._grupo(formulario, "Población y representación")
        self.combo_representacion = self._fila(grupo, 0, "Representación",
                                             self.opt["representacion"], list(OPCIONES["representacion"]))
        self._fila(grupo, 1, "Bits por variable", self.opt["bits"], rango=(1, 30, 1))
        self._fila(grupo, 2, "Tamaño de población", self.opt["poblacion"], rango=(2, 10000, 1))
        self._fila(grupo, 3, "Generaciones", self.opt["generaciones"], rango=(1, 100000, 1))
        self._fila(grupo, 4, "Semilla aleatoria", self.opt["semilla"])

        grupo = self._grupo(formulario, "Operadores")
        self._fila(grupo, 0, "Selección", self.opt["seleccion"], list(OPCIONES["seleccion"]))
        self.combo_cruce = self._fila(grupo, 1, "Cruce", self.opt["cruce"],
                                      ["Uniforme", "Aritmético", "Plano", "BLX-α"])
        self.combo_mutacion = self._fila(grupo, 2, "Mutación", self.opt["mutacion"],
                                         ["Uniforme", "No uniforme"])
        self._fila(grupo, 3, "Sustitución", self.opt["sustitucion"], list(OPCIONES["sustitucion"]))
        self._fila(grupo, 4, "Probabilidad de cruce", self.opt["pc"], rango=(0, 1, .01))
        self._fila(grupo, 5, "Probabilidad de mutación", self.opt["pm"], rango=(0, 1, .01))

        grupo = self._grupo(formulario, "Parámetros adicionales")
        ajustes = (
            ("Torneo k", "k", (1, 10000, 1)),
            ("Ranking lineal amax", "amax", (1, 2, .1)),
            ("Ranking no lineal q", "q", (0.01, 1, .05)),
            ("Peso aritmético a", "a_aritmetico", (0, 1, .05)),
            ("Alfa BLX", "alfa_blx", (0, 10, .1)),
            ("Exponente mutación b", "b_mutacion", (0.1, 10, .1)),
            ("Elitismo", "elitismo", (0, 10000, 1)),
            ("Factor crowding", "cf", (1, 10000, 1)),
            ("Reemplazos por generación", "reemplazos", (1, 10000, 1)),
        )
        for fila, (titulo, clave, rango) in enumerate(ajustes):
            self._fila(grupo, fila, titulo, self.opt[clave], rango=rango)

        acciones = ttk.Frame(formulario)
        acciones.pack(fill="x", pady=(0, 20))
        boton = ttk.Button(acciones, text="Ejecutar", style="Accion.TButton",
                           command=self._ejecutar_opt)
        boton.pack(side="left", padx=(0, 5))
        self.botones_ejecutar.append(boton)
        ttk.Button(acciones, text="Restaurar parámetros", command=self._restaurar_opt).pack(side="left", padx=5)
        ttk.Button(acciones, text="Limpiar", command=self.resultados_opt.limpiar).pack(side="left", padx=5)
        self.combo_representacion.bind("<<ComboboxSelected>>", self._actualizar_operadores)
        self._actualizar_operadores()

    def _actualizar_operadores(self, _evento=None):
        representacion = _codigo("representacion", self.opt["representacion"].get())
        compatibles = {
            "real": (["Uniforme", "Aritmético", "Plano", "BLX-α"],
                     ["Uniforme", "No uniforme"]),
            "binaria": (["Uniforme"], ["Inversión de bit"]),
        }
        cruces, mutaciones = compatibles[representacion]
        self.combo_cruce.configure(values=cruces, state="readonly")
        self.combo_mutacion.configure(values=mutaciones, state="readonly")
        if self.opt["cruce"].get() not in cruces:
            self.opt["cruce"].set(cruces[-1] if representacion == "real" else cruces[0])
        if self.opt["mutacion"].get() not in mutaciones:
            self.opt["mutacion"].set(mutaciones[-1])

    def _restaurar_opt(self):
        for clave, valor in VALORES_INICIALES.items():
            self.opt[clave].set(valor)
        self._actualizar_operadores()
        self.resultados_opt.limpiar()
        self.estado.set("Parámetros de optimización restaurados")

    def _campos(self, variables):
        campos = {clave: valor.get().strip() for clave, valor in variables.items()}
        for clave in ("objetivo", "representacion", "seleccion", "cruce", "mutacion", "sustitucion"):
            if clave in campos:
                campos[clave] = _codigo(clave, campos[clave])
        return campos

    def _ejecutar_opt(self):
        try:
            campos = self._campos(self.opt)
            funcion, config = preparar_optimizacion(campos)
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Revisa los parámetros", str(exc), parent=self)
            return
        self._lanzar(lambda: ejecutar_ag(funcion, config),
                     lambda resultado: self.resultados_opt.mostrar(
                         resultado, config, f"Función: {campos['expresion']}"))

    def _crear_ejemplos(self):
        pagina = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(pagina, text="Ejemplos (17)")
        pagina.columnconfigure(1, weight=2)
        pagina.rowconfigure(1, weight=1)
        ttk.Label(pagina, text="Métodos de la presentación", style="Titulo.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        lista_marco = ttk.Frame(pagina)
        lista_marco.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        lista_marco.rowconfigure(0, weight=1)
        lista_marco.columnconfigure(0, weight=1)
        self.lista_ejemplos = ttk.Treeview(lista_marco, columns=("num", "nombre", "tipo"),
                                           show="headings", selectmode="browse")
        for clave, titulo, ancho in (("num", "N.º", 45), ("nombre", "Método", 220),
                                     ("tipo", "Tipo", 95)):
            self.lista_ejemplos.heading(clave, text=titulo)
            self.lista_ejemplos.column(clave, width=ancho, anchor="w", stretch=clave == "nombre")
        for numero, (nombre, tipo, _datos) in enumerate(EJEMPLOS, 1):
            self.lista_ejemplos.insert("", "end", iid=str(numero), values=(numero, nombre, tipo))
        barra = ttk.Scrollbar(lista_marco, orient="vertical", command=self.lista_ejemplos.yview)
        self.lista_ejemplos.configure(yscrollcommand=barra.set)
        self.lista_ejemplos.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.lista_ejemplos.bind("<<TreeviewSelect>>", self._mostrar_datos_ejemplo)

        detalle = ttk.Frame(pagina)
        detalle.grid(row=1, column=1, sticky="nsew")
        detalle.columnconfigure(0, weight=1)
        detalle.rowconfigure(2, weight=1)
        self.titulo_ejemplo = tk.StringVar()
        self.datos_ejemplo = tk.StringVar()
        ttk.Label(detalle, textvariable=self.titulo_ejemplo,
                  style="Titulo.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(detalle, textvariable=self.datos_ejemplo, wraplength=600,
                  justify="left").grid(row=1, column=0, sticky="ew", pady=12)
        self.salida_ejemplos = tk.Text(detalle, wrap="word", relief="flat", bg="#edf4f8",
                                       fg="#173044", font=("Consolas", 10), padx=15, pady=12)
        self.salida_ejemplos.grid(row=2, column=0, sticky="nsew")
        acciones = ttk.Frame(detalle)
        acciones.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        boton = ttk.Button(acciones, text="Ejecutar seleccionado", style="Accion.TButton",
                           command=self._ejecutar_ejemplo)
        boton.pack(side="left", padx=(0, 8))
        self.botones_ejecutar.append(boton)
        boton = ttk.Button(acciones, text="Ejecutar los 17", command=self._ejecutar_todos)
        boton.pack(side="left", padx=(0, 8))
        self.botones_ejecutar.append(boton)
        ttk.Button(acciones, text="Limpiar", command=self._limpiar_ejemplos).pack(side="left")
        self.lista_ejemplos.selection_set("1")
        self._mostrar_datos_ejemplo()
        self._limpiar_ejemplos()

    def _mostrar_datos_ejemplo(self, _evento=None):
        seleccion = self.lista_ejemplos.selection()
        if seleccion:
            numero = int(seleccion[0])
            nombre, tipo, datos = EJEMPLOS[numero - 1]
            self.titulo_ejemplo.set(f"{numero}. {nombre}")
            self.datos_ejemplo.set(f"Tipo de operador: {tipo}\nDatos utilizados: {datos}")

    def _poner_salida(self, texto):
        self.salida_ejemplos.configure(state="normal")
        self.salida_ejemplos.delete("1.0", "end")
        self.salida_ejemplos.insert("1.0", texto)
        self.salida_ejemplos.configure(state="disabled")

    def _limpiar_ejemplos(self):
        self._poner_salida("Selecciona un método y pulsa Ejecutar seleccionado.")

    def _ejecutar_ejemplo(self):
        seleccion = self.lista_ejemplos.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un ejemplo", "Elige un método de la lista.", parent=self)
            return
        numero = int(seleccion[0])
        nombre, tipo, datos = EJEMPLOS[numero - 1]
        self._lanzar(lambda: ejecutar_ejemplo(numero),
                     lambda salida: self._poner_salida(
                         f"Ejemplo {numero}: {nombre}\nTipo: {tipo}\nDatos: {datos}\n\nResultado:\n{salida}"))

    def _ejecutar_todos(self):
        def tarea():
            return "\n\n".join(
                f"[{i}] {nombre}\nTipo: {tipo}\nDatos: {datos}\nResultado: {ejecutar_ejemplo(i)}"
                for i, (nombre, tipo, datos) in enumerate(EJEMPLOS, 1)
            )
        self._lanzar(tarea, self._poner_salida)

    def _crear_rutas(self):
        formulario, self.resultados_ruta = self._panel_doble("Permutaciones / rutas")
        self.ruta = {clave: tk.StringVar(value=valor) for clave, valor in RUTA_INICIAL.items()}
        ttk.Label(formulario, text="Optimización de rutas", style="Titulo.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(formulario, text="Ciclo de 6 ciudades (0–5). La ruta regresa a la ciudad inicial.",
                  wraplength=390).pack(anchor="w", pady=(0, 10))
        grupo = self._grupo(formulario, "Matriz de distancias del proyecto")
        matriz = "    " + " ".join(f"{i:>3}" for i in range(len(MATRIZ_DISTANCIAS_EJEMPLO))) + "\n"
        matriz += "\n".join(f"{i}  " + " ".join(f"{valor:>3}" for valor in fila)
                           for i, fila in enumerate(MATRIZ_DISTANCIAS_EJEMPLO))
        ttk.Label(grupo, text=matriz, font=("Consolas", 10)).grid(row=0, column=0, sticky="w")

        grupo = self._grupo(formulario, "Operadores y ejecución")
        self._fila(grupo, 0, "Cruce", self.ruta["cruce"], ["PMX", "OX", "CX"])
        self._fila(grupo, 1, "Mutación", self.ruta["mutacion"], ["Intercambio"])
        self._fila(grupo, 2, "Selección", self.ruta["seleccion"], list(OPCIONES["seleccion"]))
        self._fila(grupo, 3, "Sustitución", self.ruta["sustitucion"], list(OPCIONES["sustitucion"]))
        for fila, (titulo, clave, rango) in enumerate((
            ("Tamaño de población", "poblacion", (2, 10000, 1)),
            ("Generaciones", "generaciones", (1, 100000, 1)),
            ("Probabilidad de cruce", "pc", (0, 1, .01)),
            ("Probabilidad de mutación", "pm", (0, 1, .01)),
            ("Torneo k", "k", (1, 10000, 1)),
            ("Elitismo", "elitismo", (0, 10000, 1)),
            ("Factor crowding", "cf", (1, 10000, 1)),
            ("Reemplazos", "reemplazos", (1, 10000, 1)),
            ("Semilla", "semilla", (-999999999, 999999999, 1)),
        ), 4):
            self._fila(grupo, fila, titulo, self.ruta[clave], rango=rango)

        acciones = ttk.Frame(formulario)
        acciones.pack(fill="x", pady=(0, 20))
        boton = ttk.Button(acciones, text="Ejecutar ruta", style="Accion.TButton",
                           command=self._ejecutar_ruta)
        boton.pack(side="left", padx=(0, 5))
        self.botones_ejecutar.append(boton)
        ttk.Button(acciones, text="Restaurar parámetros", command=self._restaurar_ruta).pack(side="left", padx=5)
        ttk.Button(acciones, text="Limpiar", command=self.resultados_ruta.limpiar).pack(side="left", padx=5)

    def _restaurar_ruta(self):
        for clave, valor in RUTA_INICIAL.items():
            self.ruta[clave].set(valor)
        self.resultados_ruta.limpiar()
        self.estado.set("Parámetros de ruta restaurados")

    def _ejecutar_ruta(self):
        try:
            campos = self._campos(self.ruta)
            funcion, config = preparar_ruta(campos)
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Revisa los parámetros", str(exc), parent=self)
            return
        self._lanzar(lambda: ejecutar_ag(funcion, config),
                     lambda resultado: self.resultados_ruta.mostrar(
                         resultado, config, "Ruta circular con la matriz del proyecto"))

    def _lanzar(self, trabajo, al_terminar):
        if self.ocupado:
            return
        self.ocupado = True
        self.estado.set("Ejecutando… la ventana sigue disponible")
        for boton in self.botones_ejecutar:
            boton.configure(state="disabled")

        def trabajador():
            try:
                self.cola.put((al_terminar, True, trabajo()))
            except Exception as exc:
                self.cola.put((al_terminar, False, str(exc)))
        threading.Thread(target=trabajador, daemon=True).start()

    def _procesar_cola(self):
        try:
            while True:
                al_terminar, exito, dato = self.cola.get_nowait()
                self.ocupado = False
                for boton in self.botones_ejecutar:
                    boton.configure(state="normal")
                if exito:
                    try:
                        al_terminar(dato)
                        self.estado.set("Ejecución terminada")
                    except Exception as exc:
                        self.estado.set("No se pudieron mostrar los resultados")
                        messagebox.showerror("Error al mostrar resultados", str(exc), parent=self)
                else:
                    self.estado.set("La ejecución terminó con un error")
                    messagebox.showerror("No se pudo ejecutar", dato, parent=self)
        except Empty:
            pass
        self.after(100, self._procesar_cola)


def main():
    Aplicacion().mainloop()


if __name__ == "__main__":
    main()
