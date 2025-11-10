import customtkinter as ctk

class BaseTool(ctk.CTkFrame):
    def __init__(self, master, go_home):
        super().__init__(master)
        self.go_home = go_home
        
        # Contenido
        ctk.CTkLabel(self, text="Herramienta en desarrollo").pack(pady=5)

