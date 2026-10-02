import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs

# Configuración de parámetros
FILAS = 10000
COLUMNAS = 6
CENTROS_CLUSTERS = 4
DESVIACION_STD = 1.2  # Controla qué tan dispersos o concentrados están los clusters
NOMBRE_ARCHIVO = "datos_prueba_aco_clusters_20k.csv"

# 1. Generar clusters sintéticos reales
X, _ = make_blobs(
    n_samples=FILAS,
    n_features=COLUMNAS,
    centers=CENTROS_CLUSTERS,
    cluster_std=DESVIACION_STD,
    random_state=42,
)

# 2. Desplazar los valores para asegurar que todos sean estrictamente positivos (> 0)
if (X <= 0).any():
    X = X - X.min() + 0.1

X = np.round(X, 3)

# 3. Guardar en archivo CSV sin encabezado ni índice
df = pd.DataFrame(X)
df.to_csv(NOMBRE_ARCHIVO, index=False, header=False)

print(
    f"Dataset con clusters guardado en '{NOMBRE_ARCHIVO}' ({FILAS} filas, {COLUMNAS} columnas)."
)