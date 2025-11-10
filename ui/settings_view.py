import customtkinter as ctk
from core.config import save_config

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app_config):
        super().__init__(master)
        self.app_config = app_config

        ctk.CTkLabel(self, text="Configuración", font=("Arial", 18, "bold")).pack(pady=10)

        # Selector de tema
        self.theme_option = ctk.CTkOptionMenu(
            self, values=["light", "dark"], 
            command=self.change_theme
        )
        self.theme_option.set(self.app_config.get("theme", "dark"))
        self.theme_option.pack(pady=10)

    def change_theme(self, new_theme):
        self.app_config["theme"] = new_theme
        save_config(self.app_config)
        ctk.set_appearance_mode(new_theme)
