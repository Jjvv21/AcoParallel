"""Nivel 2 de paralelismo: las hormigas de UNA colonia se reparten entre procesos
dentro de cada iteración, en vez de recorrerse secuencialmente.

Arquitectura: coordinador-trabajador con estado centralizado. Un proceso
principal reparte las hormigas de la colonia entre N procesos trabajadores en
cada iteración; cada trabajador construye sus soluciones de forma
independiente; el proceso principal agrega los resultados y actualiza la
feromona antes de pasar a la siguiente iteración.

La matriz de feromonas y los acumuladores de cada proceso viven en memoria
compartida (multiprocessing.shared_memory), así que no se vuelven a
serializar en cada iteración -- solo viajan los centroides de cada grupo
(pequeños) y un par de enteros.
"""
from __future__ import annotations

import random
from copy import deepcopy
from math import inf
from multiprocessing import Pool, shared_memory
from time import perf_counter
from typing import Optional

import numpy as np

import Declaraciones
from Funciones_y_Procedimientos import InicializarVariables

ResultadoCorrida = tuple[float, list[int], float]

# Referencias del PROCESO TRABAJADOR a su propia memoria compartida. Cada
# proceso tiene su propia copia de estas variables de módulo -- no se
# comparten entre procesos salvo lo que vive explícitamente en shared_memory.
_shm_pheromone: Optional[shared_memory.SharedMemory] = None
_shm_deltas: list[shared_memory.SharedMemory] = []
_delta_arrays: list[np.ndarray] = []
_base_seed: Optional[int] = None


def _worker_init(
    Poblacion, M, N, R, Alpha, Beta, Q, MinFero, MinBase,
    nombre_shm_feromona: str,
    nombres_shm_deltas: list[str],
    base_seed: Optional[int],
) -> None:
    """Se ejecuta UNA sola vez por proceso, al crear el Pool -- no en cada
    iteración. Deja listo todo lo que el proceso necesita para trabajar sin
    volver a recibirlo después."""
    global _shm_pheromone, _shm_deltas, _delta_arrays, _base_seed

    # Parámetros del algoritmo y la población: se envían una sola vez aquí
    # (vía initargs), no se repiten en cada tarea.
    Declaraciones.PoblacionOriginaldeIndi = Poblacion
    Declaraciones.M, Declaraciones.N, Declaraciones.R = M, N, R
    Declaraciones.Alpha, Declaraciones.Beta, Declaraciones.Q = Alpha, Beta, Q
    Declaraciones.MinFero, Declaraciones.MinBase = MinFero, MinBase

    # Conectarse (sin copiar) al bloque de memoria compartida de la feromona.
    # Declaraciones.Matriz_FeromonaIndi_CG queda apuntando directo a esa
    # memoria: el resto del código la lee como si fuera una lista normal.
    _shm_pheromone = shared_memory.SharedMemory(name=nombre_shm_feromona)
    Declaraciones.Matriz_FeromonaIndi_CG = np.ndarray(
        (M, R), dtype=np.float64, buffer=_shm_pheromone.buf
    )

    # Conectarse a TODOS los bloques de deltas (uno por proceso trabajador),
    # no solo al propio -- así, sin importar qué proceso físico ejecute la
    # tarea del "grupo k", puede escribir en el bloque de deltas que le
    # corresponde a ese grupo.
    _shm_deltas = [shared_memory.SharedMemory(name=n) for n in nombres_shm_deltas]
    _delta_arrays = [
        np.ndarray((M, R), dtype=np.float64, buffer=shm.buf) for shm in _shm_deltas
    ]

    _base_seed = base_seed
    if base_seed is None:
        # Sin semilla: cada proceso arranca con entropía real del SO
        # (comportamiento no reproducible, explícito).
        random.seed()
    # Si SÍ hay semilla, NO sembramos aquí todavía -- se siembra por TAREA
    # dentro de _clasificar_grupo_worker (ver el porqué ahí).


