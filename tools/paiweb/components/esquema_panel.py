"""Panel de análisis de esquemas de vacunación"""
import customtkinter as ctk


class EsquemaVacunacionPanel(ctk.CTkFrame):
    """Panel que muestra el análisis de esquemas"""
    
    def __init__(self, master, analisis_esquemas, **kwargs):
        super().__init__(master, **kwargs)
        self.analisis_esquemas = analisis_esquemas
        self.configure(fg_color="#1e1e1e", corner_radius=6, border_width=1, border_color="#3a3a3a")
        self._build_ui()
    
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            self,
            text="📊 Análisis de Esquemas de Vacunación PAI",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#14b97d"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10,5))
        
        esquemas_scroll = ctk.CTkScrollableFrame(self, fg_color="#0d0d0d", height=250)
        esquemas_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        esquemas_scroll.grid_columnconfigure(0, weight=1)
        
        for idx, (esquema_key, datos) in enumerate(self.analisis_esquemas.items()):
            esquema_frame = self._create_esquema_item(esquemas_scroll, datos)
            esquema_frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=3)
    
    def _create_esquema_item(self, parent, datos):
        frame = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=6, border_width=1, border_color="#3a3a3a")
        frame.grid_columnconfigure(0, weight=1)
        
        if datos["completo"]:
            icono, color = "✅", "#27ae60"
        elif datos["porcentaje"] > 0:
            icono, color = "⚠️", "#fbc531"
        else:
            icono, color = "❌", "#e74c3c"
        
        opcional_text = " (Opcional)" if datos.get("opcional", False) else ""
        
        nombre_label = ctk.CTkLabel(
            frame,
            text=f"{icono} {datos['nombre']}{opcional_text} - {datos['total_encontradas']}/{datos['total_requeridas']} vacunas",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color,
            anchor="w"
        )
        nombre_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        if datos["vacunas_faltantes"]:
            faltantes_text = "Faltantes: " + ", ".join([v["biologico"] for v in datos["vacunas_faltantes"]])
            faltantes_label = ctk.CTkLabel(
                frame,
                text=faltantes_text,
                font=ctk.CTkFont(size=9),
                text_color="#e74c3c",
                wraplength=500,
                anchor="w"
            )
            faltantes_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
        
        return frame