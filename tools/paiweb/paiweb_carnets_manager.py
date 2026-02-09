import os
import re
import time
import requests
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from threading import Thread
from datetime import datetime

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_SEARCH_URL = "https://paiwebservices.paiweb.gov.co:8081/api/v2/Paciente/GetList"
API_CARNET_URL = "https://paiwebservices.paiweb.gov.co:8081/api/Carnet"
API_VACCINES_URL = "https://paiwebservices.paiweb.gov.co:8081/api/resumen/paciente"

# Carpeta Descargas por defecto
DOWNLOADS_FOLDER = str(Path.home() / "Downloads") if (Path.home() / "Downloads").exists() else str(Path.home() / "Descargas")

# Opciones de formato de nombre de archivo
FILENAME_OPTIONS = [
    "Nombre Completo",
    "Nombre Completo + Documento",
    "Nombre Completo + Tipo + Documento",
    "Nombre Completo + Tipo_Documento"
]

# Diccionario de esquemas de vacunación PAI Colombia
ESQUEMAS_VACUNACION = {
    "Recién nacido": {
        "nombre": "Recién nacido",
        "vacunas": [
            {"biologico": ["BCG"], "dosis": ["Única", "Unica"]},
            {"biologico": ["Hepatitis B Pediatrica", "Hepatitis B Pediátrica", "Hepatitis B"], "dosis": ["Única", "Unica", "Primera"]}
        ]
    },
    "2 meses": {
        "nombre": "2 meses",
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente"], "dosis": ["Primera"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio"], "dosis": ["Primera"]},
            {"biologico": ["Rotavirus"], "dosis": ["Primera"]},
            {"biologico": ["Neumococo", "Neumococo Conjugado", "Neumococo 13valente", "Neumococo 13 valente", "Neumococo Conjugado 10valente"], "dosis": ["Primera"]}
        ]
    },
    "4 meses": {
        "nombre": "4 meses",
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente"], "dosis": ["Segunda", "Segunda "]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio"], "dosis": ["Segunda", "Segunda "]},
            {"biologico": ["Rotavirus"], "dosis": ["Segunda", "Segunda "]},
            {"biologico": ["Neumococo", "Neumococo Conjugado", "Neumococo 13valente", "Neumococo 13 valente", "Neumococo Conjugado 10valente"], "dosis": ["Segunda", "Segunda "]}
        ]
    },
    "6 meses": {
        "nombre": "6 meses",
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente"], "dosis": ["Tercera"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio"], "dosis": ["Tercera"]},
            {"biologico": ["INFLUENZA", "INFLUENZA TRIVALENTE PEDIÁTRICA", "INFLUENZA TRIVALENTE PEDIATRICA", "Influenza"], "dosis": ["Primera"]}
        ]
    },
    "7 meses": {
        "nombre": "7 meses",
        "vacunas": [
            {"biologico": ["INFLUENZA", "INFLUENZA TRIVALENTE PEDIÁTRICA", "INFLUENZA TRIVALENTE PEDIATRICA", "Influenza"], "dosis": ["Segunda", "Segunda "]}
        ]
    },
    "12 meses": {
        "nombre": "12 meses (1 año)",
        "vacunas": [
            {"biologico": ["Triple Viral", "SRP", "Triple viral"], "dosis": ["Primera"]},
            {"biologico": ["Fiebre Amarilla", "FA"], "dosis": ["Única", "Unica"]},
            {"biologico": ["Hepatitis A", "Hepatitis A Pediátrica", "Hepatitis A Pediatrica"], "dosis": ["Única", "Unica"]},
            {"biologico": ["Neumococo", "Neumococo Conjugado", "Neumococo 13valente", "Neumococo 13 valente", "Neumococo Conjugado 10valente"], "dosis": ["Refuerzo"]},
            {"biologico": ["Varicela"], "dosis": ["Primera"]}
        ]
    },
    "18 meses": {
        "nombre": "18 meses (1 año y medio)",
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente", "DPT"], "dosis": ["Primer Refuerzo", "Refuerzo"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio Oral", "VOP", "Antipolio"], "dosis": ["Primer Refuerzo", "Refuerzo"]},
            {"biologico": ["Triple Viral", "SRP", "Triple viral"], "dosis": ["Refuerzo"]}
        ]
    },
    "5 años": {
        "nombre": "5 años",
        "vacunas": [
            {"biologico": ["DPT"], "dosis": ["Segundo Refuerzo", "Refuerzo"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio Oral", "VOP", "Antipolio"], "dosis": ["Segundo Refuerzo", "Refuerzo"]}
        ]
    },
    "9 años (VPH)": {
        "nombre": "9 años (VPH - niñas)",
        "vacunas": [
            {"biologico": ["VPH", "Virus Papiloma Humano", "Virus del Papiloma Humano"], "dosis": ["Única", "Unica", "Primera"]}
        ]
    }
}


def validar_token(token):
    """Valida si el token de acceso es válido"""
    try:
        res = requests.get(
            "https://paiwebservices.paiweb.gov.co:8081/api/Login/ValidateToken",
            cookies={"access_token": token},
            timeout=10, verify=False)
        return res.status_code == 200 and res.json() is True
    except Exception:
        return False


def nombre_completo(datos):
    """Genera el nombre completo del paciente"""
    partes = [
        datos.get("primerNombre", "").strip(),
        datos.get("segundoNombre", "").strip(),
        datos.get("primerApellido", "").strip(),
        datos.get("segundoApellido", "").strip()
    ]
    return " ".join([p for p in partes if p]).upper().strip()


def limpiar_nombre_archivo(nombre):
    """Limpia caracteres no permitidos en nombres de archivo"""
    base, ext = os.path.splitext(nombre)
    permitido = re.compile(r"[^\wÁÉÍÓÚáéíóúÑñ\s]+", re.UNICODE)
    base_limpio = permitido.sub("", base).strip()[:80]
    return base_limpio + ext


def generar_nombre_archivo(nombre_full, tdoc, ndoc, formato_idx):
    """Genera el nombre del archivo según el formato seleccionado."""
    if formato_idx == 0:
        nombre = f"{nombre_full}.pdf"
    elif formato_idx == 1:
        nombre = f"{nombre_full} {ndoc}.pdf"
    elif formato_idx == 2:
        nombre = f"{nombre_full} {tdoc}{ndoc}.pdf"
    else:
        nombre = f"{nombre_full} {tdoc}_{ndoc}.pdf"
    return limpiar_nombre_archivo(nombre)


def resolver_ruta(user_input):
    """Si empieza con / o es relativa, crea subcarpeta en Descargas."""
    user_input = user_input.strip()
    if not user_input:
        return DOWNLOADS_FOLDER
    if user_input.startswith('/') or user_input.startswith('\\') or not os.path.isabs(user_input):
        carpeta = os.path.join(DOWNLOADS_FOLDER, user_input.lstrip('/\\'))
    else:
        carpeta = user_input
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def format_date(date_str):
    """Convierte fecha ISO a formato dd/mm/yyyy"""
    if not date_str:
        return "N/A"
    try:
        date_part = date_str[:10]
        date_obj = datetime.strptime(date_part, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else "N/A"


def normalizar_biologico(biologico):
    """Normaliza el nombre del biológico removiendo caracteres especiales y convirtiendo a minúsculas"""
    if not biologico:
        return ""
    normalizado = biologico.lower().strip()
    normalizado = re.sub(r'[áäâà]', 'a', normalizado)
    normalizado = re.sub(r'[éëêè]', 'e', normalizado)
    normalizado = re.sub(r'[íïîì]', 'i', normalizado)
    normalizado = re.sub(r'[óöôò]', 'o', normalizado)
    normalizado = re.sub(r'[úüûù]', 'u', normalizado)
    normalizado = re.sub(r'[\(\)]', '', normalizado)
    return normalizado


def vacuna_coincide(vacuna_paciente, vacuna_esquema):
    """Verifica si una vacuna del paciente coincide con una vacuna del esquema"""
    biologico_paciente = normalizar_biologico(vacuna_paciente.get("biologico", ""))
    dosis_paciente = vacuna_paciente.get("dosis", "").strip()
    
    biologico_match = False
    for bio_esquema in vacuna_esquema["biologico"]:
        bio_esquema_norm = normalizar_biologico(bio_esquema)
        if bio_esquema_norm in biologico_paciente or biologico_paciente in bio_esquema_norm:
            biologico_match = True
            break
    
    if not biologico_match:
        return False
    
    dosis_match = dosis_paciente in vacuna_esquema["dosis"]
    return dosis_match


def analizar_esquema_vacunacion(vacunas_paciente):
    """Analiza las vacunas del paciente y determina qué esquemas ha completado"""
    resultado = {}
    
    for esquema_key, esquema_data in ESQUEMAS_VACUNACION.items():
        vacunas_requeridas = esquema_data["vacunas"]
        vacunas_encontradas = []
        vacunas_faltantes = []
        
        for vacuna_req in vacunas_requeridas:
            encontrada = False
            for vacuna_pac in vacunas_paciente:
                if vacuna_coincide(vacuna_pac, vacuna_req):
                    encontrada = True
                    vacunas_encontradas.append({
                        "biologico": vacuna_pac.get("biologico"),
                        "dosis": vacuna_pac.get("dosis"),
                        "fecha": vacuna_pac.get("fechaAplicacion")
                    })
                    break
            
            if not encontrada:
                vacunas_faltantes.append({
                    "biologico": vacuna_req["biologico"][0],
                    "dosis": vacuna_req["dosis"][0]
                })
        
        total_requeridas = len(vacunas_requeridas)
        total_encontradas = len(vacunas_encontradas)
        porcentaje = int((total_encontradas / total_requeridas) * 100) if total_requeridas > 0 else 0
        
        resultado[esquema_key] = {
            "nombre": esquema_data["nombre"],
            "total_requeridas": total_requeridas,
            "total_encontradas": total_encontradas,
            "porcentaje": porcentaje,
            "completo": porcentaje == 100,
            "vacunas_encontradas": vacunas_encontradas,
            "vacunas_faltantes": vacunas_faltantes
        }
    
    return resultado


class VaccinesTable(ctk.CTkFrame):
    """Tabla de vacunas usando Treeview de tkinter con foco visual en celda específica"""
    def __init__(self, master, vaccines_data, **kwargs):
        super().__init__(master, **kwargs)
        self.vaccines_data = vaccines_data
        self.configure(fg_color="#1e1e1e", corner_radius=6)
        self.selected_cell = None
        self.focused_item = None
        self.focused_column = None
        self._build_table()
    
    def _build_table(self):
        """Construye la tabla de vacunas"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview",
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=25
        )
        style.configure("Treeview.Heading",
            background="#1f6feb",
            foreground="#ffffff",
            borderwidth=1,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview",
            background=[("selected", "#14b97d")],
            foreground=[("selected", "#ffffff")]
        )
        style.map("Treeview.Heading",
            background=[("active", "#1558d6")]
        )
        
        columns = ("num", "edad", "dosis", "fecha", "biologico", "lote", "fabricante", "institucion")
        
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            height=8,
            selectmode="browse"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        self.tree.heading("num", text="#")
        self.tree.heading("edad", text="Edad trazadora")
        self.tree.heading("dosis", text="Dosis")
        self.tree.heading("fecha", text="Fecha de aplicación")
        self.tree.heading("biologico", text="Biológico")    
        self.tree.heading("lote", text="Lote")
        self.tree.heading("fabricante", text="Fabricante")
        self.tree.heading("institucion", text="Institución")
        
        self.tree.column("num", width=40, anchor="center", minwidth=40)
        self.tree.column("edad", width=120, anchor="w", minwidth=80)
        self.tree.column("dosis", width=120, anchor="w", minwidth=80)
        self.tree.column("fecha", width=110, anchor="center", minwidth=90)
        self.tree.column("biologico", width=200, anchor="w", minwidth=150)
        self.tree.column("lote", width=100, anchor="w", minwidth=80)
        self.tree.column("fabricante", width=150, anchor="w", minwidth=100)
        self.tree.column("institucion", width=250, anchor="w", minwidth=150)
        
        for idx, vaccine in enumerate(self.vaccines_data, 1):
            values = (
                idx,
                vaccine.get("edad", "N/A"),
                vaccine.get("dosis", "N/A"),
                format_date(vaccine.get("fechaAplicacion", "")),
                vaccine.get("biologico", "N/A"),
                vaccine.get("lote", "N/A") or "N/A",
                vaccine.get("fabricante", "N/A"),
                vaccine.get("institucionVacunadora", "N/A")
            )
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=values, tags=(tag,))
        
        self.tree.tag_configure("evenrow", background="#2b2b2b")
        self.tree.tag_configure("oddrow", background="#333333")
        
        self.tree.bind("<ButtonRelease-1>", self._on_click)
        self.tree.bind("<Double-Button-1>", self._on_double_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Control-c>", self._copy_cell)
        self.tree.bind("<Control-C>", self._copy_cell)
        self.tree.bind("<Control-a>", self._select_all_rows)
        self.tree.bind("<Control-A>", self._select_all_rows)
        
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="📋 Copiar celda (Ctrl+C)", command=lambda: self._copy_cell(None))
        self.context_menu.add_command(label="📄 Copiar fila completa", command=self._copy_row)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✓ Seleccionar todas las filas", command=lambda: self._select_all_rows(None))
        self.context_menu.add_command(label="📊 Copiar todas las filas", command=self._copy_all_rows)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        help_label = ctk.CTkLabel(
            self, 
            text="💡 Tip: Click en una celda para seleccionarla (resaltada en verde) | Doble click o Ctrl+C para copiar",
            font=ctk.CTkFont(size=10),
            text_color="#7f8c8d",
            wraplength=900
        )
        help_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
    
    def _on_motion(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            self.tree.configure(cursor="hand2")
        else:
            self.tree.configure(cursor="")
    
    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if item and column:
                self.tree.selection_set(item)
                self.selected_cell = (item, column)
                self.focused_item = item
                self.focused_column = column
    
    def _on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if item and column:
                self.tree.selection_set(item)
                self.selected_cell = (item, column)
                self.focused_item = item
                self.focused_column = column
                self._copy_cell(None)
    
    def _copy_cell(self, event):
        if not self.selected_cell:
            selection = self.tree.selection()
            if not selection:
                messagebox.showinfo("Sin selección", "Haz click en una celda para copiar su contenido.")
                return "break"
            
            item = selection[0]
            values = self.tree.item(item)["values"]
            if values:
                text = str(values[0])
                self.clipboard_clear()
                self.clipboard_append(text)
            return "break"
        
        item, column = self.selected_cell
        col_index = int(column.replace('#', '')) - 1
        values = self.tree.item(item)["values"]
        
        if col_index < len(values):
            cell_value = str(values[col_index])
            self.clipboard_clear()
            self.clipboard_append(cell_value)
            
            col_name = self.tree.heading(column)["text"]
            try:
                top_window = self.winfo_toplevel()
                original_title = top_window.title()
                top_window.title(f"✓ Copiado: {col_name} - {cell_value[:30]}...")
                self.after(2000, lambda: top_window.title(original_title))
            except:
                pass
        
        return "break"
    
    def _copy_row(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Sin selección", "Selecciona una fila para copiar.")
            return
        
        item = selection[0]
        values = self.tree.item(item)["values"]
        text = "\t".join(str(v) for v in values)
        
        self.clipboard_clear()
        self.clipboard_append(text)
        
        messagebox.showinfo("✓ Fila copiada", f"Se copió la fila completa al portapapeles.")
    
    def _select_all_rows(self, event):
        children = self.tree.get_children()
        for item in children:
            self.tree.selection_add(item)
        self.selected_cell = None
        return "break"
    
    def _copy_all_rows(self):
        headers = [self.tree.heading(col)["text"] for col in self.tree["columns"]]
        lines = ["\t".join(headers)]
        
        children = self.tree.get_children()
        for item in children:
            values = self.tree.item(item)["values"]
            lines.append("\t".join(str(v) for v in values))
        
        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        
        messagebox.showinfo("✓ Copiado", f"Se copiaron todas las filas ({len(children)}) con encabezados al portapapeles.")
    
    def _show_context_menu(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if item and column:
                self.tree.selection_set(item)
                self.selected_cell = (item, column)
                self.focused_item = item
                self.focused_column = column
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()


class EsquemaVacunacionPanel(ctk.CTkFrame):
    """Panel que muestra el análisis de esquemas de vacunación"""
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
        
        esquemas_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#0d0d0d",
            height=300
        )
        esquemas_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        esquemas_scroll.grid_columnconfigure(0, weight=1)
        
        row_idx = 0
        for esquema_key, datos in self.analisis_esquemas.items():
            esquema_frame = self._create_esquema_item(esquemas_scroll, datos)
            esquema_frame.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=3)
            row_idx += 1
    
    def _create_esquema_item(self, parent, datos):
        frame = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=6, border_width=1, border_color="#3a3a3a")
        frame.grid_columnconfigure(1, weight=1)
        
        if datos["completo"]:
            icono = "✅"
            color = "#27ae60"
        elif datos["porcentaje"] > 0:
            icono = "⚠️"
            color = "#fbc531"
        else:
            icono = "❌"
            color = "#e74c3c"
        
        nombre_label = ctk.CTkLabel(
            frame,
            text=f"{icono} {datos['nombre']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color,
            anchor="w"
        )
        nombre_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        progress = ctk.CTkProgressBar(frame, width=200, height=15)
        progress.set(datos["porcentaje"] / 100)
        progress.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        porcentaje_label = ctk.CTkLabel(
            frame,
            text=f"{datos['porcentaje']}%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=color
        )
        porcentaje_label.grid(row=0, column=2, sticky="e", padx=10, pady=5)
        
        detalles_label = ctk.CTkLabel(
            frame,
            text=f"{datos['total_encontradas']}/{datos['total_requeridas']} vacunas",
            font=ctk.CTkFont(size=10),
            text_color="#7f8c8d"
        )
        detalles_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=(0,5))
        
        if datos["vacunas_faltantes"]:
            faltantes_text = "Faltantes: " + ", ".join([v["biologico"] for v in datos["vacunas_faltantes"]])
            faltantes_label = ctk.CTkLabel(
                frame,
                text=faltantes_text,
                font=ctk.CTkFont(size=9),
                text_color="#e74c3c",
                wraplength=400,
                anchor="w"
            )
            faltantes_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=(0,5))
        
        return frame


class PatientVaccinePanel(ctk.CTkFrame):
    """Panel que muestra información del paciente y sus vacunas con acordeón cerrado por defecto"""
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
        
        self.checkbox = ctk.CTkCheckBox(
            self, text="", variable=self.selected_var,
            width=20, checkbox_width=20, checkbox_height=20,
            fg_color="#14b97d", hover_color="#0ea66b",
            state="disabled" if is_not_found else "normal"
        )
        self.checkbox.grid(row=0, column=0, padx=8, pady=8, sticky="n")
        
        if not is_not_found:
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
        
        if is_not_found:
            doc = patient_data.get("numeroIdentificacion", "N/A")
            patient_label = ctk.CTkLabel(
                header_frame,
                text=f"❌ Documento: {doc} - NO ENCONTRADO",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#e74c3c", anchor="w"
            )
            patient_label.grid(row=0, column=0, sticky="w", padx=5)
        else:
            nombre = nombre_completo(patient_data)
            doc = patient_data.get("numeroIdentificacion", "N/A")
            tipo_doc = patient_data.get("tipoIdentificacionCodigo", "")
            fecha_nac = format_date(patient_data.get("fechaNacimiento", ""))
            
            patient_label = ctk.CTkLabel(
                header_frame,
                text=f"���� {nombre} - {tipo_doc}{doc} (Nac: {fecha_nac})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#14b97d", anchor="w"
            )
            patient_label.grid(row=0, column=0, sticky="w", padx=5)
            
            vaccine_count = ctk.CTkLabel(
                header_frame,
                text=f"💉 {len(vaccines_data)} vacunas",
                font=ctk.CTkFont(size=12),
                text_color="#7f8c8d"
            )
            vaccine_count.grid(row=0, column=1, sticky="w", padx=10)
            
            esquemas_completos = sum(1 for e in self.analisis_esquemas.values() if e["completo"])
            esquemas_total = len(self.analisis_esquemas)
            esquemas_label = ctk.CTkLabel(
                header_frame,
                text=f"📊 {esquemas_completos}/{esquemas_total} esquemas",
                font=ctk.CTkFont(size=11),
                text_color="#14b97d" if esquemas_completos == esquemas_total else "#fbc531"
            )
            esquemas_label.grid(row=0, column=2, sticky="w", padx=10)
        
        if not is_not_found:
            self.btn_download_individual = ctk.CTkButton(
                self, text="📥 Descargar", width=110, height=32,
                fg_color="#14b97d", hover_color="#0ea66b",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self._download_individual
            )
            self.btn_download_individual.grid(row=0, column=3, padx=8, pady=8, sticky="n")
        
        if not is_not_found:
            self.details_frame = ctk.CTkFrame(self, fg_color="#0d0d0d", corner_radius=6)
            self.details_frame.grid_columnconfigure(0, weight=1)
    
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
        
        esquema_panel = EsquemaVacunacionPanel(self.details_frame, self.analisis_esquemas)
        esquema_panel.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        table = VaccinesTable(self.details_frame, self.vaccines_data)
        table.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    
    def _download_individual(self):
        if not self.is_not_found:
            self.download_callback(self.patient_data)
    
    def is_selected(self):
        return self.selected_var.get() and not self.is_not_found
    
    def get_patient_data(self):
        return self.patient_data


class PAIWebCarnetsManager(ctk.CTkFrame):
    """Descarga masiva de carnets PDF con consulta de vacunas"""
    def __init__(self, master=None):
        super().__init__(master)
        self.area_font_default = 13
        self.pack(fill="both", expand=True)
        self._build_ui()
        self.patient_panels = []
        self.session = None
        self.token = ""

    def _build_ui(self):
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky='nsew')

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)

        panel_top = ctk.CTkFrame(self.main_container)
        panel_top.grid(row=0, column=0, sticky='ew', padx=6, pady=(8,3))
        panel_top.grid_columnconfigure(1, weight=1)

        lbl_token = ctk.CTkLabel(panel_top, text="🔑 Access Token:", width=120, anchor="w", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_token.grid(row=0, column=0, padx=(6,3), pady=3, sticky="w")
        self.tk_token = ctk.CTkEntry(panel_top, font=ctk.CTkFont(size=13))
        self.tk_token.grid(row=0, column=1, padx=4, pady=3, sticky="ew")
        btn_pegar_token = ctk.CTkButton(panel_top, text="Pegar token", command=self._paste_token, width=110, fg_color="#476cb2")
        btn_pegar_token.grid(row=0, column=2, padx=(6,2), pady=3, sticky="w")

        lbl_dest = ctk.CTkLabel(panel_top, text="📁 Carpeta destino:", width=120, anchor="w")
        lbl_dest.grid(row=1, column=0, padx=(6,3), pady=3, sticky="w")
        self.destino = ctk.CTkEntry(panel_top, font=ctk.CTkFont(size=12))
        self.destino.grid(row=1, column=1, padx=4, pady=3, sticky="ew")
        self.destino.insert(0, DOWNLOADS_FOLDER)
        btn_folder = ctk.CTkButton(panel_top, text="Seleccionar carpeta", command=self._choose_folder, width=120)
        btn_folder.grid(row=1, column=2, padx=(6,2), pady=3, sticky="w")

        lbl_formato = ctk.CTkLabel(panel_top, text="📝 Convención de nombre:", width=120, anchor="w")
        lbl_formato.grid(row=2, column=0, padx=(6,3), pady=3, sticky="w")
        self.formato_selector = ctk.CTkComboBox(panel_top, values=FILENAME_OPTIONS, state="readonly", font=ctk.CTkFont(size=12), width=280)
        self.formato_selector.grid(row=2, column=1, padx=4, pady=3, sticky="w")
        self.formato_selector.set(FILENAME_OPTIONS[0])

        panel_input = ctk.CTkFrame(self.main_container)
        panel_input.grid(row=1, column=0, sticky="ew", padx=6, pady=5)
        panel_input.grid_columnconfigure(0, weight=1)

        lbl_docs = ctk.CTkLabel(panel_input, text="📑 Documentos (uno por línea):", font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        lbl_docs.grid(row=0, column=0, sticky="w", padx=8, pady=(5,2))

        input_container = ctk.CTkFrame(panel_input)
        input_container.grid(row=1, column=0, sticky="ew", padx=8, pady=(0,8))
        input_container.grid_columnconfigure(0, weight=1)

        self.area = ctk.CTkTextbox(input_container, font=("Consolas", self.area_font_default), height=100, border_width=2)
        self.area.grid(row=0, column=0, sticky="ew", padx=(0,5))

        btns_container = ctk.CTkFrame(input_container, fg_color="transparent")
        btns_container.grid(row=0, column=1, sticky="ns")

        btn_paste = ctk.CTkButton(btns_container, text="📋 Pegar", command=self._paste_clipboard, width=100, fg_color="#1f6feb")
        btn_paste.pack(pady=2)

        btn_clear = ctk.CTkButton(btns_container, text="🧹 Limpiar", command=self._clear_all, width=100, fg_color="#e74c3c")
        btn_clear.pack(pady=2)

        self.btn_search = ctk.CTkButton(
            btns_container, text="🔍 Buscar Vacunas",
            command=self._search_vaccines, width=100,
            fg_color="#14b97d", font=ctk.CTkFont(size=13, weight="bold"), height=35
        )
        self.btn_search.pack(pady=5)

        results_header = ctk.CTkFrame(self.main_container)
        results_header.grid(row=2, column=0, sticky="ew", padx=6, pady=(5,0))
        results_header.grid_columnconfigure(0, weight=1)

        self.lbl_results = ctk.CTkLabel(
            results_header, text="📋 Resultados (0 pacientes)",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        )
        self.lbl_results.grid(row=0, column=0, sticky="w", padx=8, pady=5)

        filter_frame = ctk.CTkFrame(results_header, fg_color="transparent")
        filter_frame.grid(row=0, column=1, sticky="e", padx=8)

        ctk.CTkLabel(filter_frame, text="Filtrar por esquema:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        esquemas_list = ["Todos"] + list(ESQUEMAS_VACUNACION.keys())
        self.filter_esquema_var = tk.StringVar(value="Todos")
        self.filter_esquema_combo = ctk.CTkComboBox(
            filter_frame, variable=self.filter_esquema_var,
            values=esquemas_list, width=180, state="readonly",
            command=self._apply_filter
        )
        self.filter_esquema_combo.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Filtrar por vacuna:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar(value="Todas")
        self.filter_combo = ctk.CTkComboBox(
            filter_frame, variable=self.filter_var,
            values=["Todas"], width=200, state="readonly",
            command=self._apply_filter
        )
        self.filter_combo.pack(side="left", padx=5)

        btn_select_all = ctk.CTkButton(
            filter_frame, text="✓ Todos", width=80,
            command=self._select_all, fg_color="#1f6feb"
        )
        btn_select_all.pack(side="left", padx=2)

        btn_deselect_all = ctk.CTkButton(
            filter_frame, text="✗ Ninguno", width=80,
            command=self._deselect_all, fg_color="#6c757d"
        )
        btn_deselect_all.pack(side="left", padx=2)

        self.results_container = ctk.CTkScrollableFrame(
            self.main_container, fg_color="#0a0a0a",
            corner_radius=8, border_width=2, border_color="#2a2a2a"
        )
        self.results_container.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0,5))
        self.results_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(3, weight=1)

        download_panel = ctk.CTkFrame(self.main_container)
        download_panel.grid(row=4, column=0, sticky="ew", padx=6, pady=(5,8))
        download_panel.grid_columnconfigure(0, weight=1)

        self.btn_download = ctk.CTkButton(
            download_panel, text="📥 Descargar Carnets Seleccionados",
            command=self._start_download, fg_color="#14b97d",
            font=ctk.CTkFont(size=15, weight="bold"), height=40
        )
        self.btn_download.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        self.logbox = ctk.CTkTextbox(
            self.main_container, font=("Consolas", 11),
            corner_radius=8, border_width=2, height=100
        )
        self.logbox.grid(row=5, column=0, sticky="ew", padx=6, pady=(0,5))
        self.logbox.configure(state="disabled")
        self._log_info("Listo para comenzar. Ingresa documentos y busca vacunas.", "INFO")

    def _choose_folder(self):
        carpeta = filedialog.askdirectory(title="Selecciona carpeta destino")
        if carpeta:
            self.destino.delete(0, tk.END)
            self.destino.insert(0, carpeta)

    def _paste_token(self):
        try:
            t = self.clipboard_get().strip()
            self.tk_token.delete(0, tk.END)
            self.tk_token.insert(0, t)
            self._log_info("Token pegado desde portapapeles.", "SUCCESS")
        except Exception:
            messagebox.showerror("Portapapeles", "No se pudo obtener el token del portapapeles.")

    def _paste_clipboard(self):
        try:
            texto = self.clipboard_get()
            lines = [l.strip() for l in texto.replace("\r", "").split("\n") if l.strip()]
            added = 0
            for doc in lines:
                docnum = re.sub(r"\D", "", doc)
                if docnum:
                    self.area.insert("end", docnum + "\n")
                    added += 1
            self._log_info(f"Se agregaron {added} documentos desde portapapeles.", "SUCCESS")
        except Exception:
            messagebox.showerror("Portapapeles", "No se pudo obtener el texto del portapapeles.")

    def _clear_all(self):
        self.area.delete("1.0", tk.END)
        self._clear_results()
        self._log_info("Panel limpiado completamente.", "INFO")

    def _clear_results(self):
        for widget in self.results_container.winfo_children():
            widget.destroy()
        self.patient_panels.clear()
        self.lbl_results.configure(text="📋 Resultados (0 pacientes)")
        self.filter_combo.configure(values=["Todas"])
        self.filter_var.set("Todas")

    def _get_documents(self):
        return [re.sub(r"\D", "", l.strip()) for l in self.area.get("1.0", "end").splitlines() 
                if l.strip() and len(re.sub(r"\D", "", l.strip())) > 3]

    def _get_filename_format_index(self):
        try:
            return FILENAME_OPTIONS.index(self.formato_selector.get())
        except ValueError:
            return 0

    def _log_info(self, msg, t="INFO"):
        self.logbox.configure(state="normal")
        color = {"INFO":"#7f8c8d","ERROR":"#e74c3c","SUCCESS":"#27ae60","WARN":"#fbc531"}.get(t,"#636e72")
        try:
            self.logbox.insert("end", f"[{t}] {msg}\n")
        except Exception:
            self.logbox.insert("end", f"[{t}] (error codificación)\n")
        self.logbox.tag_config(t, foreground=color)
        self.logbox.tag_add(t, "end-2l", "end-1l")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")
        self.update()

    def _search_vaccines(self):
        Thread(target=self._search_vaccines_thread, daemon=True).start()

    def _search_vaccines_thread(self):
        self.btn_search.configure(state="disabled", fg_color="#888")
        self.btn_download.configure(state="disabled", fg_color="#888")
        self.update()
        
        self.token = self.tk_token.get().strip()
        if not self.token:
            self._log_info("Ingresa tu access_token.", "ERROR")
            messagebox.showerror("Error de acceso", "Debes ingresar un access_token válido.")
            self.btn_search.configure(state="normal", fg_color="#14b97d")
            return

        self._log_info("Validando token...", "INFO")
        if not validar_token(self.token):
            self._log_info("El access_token es inválido o expiró.", "ERROR")
            messagebox.showerror("Token inválido", "El access_token es inválido o expiró. Ingresa uno nuevo.")
            self.btn_search.configure(state="normal", fg_color="#14b97d")
            return

        documentos = self._get_documents()
        if not documentos:
            self._log_info("No se ingresaron números de documento.", "ERROR")
            messagebox.showerror("Falta documentos", "No se detectaron números de documento válidos.")
            self.btn_search.configure(state="normal", fg_color="#14b97d")
            return

        self._clear_results()
        
        self.session = requests.Session()
        self.session.cookies.set("access_token", self.token)
        headers = {"Content-Type": "application/json"}

        total = len(documentos)
        self._log_info(f"Iniciando búsqueda de {total} pacientes...", "INFO")
        
        all_vaccines = set()
        
        for idx, ndoc in enumerate(documentos, 1):
            try:
                time.sleep(0.3)
                
                self._log_info(f"[{idx}/{total}] Buscando paciente {ndoc}...", "INFO")
                
                payload = {
                    "size": 10, 
                    "totalElements": 0, 
                    "totalPages": 0, 
                    "pageNumber": 0,
                    "data": {
                        "numeroIdentificacion": ndoc,
                        "tipoDocumento": {},
                        "numeroIdentificacionCuidador": "",
                        "type": "basic"
                    }
                }
                
                res = self.session.post(API_SEARCH_URL, json=payload, headers=headers, timeout=20, verify=False)
                
                if res.status_code != 200:
                    self._log_info(f"Error en búsqueda del paciente {ndoc}. Status: {res.status_code}", "ERROR")
                    self._add_not_found_panel(ndoc)
                    continue
                
                jres = res.json()
                
                if not jres or not jres.get('data') or len(jres.get('data', [])) == 0:
                    self._log_info(f"Paciente {ndoc} no encontrado en el sistema.", "WARN")
                    self._add_not_found_panel(ndoc)
                    continue

                data_list = jres.get("data", [])
                paciente = data_list[0]
                
                paciente_id = paciente.get("pacienteId")
                
                if not paciente_id:
                    self._log_info(f"No se encontró pacienteId para el documento {ndoc}.", "WARN")
                    self._add_not_found_panel(ndoc)
                    continue
                
                nombre = nombre_completo(paciente)
                self._log_info(f"✓ Paciente encontrado: {nombre} (ID: {paciente_id})", "SUCCESS")
                
                time.sleep(0.3)
                self._log_info(f"[{idx}/{total}] Consultando vacunas del paciente ID {paciente_id}...", "INFO")
                
                vaccines_url = f"{API_VACCINES_URL}/{paciente_id}/aplicaciones"
                vaccines_res = self.session.get(vaccines_url, timeout=20, verify=False)
                
                vaccines = []
                if vaccines_res.status_code == 200:
                    vaccines = vaccines_res.json()
                    if isinstance(vaccines, list):
                        for v in vaccines:
                            all_vaccines.add(v.get("biologico", "N/A"))
                        self._log_info(f"✓ {len(vaccines)} vacunas encontradas.", "SUCCESS")
                    else:
                        self._log_info(f"Formato de respuesta inesperado para vacunas de ID {paciente_id}.", "WARN")
                else:
                    self._log_info(f"No se pudieron obtener vacunas del paciente ID {paciente_id}. Status: {vaccines_res.status_code}", "WARN")
                
                self._add_patient_panel(paciente, vaccines)
                
            except Exception as ex:
                self._log_info(f"Error al procesar documento {ndoc}: {ex}", "ERROR")
                self._add_not_found_panel(ndoc)

        vaccine_list = ["Todas"] + sorted(list(all_vaccines))
        self.filter_combo.configure(values=vaccine_list)
        
        found_count = sum(1 for p in self.patient_panels if not p.is_not_found)
        not_found_count = sum(1 for p in self.patient_panels if p.is_not_found)
        self.lbl_results.configure(text=f"📋 Resultados ({found_count} encontrados, {not_found_count} no encontrados)")
        
        self._log_info(f"Búsqueda completada. {found_count} pacientes encontrados, {not_found_count} no encontrados.", "SUCCESS")
        self.btn_search.configure(state="normal", fg_color="#14b97d")
        self.btn_download.configure(state="normal", fg_color="#14b97d")

    def _add_patient_panel(self, patient_data, vaccines_data):
        panel = PatientVaccinePanel(
            self.results_container,
            patient_data, vaccines_data,
            download_callback=self._download_single_carnet,
            is_not_found=False
        )
        panel.grid(row=len(self.patient_panels), column=0, sticky="ew", padx=5, pady=5)
        self.patient_panels.append(panel)
    
    def _add_not_found_panel(self, documento):
        patient_data = {"numeroIdentificacion": documento}
        panel = PatientVaccinePanel(
            self.results_container,
            patient_data, [],
            download_callback=None,
            is_not_found=True
        )
        panel.grid(row=len(self.patient_panels), column=0, sticky="ew", padx=5, pady=5)
        self.patient_panels.append(panel)

    def _apply_filter(self, choice=None):
        filter_value = self.filter_var.get()
        filter_esquema = self.filter_esquema_var.get()
        
        visible_count = 0
        for panel in self.patient_panels:
            if panel.is_not_found:
                panel.grid()
                continue
            
            show_panel = True
            
            if filter_esquema != "Todos":
                if filter_esquema in panel.analisis_esquemas:
                    if not panel.analisis_esquemas[filter_esquema]["completo"]:
                        show_panel = False
                else:
                    show_panel = False
            
            if show_panel and filter_value != "Todas":
                has_vaccine = any(
                    v.get("biologico") == filter_value 
                    for v in panel.vaccines_data
                )
                if not has_vaccine:
                    show_panel = False
            
            if show_panel:
                panel.grid()
                visible_count += 1
            else:
                panel.grid_remove()
        
        not_found_count = sum(1 for p in self.patient_panels if p.is_not_found)
        self.lbl_results.configure(text=f"📋 Resultados ({visible_count} encontrados, {not_found_count} no encontrados)")

    def _select_all(self):
        for panel in self.patient_panels:
            if panel.winfo_viewable() and not panel.is_not_found:
                panel.selected_var.set(True)
        self._log_info("Todos los pacientes visibles seleccionados.", "INFO")

    def _deselect_all(self):
        for panel in self.patient_panels:
            if not panel.is_not_found:
                panel.selected_var.set(False)
        self._log_info("Todos los pacientes deseleccionados.", "INFO")

    def _download_single_carnet(self, patient_data):
        Thread(target=self._download_single_thread, args=(patient_data,), daemon=True).start()

    def _download_single_thread(self, patient_data):
        carpeta = resolver_ruta(self.destino.get())
        formato_idx = self._get_filename_format_index()
        
        tdoc = patient_data.get("tipoIdentificacionCodigo", "")
        ndoc = patient_data.get("numeroIdentificacion", "")
        fnac = patient_data.get("fechaNacimiento", "")[:10] if patient_data.get("fechaNacimiento") else ""
        nombre_full = nombre_completo(patient_data)
        
        self._log_info(f"Descargando carnet individual de {nombre_full}...", "INFO")
        
        try:
            payload_carnet = {
                "fechaNacimiento": fnac,
                "tipoDocumento": tdoc,
                "numeroDocumento": ndoc,
                "nombreCompleto": nombre_full
            }
            
            file_name = generar_nombre_archivo(nombre_full, tdoc, ndoc, formato_idx)
            
            carnet = self.session.post(API_CARNET_URL, json=payload_carnet, timeout=20, verify=False)
            
            if carnet.status_code == 200 and carnet.headers.get("Content-Type", "").startswith("application/pdf"):
                path = os.path.join(carpeta, file_name)
                with open(path, "wb") as f:
                    f.write(carnet.content)
                self._log_info(f"✅ Carnet individual descargado: {file_name}", "SUCCESS")
                messagebox.showinfo("Descarga exitosa", f"Carnet descargado correctamente:\n{file_name}")
            else:
                self._log_info(f"❌ Error al descargar carnet de {nombre_full}", "ERROR")
                messagebox.showerror("Error de descarga", f"No se pudo descargar el carnet de {nombre_full}")
                
        except Exception as ex:
            self._log_info(f"❌ Error inesperado: {ex}", "ERROR")
            messagebox.showerror("Error", f"Error al descargar carnet: {ex}")

    def _start_download(self):
        Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        self.btn_download.configure(state="disabled", fg_color="#888")
        self.update()

        selected_patients = [p for p in self.patient_panels if p.is_selected() and p.winfo_viewable() and not p.is_not_found]
        
        if not selected_patients:
            self._log_info("No hay pacientes seleccionados para descargar.", "WARN")
            messagebox.showwarning("Sin selección", "Debes seleccionar al menos un paciente para descargar.")
            self.btn_download.configure(state="normal", fg_color="#14b97d")
            return

        carpeta = resolver_ruta(self.destino.get())
        formato_idx = self._get_filename_format_index()

        total = len(selected_patients)
        success, failed = 0, 0
        failed_list = []

        self._log_info(f"Iniciando descarga de {total} carnets...", "INFO")

        for idx, panel in enumerate(selected_patients, 1):
            try:
                time.sleep(0.3)
                
                patient = panel.get_patient_data()
                tdoc = patient.get("tipoIdentificacionCodigo", "")
                ndoc = patient.get("numeroIdentificacion", "")
                fnac = patient.get("fechaNacimiento", "")[:10] if patient.get("fechaNacimiento") else ""
                nombre_full = nombre_completo(patient)
                
                self._log_info(f"[{idx}/{total}] Descargando carnet de {nombre_full}...", "INFO")
                
                payload_carnet = {
                    "fechaNacimiento": fnac,
                    "tipoDocumento": tdoc,
                    "numeroDocumento": ndoc,
                    "nombreCompleto": nombre_full
                }
                
                file_name = generar_nombre_archivo(nombre_full, tdoc, ndoc, formato_idx)
                
                carnet = self.session.post(API_CARNET_URL, json=payload_carnet, timeout=20, verify=False)
                
                if carnet.status_code == 200 and carnet.headers.get("Content-Type", "").startswith("application/pdf"):
                    path = os.path.join(carpeta, file_name)
                    with open(path, "wb") as f:
                        f.write(carnet.content)
                    self._log_info(f"✅ PDF guardado: {file_name}", "SUCCESS")
                    success += 1
                else:
                    self._log_info(f"❌ Error al descargar carnet de {nombre_full}", "ERROR")
                    failed_list.append(f"{nombre_full} ({ndoc})")
                    failed += 1
                    
            except Exception as ex:
                self._log_info(f"❌ Error inesperado: {ex}", "ERROR")
                failed_list.append(f"{nombre_full} ({ndoc}): {ex}")
                failed += 1

        self._log_info(f"FIN | Descargados: {success} | Fallidos: {failed}", "SUCCESS")
        self.btn_download.configure(state="normal", fg_color="#14b97d")

        if failed_list:
            messagebox.showwarning(
                "Descarga completada con errores",
                f"Descargados: {success}\nFallidos: {failed}\n\nRevisa el log para más detalles."
            )
        else:
            messagebox.showinfo(
                "Descarga completada",
                f"¡Listo!\n\nDescargados correctamente: {success}\nSin errores."
            )


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("PAIWeb Carnets Manager - Búsqueda de Vacunas y Descarga Masiva")
    root.geometry("1200x800")
    root.minsize(1000, 600)
    root.resizable(True, True)
    PAIWebCarnetsManager(root)
    root.mainloop()