"""Punto de entrada equivalente a ProyectoHormigas.dpr."""
import tkinter as tk
from FrmPrincipal import TForm1


def main() -> None:
    Application = tk.Tk()
    # Evita que los controles centrales se superpongan al reducir la ventana.
    Application.minsize(1020, 620)
    TForm1(Application)
    Application.mainloop()


if __name__ == "__main__":
    main()
