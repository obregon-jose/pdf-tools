import customtkinter as ctk

class BaseTool(ctk.CTkFrame):
    def __init__(self, master, go_home):
        super().__init__(master)
        
        