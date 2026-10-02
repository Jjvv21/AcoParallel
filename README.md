# ProyectoHormigasPython

Migración a Python del proyecto Delphi **ProyectoHormigas**. Conserva los nombres
centrales del código original (`clsHormiga`, `clsColonia`, `PoblacionOriginaldeIndi`,
`EjecutarAlgoritomoDeHormigas`, etc.) para facilitar la comparación entre ambas versiones.

## Ejecución

```powershell
py -m pip install -r requirements.txt
py ProyectoHormigas.py
```

La interfaz usa `tkinter` (incluido con Python). `openpyxl` permite cargar y exportar
archivos `.xlsx`; los archivos `.csv` se pueden cargar sin dependencias adicionales.

## Estructura

- `Declaraciones.py`: estado global y clases `clsHormiga` y `clsColonia`.
- `Funciones_y_Procedimientos.py`: inicialización y ciclo del algoritmo.
- `FrmPrincipal.py`: ventana principal, importación, corridas y exportación.
- `FrmOptimizacion.py`: búsqueda por rejilla de parámetros.
- `ProyectoHormigas.py`: punto de entrada.

La matriz de entrada usa filas como individuos y columnas como variables, igual que el
programa Delphi. Las clases se numeran desde 1, también igual que el original.