def _clasificar_grupo_worker(args):
    """Corre dentro de un proceso trabajador: recibe los centroides de un
    GRUPO de hormigas (no todas) y hace que cada una recorra sus M pasos de
    clasificación de forma completamente secuencial e independiente de las
    demás hormigas del grupo."""
    ListaDeCentroides, indice_delta, contador = args
    M = Declaraciones.M

    if _base_seed is not None:
        # La semilla depende del GRUPO LÓGICO (indice_delta) y de la
        # ITERACIÓN (contador), nunca de qué proceso físico ejecuta la tarea.
        # pool.map NO garantiza que el "grupo k" siempre lo corra el mismo
        # proceso; sembrar por identidad de proceso hacía que el camino
        # aleatorio dependiera de timing no determinístico del sistema
        # operativo. Sembrando por tarea, el resultado depende solo de
        # (Semilla, NumProcesos, datos), como exige RC-001.
        random.seed(_base_seed * 1_000_000 + indice_delta * 1_000 + contador)

    # Reiniciar SOLO el bloque de deltas de este grupo antes de usarlo --
    # los demás bloques no se tocan, por eso no hace falta ningún lock.
    delta_arr = _delta_arrays[indice_delta]
    delta_arr[:] = 0.0
    # CamineYClasifique escribe en el nombre de módulo Matriz_FeromonaAux
    # (con +=), así que basta con que ese nombre apunte a nuestra vista
    # compartida: el += de NumPy sobre una vista escribe directo en la
    # memoria compartida, sin copiarla.
    Declaraciones.Matriz_FeromonaAux = delta_arr

    Resultados = []
    for MatrizCGInicial in ListaDeCentroides:
        # Cada hormiga es un objeto nuevo en este proceso, con su propio
        # estado (centroides, lista de nodos, clasificación) -- no comparte
        # nada con las demás hormigas del grupo ni con las de otros procesos.
        Hormiga = Declaraciones.clsHormiga()
        Hormiga.MatrizCG = deepcopy(MatrizCGInicial)
        Hormiga.ListaDeNodosAClasificar = list(range(1, M + 1))
        Hormiga.VCardinalidades = [0] * Declaraciones.R
        Hormiga.VClasificacion = [0] * M
        Hormiga.ValorDeLaInerciaActual = inf

        # Recorrido secuencial de los M individuos -- esto no cambia respecto
        # a la versión original, cada paso sigue dependiendo del anterior.
        for i in range(M):
            Hormiga.CamineYClasifique(M - i)
        Hormiga.CalcularInercia_dados_CG_y_clasificacion()

        Resultados.append((Hormiga.MatrizCG, Hormiga.VClasificacion, Hormiga.VCardinalidades, Hormiga.ValorDeLaInerciaActual))

    # No se regresa ninguna matriz de feromona -- el proceso principal la lee
    # directo de memoria compartida. Solo viajan los resultados por hormiga,
    # que de todas formas hacen falta para actualizar la Colonia.
    return Resultados


