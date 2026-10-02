"""Ventana de optimización, equivalente funcional de FrmOptimizacion.pas."""
from __future__ import annotations

from itertools import product
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class TForm2(tk.Toplevel):
    def __init__(self, Form1):
        super().__init__(Form1)
        self.Form1 = Form1
        self.title("Parameter optimization")
        self.geometry("950x640")
        self.minsize(950, 640)
        self.Config, self.TodasLasConfiguraciones = {}, []
        ttk.Style().configure("Optimization.TButton", padding=(8, 14))
        self._crear_controles()

    def _crear_controles(self):
        Marco = ttk.Frame(self, padding=7); Marco.pack(fill="both", expand=True)
        Marco.columnconfigure(0, minsize=250); Marco.columnconfigure(1, weight=1); Marco.rowconfigure(0, weight=1)
        self.grpPanel = ttk.LabelFrame(Marco, text="Control panel", padding=7)
        self.grpPanel.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        for Fila, Datos in enumerate((("Alpha", "Alpha parameter optimization", "1", "5", "4"), ("Beta", "Beta parameter optimization", "1", "5", "4"), ("Rho", "Rho parameter optimization", "0.2", "0.8", "6"), ("Q", "Q parameter optimization", "50", "500", "9"))):
            self._crear_parametro(*Datos, Fila)
        self._crear_inercia()
        self.btnEjecutarOptimizacion = ttk.Button(self.grpPanel, text="Start parameter optimization", style="Optimization.TButton", command=self.btnEjecutarOptimizacionClick)
        self.btnEjecutarOptimizacion.grid(row=5, column=0, sticky="ew", pady=(10, 12))
        self.gProgreso2 = ttk.Progressbar(self.grpPanel, mode="determinate"); self.gProgreso2.grid(row=6, column=0, sticky="ew")
        self.lblProgreso = ttk.Label(self.grpPanel, text="0%", anchor="center"); self.lblProgreso.grid(row=7, column=0, sticky="ew", pady=(3, 0))

        Derecho = ttk.Frame(Marco); Derecho.grid(row=0, column=1, sticky="nsew")
        Derecho.columnconfigure(0, weight=1); Derecho.rowconfigure(1, weight=1)
        Filtro = ttk.Frame(Derecho); Filtro.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(Filtro, text="Attraction filter:").pack(side="left")
        self.scrlbrFiltro = tk.IntVar(value=0)
        ttk.Scale(Filtro, from_=0, to=100, variable=self.scrlbrFiltro, command=self.scrlbrFiltroChange).pack(side="left", fill="x", expand=True, padx=8)
        self.edtValorDelFiltro = tk.StringVar(value="0%")
        ttk.Entry(Filtro, textvariable=self.edtValorDelFiltro, width=11, state="readonly").pack(side="right")
        self.ListaResultados = ttk.Treeview(Derecho, columns=("atraccion", "Alpha", "Beta", "Rho", "Q"), show="headings", height=23)
        for Columna, Encabezado in zip(self.ListaResultados["columns"], ("Attraction rate", "Alpha", "Beta", "Rho", "Q")):
            self.ListaResultados.heading(Columna, text=Encabezado); self.ListaResultados.column(Columna, width=125, anchor="center")
        Barra = ttk.Scrollbar(Derecho, orient="vertical", command=self.ListaResultados.yview)
        self.ListaResultados.configure(yscrollcommand=Barra.set)
        self.ListaResultados.grid(row=1, column=0, sticky="nsew"); Barra.grid(row=1, column=1, sticky="ns")
        Acciones = ttk.Frame(Derecho); Acciones.grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Button(Acciones, text="Export to text", width=18, command=self.btnExportarTextoClick).pack(side="left", padx=(0, 8))
        ttk.Button(Acciones, text="Export all tables", width=20, command=self.btnExportarTablasClick).pack(side="left")

    def _crear_parametro(self, Nombre, Titulo, Minimo, Maximo, Particiones, Fila):
        Grupo = ttk.LabelFrame(self.grpPanel, text=Titulo, padding=6); Grupo.grid(row=Fila, column=0, sticky="ew", pady=(0, 6))
        Activar = tk.BooleanVar(value=False); Valores = [tk.StringVar(value=X) for X in (Minimo, Maximo, Particiones)]
        self.Config[Nombre] = (Activar, Valores)
        ttk.Checkbutton(Grupo, text="Optimize this parameter", variable=Activar).grid(row=0, column=0, columnspan=3, sticky="w")
        for Columna, (Etiqueta, Valor) in enumerate(zip(("Minimum", "Maximum", "Partitions"), Valores)):
            ttk.Label(Grupo, text=Etiqueta).grid(row=1, column=Columna, sticky="w")
            ttk.Entry(Grupo, textvariable=Valor, width=9).grid(row=2, column=Columna, padx=(0, 5), sticky="w")

    def _crear_inercia(self):
        self.grpInercia = ttk.LabelFrame(self.grpPanel, text="Manual entry of optimal inertia", padding=7); self.grpInercia.grid(row=4, column=0, sticky="ew", pady=(7, 0))
        self.chkIngresoInerciaManual = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.grpInercia, text="Manually enter optimal inertia", variable=self.chkIngresoInerciaManual, command=self.chkIngresoInerciaManualClick).grid(row=0, column=0, columnspan=2, sticky="w")
        self.edtInerciaOptimaConocida, self.edtTolInerciaOptima = tk.StringVar(value="0"), tk.StringVar(value="0.00001")
        ttk.Label(self.grpInercia, text="Known optimal inertia").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.entradaInercia = ttk.Entry(self.grpInercia, textvariable=self.edtInerciaOptimaConocida, width=17); self.entradaInercia.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Label(self.grpInercia, text="Inertia tolerance").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.entradaTolerancia = ttk.Entry(self.grpInercia, textvariable=self.edtTolInerciaOptima, width=17); self.entradaTolerancia.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.chkIngresoInerciaManualClick()

    def _valores(self, Nombre):
        Activar, (Minimo, Maximo, Particiones) = self.Config[Nombre]
        if not Activar.get(): return [float(self.Form1.Variables[Nombre].get())]
        Inicio, Fin, N = float(Minimo.get()), float(Maximo.get()), int(Particiones.get())
        if N < 1: raise ValueError(f"Partitions for {Nombre} must be greater than zero.")
        return [Inicio + i * (Fin - Inicio) / N for i in range(N + 1)]

    def chkIngresoInerciaManualClick(self):
        Estado = "normal" if self.chkIngresoInerciaManual.get() else "disabled"
        self.entradaInercia.configure(state=Estado); self.entradaTolerancia.configure(state=Estado)

    def scrlbrFiltroChange(self, _Valor=None):
        Limite = int(float(self.scrlbrFiltro.get())) / 100; self.edtValorDelFiltro.set(f"{int(float(self.scrlbrFiltro.get()))}%")
        self.ListaResultados.delete(*self.ListaResultados.get_children())
        for Atraccion, Alpha, Beta, Rho, Q in self.TodasLasConfiguraciones:
            if Atraccion >= Limite: self.ListaResultados.insert("", "end", values=(f"{Atraccion:.2%}", Alpha, Beta, Rho, Q))

    def btnEjecutarOptimizacionClick(self):
        try:
            Rejilla = list(product(*(self._valores(Nombre) for Nombre in ("Alpha", "Beta", "Rho", "Q"))))
            Corridas = int(self.Form1.Variables["CantidadDeCorridasMultiplesGeneral"].get())
            if Corridas < 1: raise ValueError("The number of multiple runs must be greater than zero.")
            self.TodasLasConfiguraciones.clear(); self.gProgreso2.configure(maximum=len(Rejilla), value=0)
            for Indice, (Alpha, Beta, Rho, Q) in enumerate(Rejilla, 1):
                Original = {Nombre: self.Form1.Variables[Nombre].get() for Nombre in ("Alpha", "Beta", "Rho", "Q")}
                for Nombre, Valor in zip(("Alpha", "Beta", "Rho", "Q"), (Alpha, Beta, Rho, Q)): self.Form1.Variables[Nombre].set(str(Valor))
                Inercias = [self.Form1._ejecutar_una_corrida()[0] for _ in range(Corridas)]
                for Nombre, Valor in Original.items(): self.Form1.Variables[Nombre].set(Valor)
                Referencia = float(self.edtInerciaOptimaConocida.get()) if self.chkIngresoInerciaManual.get() else min(Inercias)
                Atraccion = sum(abs(X - Referencia) < float(self.edtTolInerciaOptima.get()) for X in Inercias) / Corridas
                self.TodasLasConfiguraciones.append((Atraccion, Alpha, Beta, Rho, Q))
                self.gProgreso2.configure(value=Indice); self.lblProgreso.configure(text=f"{100 * Indice / len(Rejilla):.0f}%"); self.update_idletasks()
            self.scrlbrFiltroChange(); messagebox.showinfo("Information", "Parameter optimization completed.")
        except Exception as Error: messagebox.showerror("Optimization error", str(Error))

    def _guardar_resultados(self, NombreSugerido):
        Destino = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=NombreSugerido, filetypes=[("Text file", "*.txt")])
        if not Destino: return
        Lineas = ["Attraction rate\tAlpha\tBeta\tRho\tQ"]
        for Fila in self.TodasLasConfiguraciones: Lineas.append("\t".join((f"{Fila[0]:.2%}", *(str(X) for X in Fila[1:]))))
        Path(Destino).write_text("\n".join(Lineas), encoding="utf-8")

    def btnExportarTextoClick(self): self._guardar_resultados("parameter_optimization.txt")
    def btnExportarTablasClick(self): self._guardar_resultados("all_parameter_tables.txt")
