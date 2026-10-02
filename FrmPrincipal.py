"""Ventana principal equivalente a FrmPrincipal.pas (tkinter)."""
from __future__ import annotations

import csv
import os
from math import inf
from pathlib import Path
from time import perf_counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import Declaraciones
from Declaraciones import T2, TLang
from Funciones_y_Procedimientos import EjecutarAlgoritomoDeHormigas, InicializarVariables
from paralelonivel1 import ejecutar_corridas_multiples_paralelo
from Paralelonivel2 import ejecutar_corrida_nivel2


class TForm1(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        self.master = master
        self.pack(fill="both", expand=True)
        self.TablaDatos: list[list[float]] = []
        self.NombreTabla = ""
        self._crear_controles()
        self.ApplyLanguage()

    def _crear_controles(self) -> None:
        ttk.Style().configure("Action.TButton", padding=(8, 9))
        self.Variables = {
            "R": tk.StringVar(value="7"), "CantiHormigas": tk.StringVar(value="10"),
            "Alpha": tk.StringVar(value="0.25"), "Beta": tk.StringVar(value="2.5"),
            "Q": tk.StringVar(value="250"), "Rho": tk.StringVar(value="0.5"),
            "MaxIteraSinMejora": tk.StringVar(value="10"), "K_Medias_Cada": tk.StringVar(value="2"),
            "CantidadDeCorridasMultiplesGeneral": tk.StringVar(value="10"),
            "MejoraKMediasActiva": tk.BooleanVar(value=True), "TolInercia": tk.StringVar(value="0.001"),
            # --- Nivel 1 de paralelismo ---
            "ParalelizarCorridas": tk.BooleanVar(value=False),
            "NumProcesos": tk.StringVar(value=str(os.cpu_count() or 4)),
            # --- Nivel 2 de paralelismo ---
            "ParalelizarHormigas": tk.BooleanVar(value=False),
            "NumProcesosNivel2": tk.StringVar(value=str(os.cpu_count() or 4)),
            "SemillaNivel2": tk.StringVar(value=""), #vacío = no reproducible (random.seed())
        }

        # Tres columnas superiores, como el formulario Delphi mostrado: datos | control | resultados.
        # La columna central conserva siempre su ancho: no se comprime al reducir la ventana.
        self.columnconfigure(0, weight=1, minsize=390)
        self.columnconfigure(1, weight=0, minsize=320)
        self.columnconfigure(2, weight=1, minsize=300)
        self.rowconfigure(0, weight=1, minsize=345)
        self.rowconfigure(1, weight=0, minsize=185)
        MarcoDatos = ttk.Frame(self, width=390, height=345)
        # Impide que nuevas columnas cambien el tamaño de la ventana; se navegan con scroll.
        MarcoDatos.grid_propagate(False)
        MarcoDatos.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.lblTabla = ttk.Label(MarcoDatos, text="Tabla de datos originales")
        self.lblTabla.grid(row=0, column=0, columnspan=2, sticky="w")
        self.TablaCargarDatos = ttk.Treeview(MarcoDatos, show="headings", height=17)
        BarraDatos = ttk.Scrollbar(MarcoDatos, orient="vertical", command=self.TablaCargarDatos.yview)
        BarraHorizontalDatos = ttk.Scrollbar(MarcoDatos, orient="horizontal", command=self.TablaCargarDatos.xview)
        self.TablaCargarDatos.configure(yscrollcommand=BarraDatos.set, xscrollcommand=BarraHorizontalDatos.set)
        self.TablaCargarDatos.grid(row=1, column=0, sticky="nsew")
        BarraDatos.grid(row=1, column=1, sticky="ns")
        BarraHorizontalDatos.grid(row=2, column=0, sticky="ew")
        MarcoDatos.columnconfigure(0, weight=1); MarcoDatos.rowconfigure(1, weight=1)

        self.grpPanel = ttk.LabelFrame(self, text="Panel de control", padding=8)
        self.grpPanel.grid(row=0, column=1, sticky="nsew", padx=2)
        self.grpKMedias = ttk.LabelFrame(self.grpPanel, text="Estrategia de k-medias", padding=6)
        self.grpKMedias.grid(row=0, column=0, sticky="ew")
        ttk.Checkbutton(self.grpKMedias, text="Usar esta estrategia", variable=self.Variables["MejoraKMediasActiva"]).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(self.grpKMedias, text="Aplicar estrategia cada").grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Spinbox(self.grpKMedias, from_=1, to=9999, textvariable=self.Variables["K_Medias_Cada"], width=6).grid(row=1, column=1, padx=5, pady=(5, 0))
        ttk.Label(self.grpKMedias, text="iteraciones").grid(row=1, column=2, sticky="w", pady=(5, 0))
        self.grpEntrada = ttk.LabelFrame(self.grpPanel, text="Parámetros de entrada", padding=6)
        self.grpEntrada.grid(row=1, column=0, sticky="ew", pady=(7, 0))
        self._control_numerico(self.grpEntrada, "Número de clases", "K=", "R", 0)
        self._control_numerico(self.grpEntrada, "Cantidad de hormigas", "N=", "CantiHormigas", 1)
        ttk.Label(self.grpEntrada, text="Parámetros adicionales:").grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 3))
        for Fila, (Izquierda, Derecha) in enumerate((("Alpha", "Beta"), ("Q", "Rho")), start=3):
            for Columna, Nombre in ((0, Izquierda), (2, Derecha)):
                ttk.Label(self.grpEntrada, text={"Alpha": "α=", "Beta": "β=", "Q": "Q=", "Rho": "ρ="}[Nombre]).grid(row=Fila, column=Columna, sticky="e", padx=(0, 3))
                ttk.Entry(self.grpEntrada, textvariable=self.Variables[Nombre], width=9).grid(row=Fila, column=Columna + 1, sticky="w", padx=(0, 9))
        self._control_numerico(self.grpEntrada, "Número de corridas múltiples", "", "CantidadDeCorridasMultiplesGeneral", 5)
        ttk.Label(self.grpEntrada, text="Iteraciones sin mejora\nantes de detenerse:").grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Spinbox(self.grpEntrada, from_=1, to=99999, textvariable=self.Variables["MaxIteraSinMejora"], width=7).grid(row=6, column=2, sticky="e", pady=(6, 0))

        # Resultados a la derecha: se extienden desde arriba hasta abajo y siempre usan scroll.
        MarcoResultados = ttk.Frame(self, width=300, height=540)
        MarcoResultados.grid_propagate(False)
        MarcoResultados.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(6, 0))
        self.lblResultados = ttk.Label(MarcoResultados, text="Inercia intraclase y tiempo por corrida")
        self.lblResultados.grid(row=0, column=0, columnspan=2, sticky="w")
        self.ListaResultados = ttk.Treeview(MarcoResultados, show="headings", height=26)
        BarraResultados = ttk.Scrollbar(MarcoResultados, orient="vertical", command=self.ListaResultados.yview)
        self.ListaResultados.configure(yscrollcommand=BarraResultados.set)
        self.ListaResultados.grid(row=1, column=0, sticky="nsew")
        BarraResultados.grid(row=1, column=1, sticky="ns")
        MarcoResultados.columnconfigure(0, weight=1); MarcoResultados.rowconfigure(1, weight=1)

        MarcoInferior = ttk.Frame(self)
        MarcoInferior.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 4), pady=(7, 0))
        MarcoInferior.columnconfigure(0, minsize=190)
        MarcoInferior.columnconfigure(1, minsize=210)
        MarcoInferior.columnconfigure(2, minsize=300)
        MarcoAcciones = ttk.Frame(MarcoInferior); MarcoAcciones.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.cmdCargarDatos = ttk.Button(MarcoAcciones, command=self.cmdCargarDatosClick, style="Action.TButton"); self.cmdCargarDatos.pack(fill="x", pady=2)
        self.btnCorridaUnica = ttk.Button(MarcoAcciones, command=self.btnCorridaUnicaClick, style="Action.TButton"); self.btnCorridaUnica.pack(fill="x", pady=2)
        # --- Nivel 2 de paralelismo: controles nuevos (aplican solo a Corrida única) ---
        self.chkParalelizarHormigas = ttk.Checkbutton(MarcoAcciones, text="Paralelizar hormigas (Nivel 2)", variable=self.Variables["ParalelizarHormigas"])
        self.chkParalelizarHormigas.pack(fill="x", pady=(2, 0))
        MarcoProcesosNivel2 = ttk.Frame(MarcoAcciones); MarcoProcesosNivel2.pack(fill="x", pady=(0, 2))
        ttk.Label(MarcoProcesosNivel2, text="Procesos:").pack(side="left")
        ttk.Spinbox(MarcoProcesosNivel2, from_=1, to=max(1, os.cpu_count() or 8), textvariable=self.Variables["NumProcesosNivel2"], width=5).pack(side="right")
        MarcoSemilla = ttk.Frame(MarcoAcciones); MarcoSemilla.pack(fill="x", pady=(0, 2))
        ttk.Label(MarcoSemilla, text="Semilla:").pack(side="left")
        ttk.Entry(MarcoSemilla, textvariable=self.Variables["SemillaNivel2"], width=8).pack(side="right")
        # --- fin de controles nuevos ---
        self.btnOptimizacion = ttk.Button(MarcoAcciones, command=self.btnOptimizacionClick, style="Action.TButton"); self.btnOptimizacion.pack(fill="x", pady=2)
        MarcoIdioma = ttk.Frame(MarcoAcciones); MarcoIdioma.pack(fill="x", pady=(5, 0))
        self.lblIdioma = ttk.Label(MarcoIdioma, text="Idioma:"); self.lblIdioma.pack(side="left")
        self.cmbIdioma = ttk.Combobox(MarcoIdioma, values=("Español", "English"), state="readonly", width=10); self.cmbIdioma.current(0); self.cmbIdioma.pack(side="left", padx=5); self.cmbIdioma.bind("<<ComboboxSelected>>", self.cmbIdiomaChange)

        MarcoMultiple = ttk.LabelFrame(MarcoInferior, text="Corridas múltiples", padding=6)
        MarcoMultiple.grid(row=0, column=1, sticky="nsew", padx=2)
        self.btnCorridasMultiples = ttk.Button(MarcoMultiple, command=self.btnCorridasMultiplesClick, style="Action.TButton"); self.btnCorridasMultiples.pack(fill="x", pady=(0, 8))
        # --- Nivel 1 de paralelismo: controles nuevos ---
        self.chkParalelizar = ttk.Checkbutton(MarcoMultiple, text="Paralelizar corridas (Nivel 1)", variable=self.Variables["ParalelizarCorridas"])
        self.chkParalelizar.pack(fill="x", pady=(0, 4))
        MarcoProcesos = ttk.Frame(MarcoMultiple); MarcoProcesos.pack(fill="x", pady=(0, 8))
        ttk.Label(MarcoProcesos, text="Procesos:").pack(side="left")
        ttk.Spinbox(MarcoProcesos, from_=1, to=max(1, os.cpu_count() or 8), textvariable=self.Variables["NumProcesos"], width=5).pack(side="right")
        # --- fin de controles nuevos ---
        Tolerancia = ttk.Frame(MarcoMultiple); Tolerancia.pack(fill="x")
        ttk.Label(Tolerancia, text="Tolerancia\nde inercia:").pack(side="left")
        ttk.Entry(Tolerancia, textvariable=self.Variables["TolInercia"], width=10).pack(side="right")
        self.gProgreso = ttk.Progressbar(MarcoMultiple, mode="determinate"); self.gProgreso.pack(side="bottom", fill="x", pady=(10, 0))

        # El reporte queda debajo de los datos y el panel de control, no debajo de resultados.
        MarcoResumen = ttk.Frame(MarcoInferior); MarcoResumen.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
        self.lblResumen = ttk.Label(MarcoResumen, text="Reporte de corridas múltiples"); self.lblResumen.pack(anchor="w")
        # height=6 porque el reporte ahora tiene 6 conceptos (se agregó "Tiempo de pared (real)");
        # sin esto, la sexta fila queda oculta ya que este Treeview no tiene scrollbar.
        self.ListaResumen = ttk.Treeview(MarcoResumen, show="headings", height=6); self.ListaResumen.pack(fill="x")
        AccionesFinales = ttk.Frame(MarcoResumen); AccionesFinales.pack(fill="x", pady=(8, 0))
        self.tblExportarExcel = ttk.Button(AccionesFinales, command=self.tblExportarExcelClick, width=21)
        self.tblExportarExcel.pack(side="left", padx=(0, 4))
        self.btnLimpiar = ttk.Button(AccionesFinales, command=self.btnLimpiarClick, width=8)
        self.btnLimpiar.pack(side="left")

    def _control_numerico(self, Padre, Etiqueta, Sufijo, Nombre, Fila) -> None:
        ttk.Label(Padre, text=Etiqueta).grid(row=Fila, column=0, sticky="w", pady=3)
        ttk.Label(Padre, text=Sufijo).grid(row=Fila, column=1, sticky="e")
        ttk.Spinbox(Padre, from_=1, to=99999, textvariable=self.Variables[Nombre], width=7).grid(row=Fila, column=2, sticky="e", pady=3)

    @staticmethod
    def _cargar_tabla(tabla: ttk.Treeview, encabezados: list[str], filas: list[list[object]], anchos: list[int] | None = None) -> None:
        tabla.delete(*tabla.get_children())
        tabla["columns"] = list(range(len(encabezados)))
        for i, Encabezado in enumerate(encabezados):
            tabla.heading(i, text=Encabezado)
            tabla.column(i, width=(anchos[i] if anchos else 100), anchor="center", stretch=False)
        for Fila in filas:
            tabla.insert("", "end", values=[str(x) for x in Fila])

    def Parametros(self) -> dict:
        return {Nombre: Variable.get() for Nombre, Variable in self.Variables.items()}

    def cmdCargarDatosClick(self) -> None:
        FileName = filedialog.askopenfilename(filetypes=[("Datos", "*.xlsx *.csv"), ("Todos", "*.*")])
        if not FileName:
            return
        try:
            Ruta = Path(FileName)
            if Ruta.suffix.lower() == ".csv":
                with Ruta.open(newline="", encoding="utf-8-sig") as Archivo:
                    Datos = [[float(x.replace(",", ".")) for x in Fila] for Fila in csv.reader(Archivo) if Fila]
            elif Ruta.suffix.lower() == ".xlsx":
                from openpyxl import load_workbook
                Hoja = load_workbook(Ruta, read_only=True, data_only=True).active
                Datos = [[float(x) for x in Fila] for Fila in Hoja.iter_rows(values_only=True) if any(x is not None for x in Fila)]
            else:
                raise ValueError("Solo se admiten archivos CSV o XLSX.")
            if not Datos or any(len(Fila) != len(Datos[0]) for Fila in Datos):
                raise ValueError("La tabla debe ser rectangular y no estar vacía.")
            self.TablaDatos, self.NombreTabla = Datos, Ruta.name
            Declaraciones.PoblacionOriginaldeIndi = [Fila.copy() for Fila in Datos]
            Declaraciones.M, Declaraciones.N = len(Datos), len(Datos[0])
            Declaraciones.MatrizDeAcotaciones = [[min(Fila[j] for Fila in Datos) for j in range(Declaraciones.N)], [max(Fila[j] for Fila in Datos) for j in range(Declaraciones.N)]]
            self._cargar_tabla(self.TablaCargarDatos, [f"Var {i}" for i in range(1, Declaraciones.N + 1)], Datos)
            self.master.title(f"Optimización basada en colonias de hormigas - {Ruta.name}")
        except Exception as Error:
            messagebox.showerror("Error al cargar datos", str(Error))

    def _ejecutar_una_corrida(self) -> tuple[float, list[int], float]:
        InicializarVariables(self.Parametros())
        Inicio = perf_counter()
        Declaraciones.Colonia = Declaraciones.clsColonia(Declaraciones.CantiHormigas)
        EjecutarAlgoritomoDeHormigas()
        Tiempo = (perf_counter() - Inicio) * 1_000_000
        return (Declaraciones.Colonia.MejorInerciaDeLaHistoria, Declaraciones.Colonia.MejorClasificacionDeLaHistoria.copy(), Tiempo)

    @staticmethod
    def FormatearTiempo(Microsegundos: float) -> str:
        """Formato 0 XXX XXX usado para tiempo en pantalla y exportación."""
        Texto = f"{max(0, round(Microsegundos)):07d}"
        return f"{Texto[:-6]} {Texto[-6:-3]} {Texto[-3:]}"

    def _verificar_no_combinar_niveles(self) -> None:
        """Nivel 1 (procesos por corrida) y Nivel 2 (procesos por hormiga) no se
        pueden combinar todavía: anidar un Pool dentro de un proceso hijo choca
        con la restricción de multiprocessing de que un proceso daemónico no
        puede tener hijos propios. Se deja para una futura iteración del proyecto."""
        if self.Variables["ParalelizarCorridas"].get() and self.Variables["ParalelizarHormigas"].get():
            raise ValueError(
                "Nivel 1 y Nivel 2 no se pueden activar al mismo tiempo todavía "
                "(un Pool no puede crear otro Pool anidado dentro de sus procesos). "
                "Desactive uno de los dos checkboxes de paralelismo."
            )

    def btnCorridaUnicaClick(self) -> None:
        try:
            self._verificar_no_combinar_niveles()
            if self.Variables["ParalelizarHormigas"].get():
                if not self.TablaDatos:
                    raise ValueError("Primero cargue una tabla de datos.")
                NumProcesos = int(self.Variables["NumProcesosNivel2"].get())
                Inercia, Clasificacion, Tiempo = ejecutar_corrida_nivel2(
                    self.Parametros(), self.TablaDatos, Declaraciones.MatrizDeAcotaciones,
                    NumProcesos, self._obtener_semilla_nivel2(),
                )
            else:
                Inercia, Clasificacion, Tiempo = self._ejecutar_una_corrida()
            Declaraciones.MejorInerciaDeLaHistoriaGlobal, Declaraciones.MejorClasificacionDeLaHistoriaGlobal = Inercia, Clasificacion
            self._cargar_tabla(self.ListaResultados, [T2("Corrida", "Run"), T2("Valor de inercia", "Inertia value"), T2("Tiempo (µs)", "Time (µs)")], [[T2("Única", "Single"), Inercia, self.FormatearTiempo(Tiempo)]], [55, 140, 75])
        except Exception as Error:
            messagebox.showerror("Error", str(Error))

    # --- Nivel 1 de paralelismo: dos caminos separados que alimentan el mismo reporte ---
    def _corridas_multiples_secuencial(self, Numero: int) -> list[tuple[float, list[int], float]]:
        Resultados = []
        self.gProgreso.configure(mode="determinate", maximum=Numero, value=0)
        for i in range(1, Numero + 1):
            Resultados.append(self._ejecutar_una_corrida())
            self.gProgreso.configure(value=i); self.update_idletasks()
        return Resultados

    def _corridas_multiples_paralelo(self, Numero: int) -> list[tuple[float, list[int], float]]:
        if not self.TablaDatos:
            raise ValueError("Primero cargue una tabla de datos.")
        self.gProgreso.configure(mode="indeterminate"); self.gProgreso.start(10); self.update_idletasks()
        try:
            NumProcesos = int(self.Variables["NumProcesos"].get())
            Resultados = ejecutar_corridas_multiples_paralelo(
                self.Parametros(), self.TablaDatos, Declaraciones.MatrizDeAcotaciones, Numero, NumProcesos,
            )
        finally:
            self.gProgreso.stop(); self.gProgreso.configure(mode="determinate", value=Numero)
        return Resultados

    # --- Nivel 2 de paralelismo aplicado a "Corridas múltiples" ---
    # Cada una de las Numero corridas usa internamente el Nivel 2 (hormigas
    # repartidas entre procesos), pero las corridas en sí se hacen una por una,
    # en el proceso principal -- por eso la barra de progreso SÍ puede avanzar
    # corrida por corrida, a diferencia del Nivel 1 donde todas corren a la vez.
    def _corridas_multiples_nivel2(self, Numero: int) -> list[tuple[float, list[int], float]]:
        if not self.TablaDatos:
            raise ValueError("Primero cargue una tabla de datos.")
        NumProcesos = int(self.Variables["NumProcesosNivel2"].get())
        SemillaBase = self._obtener_semilla_nivel2()
        Resultados = []
        self.gProgreso.configure(mode="determinate", maximum=Numero, value=0)
        for i in range(1, Numero + 1):
            Semilla = (SemillaBase + i) if SemillaBase is not None else None
            Resultados.append(ejecutar_corrida_nivel2(
                self.Parametros(), self.TablaDatos, Declaraciones.MatrizDeAcotaciones, NumProcesos, Semilla,
            ))
            self.gProgreso.configure(value=i); self.update_idletasks()
        return Resultados

    def btnCorridasMultiplesClick(self) -> None:
        try:
            self._verificar_no_combinar_niveles()
            Numero = int(self.Variables["CantidadDeCorridasMultiplesGeneral"].get())
            if Numero < 1: raise ValueError("El número de corridas debe ser mayor que cero.")

            # Tiempo de pared: lo que realmente transcurre desde que se pide el lote
            # hasta que se tienen todos los resultados. A diferencia de sum(Tiempos),
            # esto SÍ refleja el beneficio (o la falta de beneficio) del paralelismo,
            # porque en modo paralelo varias corridas avanzan al mismo tiempo.
            InicioPared = perf_counter()
            if self.Variables["ParalelizarHormigas"].get():
                Resultados = self._corridas_multiples_nivel2(Numero)
            elif self.Variables["ParalelizarCorridas"].get():
                Resultados = self._corridas_multiples_paralelo(Numero)
            else:
                Resultados = self._corridas_multiples_secuencial(Numero)
            TiempoDeParedTotal = (perf_counter() - InicioPared) * 1_000_000

            Filas = [[i + 1, Inercia, self.FormatearTiempo(Tiempo)] for i, (Inercia, _Clasif, Tiempo) in enumerate(Resultados)]
            Tiempos = [Tiempo for _, _, Tiempo in Resultados]
            MejorInercia, MejorClasificacion, _ = min(Resultados, key=lambda R: R[0])

            Declaraciones.MejorInerciaDeLaHistoriaGlobal, Declaraciones.MejorClasificacionDeLaHistoriaGlobal = MejorInercia, MejorClasificacion
            Tolerancia = float(self.Variables["TolInercia"].get())
            Frecuencia = sum(abs(Inercia - MejorInercia) < Tolerancia for Inercia, _, _ in Resultados)
            self._cargar_tabla(self.ListaResultados, [T2("Corrida", "Run"), T2("Valor de inercia", "Inertia value"), T2("Tiempo (µs)", "Time (µs)")], Filas, [55, 140, 75])
            self._cargar_tabla(self.ListaResumen, [T2("Concepto", "Item"), T2("Valor", "Value")], [
                [T2("Mejor inercia", "Best inertia"), MejorInercia],
                [T2("Número de apariciones", "Occurrence count"), f"{Frecuencia} {T2('de', 'of')} {Numero}"],
                [T2("Porcentaje de atracción", "Attraction rate"), f"{100 * Frecuencia / Numero:.2f}%"],
                [T2("Tiempo promedio por corrida", "Average time per run"), self.FormatearTiempo(sum(Tiempos) / Numero)],
                [T2("Suma de tiempos (CPU)", "Sum of times (CPU)"), self.FormatearTiempo(sum(Tiempos))],
                [T2("Tiempo de pared (real)", "Wall-clock time (real)"), self.FormatearTiempo(TiempoDeParedTotal)],
            ], [180, 130])
        except Exception as Error:
            messagebox.showerror("Error", str(Error))

    def tblExportarExcelClick(self) -> None:
        if not self.TablaDatos:
            messagebox.showwarning("Sin datos", "Primero cargue y ejecute una tabla."); return
        Nombre = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not Nombre: return
        try:
            from openpyxl import Workbook
            Libro = Workbook(); Hoja = Libro.active; Hoja.title = "Datos Originales"
            Hoja.append([f"Var {i}" for i in range(1, Declaraciones.N + 1)])
            for Fila in self.TablaDatos: Hoja.append(Fila)
            for NombreHoja, Tabla in [("Corridas", self.ListaResultados), ("Resumen", self.ListaResumen)]:
                H = Libro.create_sheet(NombreHoja); H.append([Tabla.heading(C)["text"] for C in Tabla["columns"]])
                for Item in Tabla.get_children(): H.append(list(Tabla.item(Item)["values"]))
            H = Libro.create_sheet("Clasificación")
            H.append(["Individuo", "Clase asignada"])
            for i, Clase in enumerate(Declaraciones.MejorClasificacionDeLaHistoriaGlobal, 1): H.append([i, Clase])
            Libro.save(Nombre); messagebox.showinfo("Información", f"Excel generado: {Nombre}")
        except Exception as Error: messagebox.showerror("Error al exportar", str(Error))

    def btnLimpiarClick(self) -> None:
        self._cargar_tabla(self.ListaResultados, [], []); self._cargar_tabla(self.ListaResumen, [], [])

    def cmbIdiomaChange(self, _Evento=None) -> None:
        Declaraciones.CurrentLang = TLang.lgES if self.cmbIdioma.current() == 0 else TLang.lgEN
        self.ApplyLanguage()

    def _traducir_controles(self, Control) -> None:
        """Traduce etiquetas estáticas de la interfaz sin alterar los valores del usuario."""
        Textos = {
            "Tabla de datos originales": "Original data table",
            "Panel de control": "Control panel",
            "Estrategia de k-medias": "k-means strategy",
            "Usar esta estrategia": "Use this strategy",
            "Aplicar estrategia cada": "Apply strategy every",
            "iteraciones": "iterations",
            "Parámetros de entrada": "Input parameters",
            "Número de clases": "Number of clusters",
            "Cantidad de hormigas": "Number of ants",
            "Parámetros adicionales:": "Additional parameters:",
            "Número de corridas múltiples": "Number of multiple runs",
            "Iteraciones sin mejora\nantes de detenerse:": "Iterations without improvement\nbefore stopping:",
            "Inercia intraclase y tiempo por corrida": "Within-cluster inertia and runtime per run",
            "Corridas múltiples": "Multiple runs",
            "Paralelizar corridas (Nivel 1)": "Parallelize runs (Level 1)",
            "Paralelizar hormigas (Nivel 2)": "Parallelize ants (Level 2)",
            "Procesos:": "Processes:",
            "Tolerancia\nde inercia:": "Inertia\ntolerance:",
            "Reporte de corridas múltiples": "Multiple-run report",
            "Idioma:": "Language:",
        }
        Inversos = {EN: ES for ES, EN in Textos.items()}
        Mapa = Textos if Declaraciones.CurrentLang == TLang.lgEN else Inversos
        try:
            Texto = Control.cget("text")
            if Texto in Mapa:
                Control.configure(text=Mapa[Texto])
        except tk.TclError:
            pass
        for Hijo in Control.winfo_children():
            self._traducir_controles(Hijo)

    def ApplyLanguage(self) -> None:
        self.master.title(T2("Optimización basada en colonias de hormigas", "Ant colony optimization"))
        self.cmdCargarDatos.configure(text=T2("Cargar datos", "Load data")); self.btnCorridaUnica.configure(text=T2("Corrida única", "Single run"))
        self.btnCorridasMultiples.configure(text=T2("Corridas múltiples", "Multiple runs")); self.btnOptimizacion.configure(text=T2("Realizar optimización", "Perform optimization"))
        self.tblExportarExcel.configure(text=T2("Exportar resultados a Excel", "Export results to Excel")); self.btnLimpiar.configure(text=T2("Limpiar", "Clear"))
        self._traducir_controles(self)


    def _obtener_semilla_nivel2(self) -> "int | None":
        """Campo vacío = None (no reproducible, random.seed() sin argumento).
        Un valor inválido (no numérico) también se trata como 'sin semilla'
        en vez de tronar la corrida por un typo."""
        Texto = self.Variables["SemillaNivel2"].get().strip()
        if not Texto:
            return None
        try:
            return int(Texto)
        except ValueError:
            raise ValueError(f"La semilla debe ser un número entero, no '{Texto}'.")

    def btnOptimizacionClick(self) -> None:
        from FrmOptimizacion import TForm2
        TForm2(self)

    