def construir_clasificacion_paralelo(Colonia: "Declaraciones.clsColonia", pool: Pool, NumProcesos: int, contador: int) -> None:
    """Reemplazo paralelo de clsColonia.ContruirClasificacion(). Se llama una
    vez por cada iteración del ciclo externo (igual que en la versión
    secuencial original)."""
    M, R = Declaraciones.M, Declaraciones.R

    # Repartir las hormigas en NumProcesos grupos, guardando el índice
    # original de cada una para poder reasignar los resultados al objeto
    # correcto más abajo, sin importar en qué orden lleguen los procesos.
    Indices: list[list[int]] = [[] for _ in range(NumProcesos)]
    Centroides: list[list] = [[] for _ in range(NumProcesos)]
    for i, Hormiga in enumerate(Colonia.VectorDeHormigas):
        Slot = i % NumProcesos
        Indices[Slot].append(i)
        Centroides[Slot].append(Hormiga.MatrizCG)

    # Si hay menos hormigas que procesos, algunos slots quedan vacíos --
    # se excluyen para no mandar tareas de trabajo vacío.
    slots_usados = [k for k in range(NumProcesos) if Centroides[k]]
    IndicesTareas = [Indices[k] for k in slots_usados]
    # Solo viajan los centroides (livianos) y el índice de grupo/iteración --
    # la matriz de feromona NO se envía, ya está en memoria compartida.
    Tareas = [(Centroides[k], k, contador) for k in slots_usados]

    ResultadosPorProceso = pool.map(_clasificar_grupo_worker, Tareas)

    # Sumar los aportes de feromona de cada grupo leyendo directo de memoria
    # compartida (esto corre en el proceso principal, que tiene sus propias
    # vistas de NumPy sobre los mismos bloques -- ver ejecutar_corrida_nivel2).
    Matriz_FeromonaAux_total = np.zeros((M, R), dtype=np.float64)
    for k in slots_usados:
        Matriz_FeromonaAux_total += _delta_arrays_maestro[k]

    # Volcar en cada objeto Hormiga de la Colonia el resultado que le
    # corresponde, usando los índices originales guardados arriba.
    for IndicesGrupo, Resultados in zip(IndicesTareas, ResultadosPorProceso):
        for Indice, (MatrizCG, VClasificacion, VCardinalidades, Inercia) in zip(IndicesGrupo, Resultados):
            Hormiga = Colonia.VectorDeHormigas[Indice]
            Hormiga.MatrizCG = MatrizCG
            Hormiga.VClasificacion = VClasificacion
            Hormiga.VCardinalidades = VCardinalidades
            Hormiga.ValorDeLaInerciaActual = Inercia

    MejorHormiga = min(Colonia.VectorDeHormigas, key=lambda H: H.ValorDeLaInerciaActual)
    for Hormiga in Colonia.VectorDeHormigas:
        Hormiga.VCardinalidades = [0] * R

    # Actualización global de feromona (evaporación + refuerzo), vectorizada
    # con NumPy directo sobre la memoria compartida -- equivalente a
    # Colonia.Actualizar_el_rastro_de_la_feromona() de la versión secuencial.
    _pheromone_array_maestro[:] = (
        (1 - Declaraciones.Rho) * _pheromone_array_maestro
        + Declaraciones.Rho * Matriz_FeromonaAux_total
    )

    if MejorHormiga.ValorDeLaInerciaActual < Colonia.MejorInerciaDeLaHistoria:
        Colonia.MejorInerciaDeLaHistoria = MejorHormiga.ValorDeLaInerciaActual
        Colonia.MejorClasificacionDeLaHistoria = MejorHormiga.VClasificacion.copy()
    # Este método muta Matriz_FeromonaIndi_CG directamente; como ya apunta a
    # _pheromone_array_maestro, el cambio queda visible para los procesos
    # trabajadores en la siguiente iteración sin tocar ese método.
    Colonia.IntesificarRastroDeFeromonaDelaMejorSolucion()


def _ejecutar_algoritmo_nivel2(pool: Pool, NumProcesos: int) -> None:
    """Mismo ciclo que EjecutarAlgoritomoDeHormigas de la versión secuencial,
    pero llamando a la versión paralela de ContruirClasificacion en cada
    iteración."""
    if Declaraciones.Colonia is None:
        raise RuntimeError("La Colonia debe crearse antes de ejecutar el algoritmo.")
    IteraSinMejoras, InerciaAux, contador = 0, inf, 0
    while IteraSinMejoras < Declaraciones.MaxIteraSinMejora:
        contador += 1
        construir_clasificacion_paralelo(Declaraciones.Colonia, pool, NumProcesos, contador)
        IteraSinMejoras += 1
        if Declaraciones.Colonia.MejorInerciaDeLaHistoria < InerciaAux:
            InerciaAux = Declaraciones.Colonia.MejorInerciaDeLaHistoria
            IteraSinMejoras = 0
        # El refinamiento de k-medias se queda secuencial en el proceso
        # principal -- no está paralelizado en esta versión.
        if Declaraciones.MejoraKMediasActiva and Declaraciones.K_Medias_Cada > 0 and contador % Declaraciones.K_Medias_Cada == 0:
            for Hormiga in Declaraciones.Colonia.VectorDeHormigas:
                Hormiga.AplicarK_MediasCompleto()
                if Hormiga.ValorDeLaInerciaActual < Declaraciones.Colonia.MejorInerciaDeLaHistoria:
                    Declaraciones.Colonia.MejorInerciaDeLaHistoria = Hormiga.ValorDeLaInerciaActual
                    Declaraciones.Colonia.MejorClasificacionDeLaHistoria = Hormiga.VClasificacion.copy()


