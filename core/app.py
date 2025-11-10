import customtkinter as ctk
import os, sys
from pathlib import Path

from core.config import load_config, save_config
from ui.main_window import MainWindow
from core.config import APP_NAME, VERSION, DEFAULT_CONFIG

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_data = load_config()
        self.title(APP_NAME)
        # self.iconbitmap(resource_path("assets/icon.ico"))
        self.geometry("990x540")
        self.minsize(990, 540)

        ctk.set_appearance_mode(self.config_data.get("theme", DEFAULT_CONFIG["theme"]))
        ctk.set_default_color_theme(DEFAULT_CONFIG["color_theme"])

        self.main_window = MainWindow(self, self.config_data)
        self.main_window.pack(fill="both", expand=True)

        # Correcta gestión del botón X
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Guarda configuración y cierra la app correctamente."""
        try:
            self.config_data["last_tool"] = self.main_window.current_tool_name
            save_config(self.config_data)
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
        finally:
            self.destroy()  # ← Cierra la ventana correctamente

