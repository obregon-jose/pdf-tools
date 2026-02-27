"""Panel de paciente con información y vacunas"""
import customtkinter as ctk
import tkinter as tk
from utils import nombre_completo, format_date
from vaccine_analyzer import analizar_esquema_vacunacion
from .vaccines_table import VaccinesTable


class PatientVaccinePanel(ctk.CTkFrame):
    """Panel de paciente con acordeón para ver detalles"""
    
    def __init__(self, master, patient_data, vaccines_data, download_callback, is_not_found=False, **kwargs):
        super().__init__(master, **kwargs)
        self.patient_data = patient_data
        self.vaccines_data = vaccines_data
        self.download_callback = download_callback
        self.is_not_found = is_not_found
        self.selected_var = tk.BooleanVar(value=not is_not_found)
        self.is_expanded = False
        
        self.analisis_esquemas = analizar_esquema_vacunacion(vaccines_data) if not is_not_found else {}
        
        border_color = "#e74c3c" if is_not_found else "#3a3a3a"
        self.configure(fg_color="#1a1a1a", corner_radius=8, border_width=2, border_color=border_color)
        self.grid_columnconfigure(2, weight=1)
        
        self._build_header()
        
        if not is_not_found:
            self.details_frame = ctk.CTkFrame(self, fg_color="#0d0d0d", corner_radius=6)
            self.details_frame.grid_columnconfigure(0, weight=1)
    
    def _build_header(self):
        """Construye el header del panel"""
        self.checkbox = ctk.CTkCheckBox(
            self, text="", variable=self.selected_var,
            width=20, checkbox_width=20, checkbox_height=20,
            fg_color="#14b97d", hover_color="#0ea66b",
            state="disabled" if self.is_not_found else "normal"
        )
        self.checkbox.grid(row=0, column=0, padx=8, pady=8, sticky="n")
        
        if not self.is_not_found:
            self.expand_btn = ctk.CTkButton(
                self, text="▶", width=30, height=30,
                fg_color="#476cb2", hover_color="#3a5a9a",
                command=self.toggle_expand, font=ctk.CTkFont(size=14, weight="bold")
            )
            self.expand_btn.grid(row=0, column=1, padx=(0,8), pady=8, sticky="n")
        else:
            placeholder = ctk.CTkLabel(self, text="", width=30)
            placeholder.grid(row=0, column=1, padx=(0,8), pady=8, sticky="n")
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=2, sticky="ew", padx=5, pady=8)
        header_frame.grid_columnconfigure(0, weight=1)
        
        if self.is_not_found:
            doc = self.patient_data.get("numeroIdentificacion", "N/A")
            patient_label = ctk.CTkLabel(
                header_frame,
                text=f"❌ Documento: {doc} - NO ENCONTRADO",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#e74c3c", anchor="w"
            )
            patient_label.grid(row=0, column=0, sticky="w", padx=5)
        else:
            nombre = nombre_completo(self.patient_data)
            doc = self.patient_data.get("numeroIdentificacion", "N/A")
            tipo_doc = self.patient_data.get("tipoIdentificacionCodigo", "")
            fecha_nac = format_date(self.patient_data.get("fechaNacimiento", ""))
            
            patient_label = ctk.CTkLabel(
                header_frame,
                text=f"👤 {nombre} - {tipo_doc}{doc} (Nac: {fecha_nac})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#14b97d", anchor="w"
            )
            patient_label.grid(row=0, column=0, sticky="w", padx=5)
            
            vaccine_count = ctk.CTkLabel(
                header_frame,
                text=f"💉 {len(self.vaccines_data)} vacunas",
                font=ctk.CTkFont(size=12),
                text_color="#7f8c8d"
            )
            vaccine_count.grid(row=0, column=1, sticky="w", padx=10)
            
            esquemas_completos = sum(1 for e in self.analisis_esquemas.values() if e["completo"])
            esquemas_obligatorios = sum(1 for e in self.analisis_esquemas.values() if not e.get("opcional", False))
            
            esquemas_label = ctk.CTkLabel(
                header_frame,
                text=f"📊 {esquemas_completos}/{esquemas_obligatorios} esquemas",
                font=ctk.CTkFont(size=11),
                text_color="#14b97d" if esquemas_completos == esquemas_obligatorios else "#fbc531"
            )
            esquemas_label.grid(row=0, column=2, sticky="w", padx=10)
        
        if not self.is_not_found:
            self.btn_download_individual = ctk.CTkButton(
                self, text="📥 Descargar", width=110, height=32,
                fg_color="#14b97d", hover_color="#0ea66b",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self._download_individual
            )
            self.btn_download_individual.grid(row=0, column=3, padx=8, pady=8, sticky="n")
    
    def toggle_expand(self):
        if self.is_not_found:
            return
        
        if self.is_expanded:
            self.details_frame.grid_forget()
            self.expand_btn.configure(text="▶")
            self.is_expanded = False
        else:
            self.details_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=8, pady=(0,8))
            self.expand_btn.configure(text="▼")
            if not self.details_frame.winfo_children():
                self._populate_details()
            self.is_expanded = True
    
    def _populate_details(self):
        if self.is_not_found:
            return
        
        table = VaccinesTable(self.details_frame, self.vaccines_data)
        table.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    
    def _download_individual(self):
        if not self.is_not_found:
            self.download_callback(self.patient_data)
    
    def is_selected(self):
        return self.selected_var.get() and not self.is_not_found
    
    def get_patient_data(self):
        return self.patient_data