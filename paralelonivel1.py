"""Nivel 1 de paralelismo: corridas independientes en procesos separados.

Cada corrida (crear una Colonia nueva + correr EjecutarAlgoritomoDeHormigas
hasta converger) es completamente independiente de las demás: no comparten
feromona, centroides ni generador aleatorio. Por eso se pueden repartir en un
Pool de procesos sin necesitar locks ni sincronización -- es paralelismo a
nivel de "corrida completa", no a nivel de hormiga.

Los procesos hijos no heredan el estado del módulo Declaraciones de forma
confiable (en Windows/macOS, multiprocessing usa 'spawn' y arranca un
intérprete nuevo desde cero). Por eso cada worker recibe explícitamente todo
lo que necesita como argumento y reconstruye el estado global él mismo --
esto también funciona igual de bien con 'fork' en Linux, así que es la forma
más portable de hacerlo.
"""
from __future__ import annotations

import os
import random
from multiprocessing import Pool
from time import perf_counter
from typing import Optional

import Declaraciones
from Funciones_y_Procedimientos import EjecutarAlgoritomoDeHormigas, InicializarVariables

# Un resultado de corrida: (mejor inercia, mejor clasificación, tiempo en microsegundos)
ResultadoCorrida = tuple[float, list[int], float]


def _ejecutar_una_corrida_worker(
    args: tuple[dict, list[list[float]], list[list[float]], int]
) -> ResultadoCorrida:
    """Se ejecuta DENTRO de un proceso hijo. No se llama directamente."""
    Parametros, Poblacion, Acotaciones, Semilla = args

    # Semilla única por corrida: sin esto, procesos creados casi al mismo tiempo
    # pueden terminar con el generador aleatorio en el mismo estado y dejar de
    # ser corridas realmente independientes.
    random.seed(Semilla + os.getpid())

    # Reconstruir en este proceso lo que normalmente deja listo cmdCargarDatosClick.
    # No dependemos de que el proceso haya heredado el estado del padre -- lo
    # armamos aquí desde los argumentos recibidos, para que funcione igual
    # con fork o con spawn.
    Declaraciones.PoblacionOriginaldeIndi = [Fila.copy() for Fila in Poblacion]
    Declaraciones.M = len(Poblacion)
    Declaraciones.N = len(Poblacion[0]) if Poblacion else 0
    Declaraciones.MatrizDeAcotaciones = Acotaciones

    InicializarVariables(Parametros)
    Inicio = perf_counter()
    # Esta Colonia, su feromona y sus centroides viven SOLO en este proceso --
    # ninguna otra corrida los ve ni los modifica.
    Declaraciones.Colonia = Declaraciones.clsColonia(Declaraciones.CantiHormigas)
    EjecutarAlgoritomoDeHormigas()
    Tiempo = (perf_counter() - Inicio) * 1_000_000

    return (
        Declaraciones.Colonia.MejorInerciaDeLaHistoria,
        Declaraciones.Colonia.MejorClasificacionDeLaHistoria.copy(),
        Tiempo,
    )


def ejecutar_corridas_multiples_paralelo(
    Parametros: dict,
    Poblacion: list[list[float]],
    Acotaciones: list[list[float]],
    NumeroCorridas: int,
    NumProcesos: Optional[int] = None,
) -> list[ResultadoCorrida]:
    """Lanza NumeroCorridas corridas independientes repartidas en procesos separados.

    NumProcesos=None deja que multiprocessing use os.cpu_count().
    El orden de los resultados coincide con el orden de las corridas (pool.map
    preserva el orden aunque los procesos terminen en orden distinto).
    """
    # Cada tarea lleva todo lo que su worker necesita -- los parámetros y los
    # datos se repiten en cada tupla (se copian al enviarse al proceso), y el
    # índice i funciona como semilla base de esa corrida en particular.
    Tareas = [(Parametros, Poblacion, Acotaciones, i) for i in range(NumeroCorridas)]
    with Pool(processes=NumProcesos) as pool:
        # pool.map crea los NumProcesos (o los que se le pidan) y reparte las
        # NumeroCorridas tareas entre ellos; bloquea hasta que todas terminan.
        Resultados = pool.map(_ejecutar_una_corrida_worker, Tareas)
    return Resultados