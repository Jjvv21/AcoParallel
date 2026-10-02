"""Equivalente de Funciones_y_Procedimientos.pas."""
from __future__ import annotations

from math import inf
import random
import Declaraciones


def GenerarCGAleatorio() -> Declaraciones.VectorIR:
    return [
        random.uniform(Declaraciones.MatrizDeAcotaciones[0][j], Declaraciones.MatrizDeAcotaciones[1][j])
        for j in range(Declaraciones.N)
    ]


def InicializarVariables(Parametros: dict) -> None:
    """Actualiza las variables globales con los controles de la ventana principal."""
    for Nombre in ("R", "CantiHormigas", "MaxIteraSinMejora", "K_Medias_Cada", "CantidadDeCorridasMultiplesGeneral"):
        setattr(Declaraciones, Nombre, int(Parametros[Nombre]))
    for Nombre in ("Alpha", "Beta", "Rho", "Q"):
        setattr(Declaraciones, Nombre, float(Parametros[Nombre]))
    Declaraciones.MejoraKMediasActiva = bool(Parametros["MejoraKMediasActiva"])
    if Declaraciones.R < 1 or Declaraciones.CantiHormigas < 1:
        raise ValueError("R y CantiHormigas deben ser mayores que cero.")
    if not Declaraciones.PoblacionOriginaldeIndi:
        raise ValueError("Primero cargue una tabla de datos.")
    Declaraciones.Matriz_FeromonaIndi_CG = [[0.0] * Declaraciones.R for _ in range(Declaraciones.M)]


def InicializarVariablesEnOptimizacion(Parametros: dict) -> None:
    """Se conserva por compatibilidad: en Python recibe el mismo diccionario."""
    InicializarVariables(Parametros)


def EjecutarAlgoritomoDeHormigas() -> None:
    """Ejecuta el ciclo de convergencia sobre la Colonia ya creada."""
    if Declaraciones.Colonia is None:
        raise RuntimeError("La Colonia debe crearse antes de ejecutar el algoritmo.")
    IteraSinMejoras = 0
    InerciaAux = inf
    contador = 0
    while IteraSinMejoras < Declaraciones.MaxIteraSinMejora:
        contador += 1
        Declaraciones.Colonia.ContruirClasificacion()
        IteraSinMejoras += 1
        if Declaraciones.Colonia.MejorInerciaDeLaHistoria < InerciaAux:
            InerciaAux = Declaraciones.Colonia.MejorInerciaDeLaHistoria
            IteraSinMejoras = 0
        if Declaraciones.MejoraKMediasActiva and Declaraciones.K_Medias_Cada > 0 and contador % Declaraciones.K_Medias_Cada == 0:
            for Hormiga in Declaraciones.Colonia.VectorDeHormigas:
                Hormiga.AplicarK_MediasCompleto()
                if Hormiga.ValorDeLaInerciaActual < Declaraciones.Colonia.MejorInerciaDeLaHistoria:
                    Declaraciones.Colonia.MejorInerciaDeLaHistoria = Hormiga.ValorDeLaInerciaActual
                    Declaraciones.Colonia.MejorClasificacionDeLaHistoria = Hormiga.VClasificacion.copy()
