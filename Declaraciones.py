"""Equivalente de Declaraciones.pas.

Los nombres de datos y clases se preservan deliberadamente para que el código se pueda
contrastar línea a línea con la implementación Delphi.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from math import inf
import random
from typing import List

VectorIR = List[float]
VectorINT = List[int]
MatrizIR = List[VectorIR]
MatrizINT = List[VectorINT]


class TLang(Enum):
    lgES = "es"
    lgEN = "en"


MinFero = 0.000001
MinBase = 0.000001

# Variables globales homónimas a Declaraciones.pas.
PoblacionOriginaldeIndi: MatrizIR = []
M = N = R = 0
MatrizDeAcotaciones: MatrizIR = []
Alpha = 1.0
Beta = 1.0
Rho = 0.5
Q = 1.0
CantiHormigas = 10
Colonia: "clsColonia | None" = None
Matriz_FeromonaIndi_CG: MatrizIR = []
Matriz_FeromonaAux: MatrizIR = []
MaxIteraSinMejora = 20
K_Medias_Cada = 5
MejoraKMediasActiva = False
CantidadDeCorridasMultiplesGeneral = 10
MejorInerciaDeLaHistoriaGlobal = inf
MejorClasificacionDeLaHistoriaGlobal: VectorINT = []
CurrentLang = TLang.lgES
HiperMatrizDeOptimizacion = []


def T2(ES: str, EN: str) -> str:
    return ES if CurrentLang == TLang.lgES else EN


@dataclass
class clsHormiga:
    ListaDeNodosAClasificar: VectorINT = field(default_factory=list)
    MatrizCG: MatrizIR = field(default_factory=list)
    VCardinalidades: VectorINT = field(default_factory=list)
    VClasificacion: VectorINT = field(default_factory=list)
    ValorDeLaInerciaActual: float = inf

    def DistanciaAlCudrado(self, k_Individuo: int, k_CG: int) -> float:
        """Mantiene la ortografía del método Delphi y sus índices basados en 1."""
        return sum(
            (PoblacionOriginaldeIndi[k_Individuo - 1][i] - self.MatrizCG[k_CG - 1][i]) ** 2
            for i in range(N)
        )

    def IniciarCG(self) -> None:
        self.MatrizCG = [
            [random.uniform(MatrizDeAcotaciones[0][j], MatrizDeAcotaciones[1][j]) for j in range(N)]
            for _ in range(R)
        ]
        self.ListaDeNodosAClasificar = list(range(1, M + 1))
        self.VCardinalidades = [0] * R
        self.VClasificacion = [0] * M
        self.ValorDeLaInerciaActual = inf

    def CamineYClasifique(self, NumeroNodosPorClasificar: int) -> None:
        AuxINT2 = random.randrange(NumeroNodosPorClasificar)
        NumDeNodo = self.ListaDeNodosAClasificar[AuxINT2]
        self.ListaDeNodosAClasificar[AuxINT2], self.ListaDeNodosAClasificar[NumeroNodosPorClasificar - 1] = (
            self.ListaDeNodosAClasificar[NumeroNodosPorClasificar - 1],
            self.ListaDeNodosAClasificar[AuxINT2],
        )

        Pesos = []
        for i in range(1, R + 1):
            VarAux = self.DistanciaAlCudrado(NumDeNodo, i) + MinBase
            Pesos.append((Matriz_FeromonaIndi_CG[NumDeNodo - 1][i - 1] + MinFero) ** Alpha * VarAux ** (-Beta))
        Suma = sum(Pesos)
        # La guarda evita una selección inválida si parámetros extremos provocan overflow.
        if not Suma or Suma == inf:
            ClsAsignada = random.randrange(1, R + 1)
        else:
            RndAux, Acumulado = random.random(), 0.0
            ClsAsignada = R
            for i, Peso in enumerate(Pesos, start=1):
                Acumulado += Peso / Suma
                if RndAux <= Acumulado:
                    ClsAsignada = i
                    break

        Distancia = self.DistanciaAlCudrado(NumDeNodo, ClsAsignada)
        Matriz_FeromonaAux[NumDeNodo - 1][ClsAsignada - 1] += Q / (Distancia + MinBase)
        CarCl = self.VCardinalidades[ClsAsignada - 1]
        if CarCl == 0:
            self.MatrizCG[ClsAsignada - 1] = PoblacionOriginaldeIndi[NumDeNodo - 1].copy()
        else:
            self.MatrizCG[ClsAsignada - 1] = [
                (CarCl * self.MatrizCG[ClsAsignada - 1][i] + PoblacionOriginaldeIndi[NumDeNodo - 1][i]) / (CarCl + 1)
                for i in range(N)
            ]
        self.VCardinalidades[ClsAsignada - 1] += 1
        self.VClasificacion[NumDeNodo - 1] = ClsAsignada

    def Clon(self) -> "clsHormiga":
        return deepcopy(self)

    def DeterminarVClasificacionYInercia(self) -> None:
        self.VClasificacion = [0] * M
        self.VCardinalidades = [0] * R
        suma1 = 0.0
        for i in range(1, M + 1):
            Distancias = [self.DistanciaAlCudrado(i, j) for j in range(1, R + 1)]
            Distancia = min(Distancias)
            Clase = Distancias.index(Distancia) + 1
            self.VClasificacion[i - 1] = Clase
            self.VCardinalidades[Clase - 1] += 1
            suma1 += Distancia
        self.ValorDeLaInerciaActual = suma1 / M if M else inf

    def CalcularCG_dada_Clasificacion(self) -> None:
        # Las clases vacías conservan el centro anterior para impedir división por cero.
        Anterior = deepcopy(self.MatrizCG)
        self.MatrizCG = [[0.0] * N for _ in range(R)]
        for i, ClsIndi in enumerate(self.VClasificacion):
            for j in range(N):
                self.MatrizCG[ClsIndi - 1][j] += PoblacionOriginaldeIndi[i][j]
        for i in range(R):
            if self.VCardinalidades[i]:
                self.MatrizCG[i] = [x / self.VCardinalidades[i] for x in self.MatrizCG[i]]
            elif Anterior:
                self.MatrizCG[i] = Anterior[i]

    def CalcularInercia_dados_CG_y_clasificacion(self) -> None:
        self.ValorDeLaInerciaActual = sum(
            self.DistanciaAlCudrado(i, Clase) for i, Clase in enumerate(self.VClasificacion, start=1)
        ) / M if M else inf

    def Intesificar_Rastro_Feromona(self) -> None:
        if self.ValorDeLaInerciaActual <= 0 or self.ValorDeLaInerciaActual == inf:
            return
        for i, Clase in enumerate(self.VClasificacion):
            Matriz_FeromonaIndi_CG[i][Clase - 1] = Q / self.ValorDeLaInerciaActual

    def Haga_K_Medias(self) -> None:
        self.DeterminarVClasificacionYInercia()
        self.CalcularCG_dada_Clasificacion()
        self.DeterminarVClasificacionYInercia()

    def AplicarK_MediasCompleto(self) -> None:
        InerciaAnterior = inf
        while abs(InerciaAnterior - self.ValorDeLaInerciaActual) > 0.001:
            InerciaAnterior = self.ValorDeLaInerciaActual
            self.DeterminarVClasificacionYInercia()
            self.CalcularCG_dada_Clasificacion()
        self.DeterminarVClasificacionYInercia()


class clsColonia:
    def __init__(self, NumHormigas: int):
        self.Cantidad_de_Hormiga = NumHormigas
        self.VectorDeHormigas = [clsHormiga() for _ in range(NumHormigas)]
        for Hormiga in self.VectorDeHormigas:
            Hormiga.IniciarCG()
        self.MejorInerciaDeLaHistoria = inf
        self.MejorClasificacionDeLaHistoria: VectorINT = []

    def Actualizar_el_rastro_de_la_feromona(self) -> None:
        for i in range(M):
            for j in range(R):
                Matriz_FeromonaIndi_CG[i][j] = (1 - Rho) * Matriz_FeromonaIndi_CG[i][j] + Rho * Matriz_FeromonaAux[i][j]

    def ContruirClasificacion(self) -> None:
        global Matriz_FeromonaAux
        Matriz_FeromonaAux = [[0.0] * R for _ in range(M)]
        for i in range(M):
            for Hormiga in self.VectorDeHormigas:
                Hormiga.CamineYClasifique(M - i)
        MejorHormiga = min(self.VectorDeHormigas, key=lambda Hormiga: (Hormiga.CalcularInercia_dados_CG_y_clasificacion() or Hormiga.ValorDeLaInerciaActual))
        for Hormiga in self.VectorDeHormigas:
            Hormiga.VCardinalidades = [0] * R
        self.Actualizar_el_rastro_de_la_feromona()
        if MejorHormiga.ValorDeLaInerciaActual < self.MejorInerciaDeLaHistoria:
            self.MejorInerciaDeLaHistoria = MejorHormiga.ValorDeLaInerciaActual
            self.MejorClasificacionDeLaHistoria = MejorHormiga.VClasificacion.copy()
        self.IntesificarRastroDeFeromonaDelaMejorSolucion()

    def IntesificarRastroDeFeromonaDelaMejorSolucion(self) -> None:
        if not self.MejorClasificacionDeLaHistoria or self.MejorInerciaDeLaHistoria <= 0:
            return
        for i, Clase in enumerate(self.MejorClasificacionDeLaHistoria):
            Matriz_FeromonaIndi_CG[i][Clase - 1] = Q / self.MejorInerciaDeLaHistoria
