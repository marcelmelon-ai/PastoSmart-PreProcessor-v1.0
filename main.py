"""
PastoSmart PreProcessor v1.0
Ponto de entrada principal da aplicação.
"""

import os
import sys

# Garante que o diretório raiz esteja no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cria pastas necessárias se não existirem
for folder in ["icons", "ui", "outputs", "temp"]:
    os.makedirs(folder, exist_ok=True)

from interface import PastoSmartApp
import tkinter as tk


def main():
    root = tk.Tk()
    app = PastoSmartApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
