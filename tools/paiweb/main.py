"""Punto de entrada principal de la aplicación"""
import customtkinter as ctk
from app import PAIWebCarnetsManager


def main():
    """Función principal"""
    # ctk.set_appearance_mode("dark")
    # ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("PAIWeb Carnets Manager - Búsqueda de Vacunas y Descarga Masiva")
    root.geometry("1200x800")
    root.minsize(1000, 600)
    root.resizable(True, True)
    
    app = PAIWebCarnetsManager(root)
    
    root.mainloop()


if __name__ == "__main__":
    main()