# Vistas del PROCESO PRINCIPAL sobre la misma memoria compartida que usan los
# trabajadores (se llenan en ejecutar_corrida_nivel2, antes de crear el Pool).
_pheromone_array_maestro: Optional[np.ndarray] = None
_delta_arrays_maestro: list[np.ndarray] = []


def ejecutar_corrida_nivel2(
    Parametros: dict,
    Poblacion: list[list[float]],
    Acotaciones: list[list[float]],
    NumProcesos: Optional[int] = None,
    Semilla: Optional[int] = None,
) -> ResultadoCorrida:
    """Punto de entrada de una corrida completa usando el Nivel 2. Crea el
    Pool y los bloques de memoria compartida UNA sola vez para toda la
    corrida (no en cada iteración), y los libera siempre al terminar.

    Semilla: si se especifica, la corrida es reproducible (misma Semilla +
    mismo NumProcesos + mismos datos -> mismo resultado). Si es None, el
    comportamiento es intencionalmente no reproducible.
    """
    global _pheromone_array_maestro, _delta_arrays_maestro

    Declaraciones.PoblacionOriginaldeIndi = [Fila.copy() for Fila in Poblacion]
    Declaraciones.M = len(Poblacion)
    Declaraciones.N = len(Poblacion[0]) if Poblacion else 0
    Declaraciones.MatrizDeAcotaciones = Acotaciones
    InicializarVariables(Parametros)

    M, R = Declaraciones.M, Declaraciones.R
    NumProcesos = NumProcesos or min(Declaraciones.CantiHormigas, os_cpu_count_seguro())

    # Un bloque de memoria compartida para la feromona y uno por cada proceso
    # trabajador para sus deltas -- todos del mismo tamaño (M x R floats).
    tamano_bytes = M * R * 8

    shm_pher = shared_memory.SharedMemory(create=True, size=tamano_bytes)
    shm_deltas = [
        shared_memory.SharedMemory(create=True, size=tamano_bytes)
        for _ in range(NumProcesos)
    ]
    todos_los_shm = [shm_pher, *shm_deltas]

    try:
        _pheromone_array_maestro = np.ndarray((M, R), dtype=np.float64, buffer=shm_pher.buf)
        _pheromone_array_maestro[:] = 0.0  # mismo estado inicial que la versión secuencial
        Declaraciones.Matriz_FeromonaIndi_CG = _pheromone_array_maestro

        _delta_arrays_maestro = [
            np.ndarray((M, R), dtype=np.float64, buffer=shm.buf) for shm in shm_deltas
        ]

        Inicio = perf_counter()
        # Sembrar también el proceso PRINCIPAL: IniciarCG (los centroides
        # iniciales de cada hormiga) se ejecuta aquí, antes de crear el Pool,
        # y usa random.random()/random.uniform() del módulo estándar. Sin
        # esto, aunque los trabajadores fueran reproducibles, cada corrida
        # arrancaría de centroides iniciales distintos y divergería desde el
        # primer paso.
        if Semilla is not None:
            random.seed(Semilla)
        Declaraciones.Colonia = Declaraciones.clsColonia(Declaraciones.CantiHormigas)
        with Pool(
            processes=NumProcesos,
            initializer=_worker_init,
            initargs=(
                Declaraciones.PoblacionOriginaldeIndi, M, Declaraciones.N, R,
                Declaraciones.Alpha, Declaraciones.Beta, Declaraciones.Q,
                Declaraciones.MinFero, Declaraciones.MinBase,
                shm_pher.name,
                [shm.name for shm in shm_deltas],
                Semilla,
            ),
        ) as pool:
            _ejecutar_algoritmo_nivel2(pool, NumProcesos)
        Tiempo = (perf_counter() - Inicio) * 1_000_000

        return (
            Declaraciones.Colonia.MejorInerciaDeLaHistoria,
            Declaraciones.Colonia.MejorClasificacionDeLaHistoria.copy(),
            Tiempo,
        )
    finally:
        # Liberar la memoria compartida SIEMPRE, incluso si algo falla arriba
        # -- los procesos trabajadores ya fueron cerrados por el "with Pool",
        # aquí solo falta cerrar y liberar las vistas del proceso principal.
        for shm in todos_los_shm:
            shm.close()
            shm.unlink()


def os_cpu_count_seguro() -> int:
    import os
    return os.cpu_count() or 4