import os
import re
import csv
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog
from openpyxl import load_workbook
from typing import List, Dict, Set, Tuple


# ==================== UTILIDADES ====================

def extract_document_full(text: str) -> str:
    """
    Extrae el documento completo con tipo y número.
    Ejemplos: CC1234567890, TI9876543210, RC1122334455
    """
    if not text:
        return ""
    
    # Patrones comunes: TIPO + NÚMERO
    patterns = [
        r'((?:CC|TI|CE|RC|PA|PE|NIT|CD|SC|CN|AS|MS)\s*\d{6,})',  # Tipo seguido de número
        r'(\d{8,})',  # Solo números largos como fallback
    ]
    
    text_upper = text.upper()
    
    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            doc = match.group(1)
            # Limpiar espacios/guiones
            doc = re.sub(r'[\s\-_]+', '', doc)
            return doc
    
    return ""


def normalize_document(doc: str) -> str:
    """Normaliza un documento para comparación (sin espacios, mayúsculas)."""
    if not doc:
        return ""
    return re.sub(r'[\s\-_]+', '', doc.strip().upper())


def classify_files(folder: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    Clasifica archivos PDF por prefijo CRC/OPF.
    Retorna: {'CRC': [(filename, documento)], 'OPF': [(filename, documento)], 'OTHER': [...]}
    """
    files = {
        'CRC': [],
        'OPF': [],
        'OTHER': []
    }
    
    if not os.path.exists(folder):
        return files
    
    for f in os.listdir(folder):
        if not f.lower().endswith('.pdf'):
            continue
        
        full_path = os.path.join(folder, f)
        if not os.path.isfile(full_path):
            continue
        
        # Extraer documento del nombre del archivo
        doc = extract_document_full(f)
        
        name_upper = f.upper()
        if name_upper.startswith('CRC'):
            files['CRC'].append((f, doc))
        elif name_upper.startswith('OPF'):
            files['OPF'].append((f, doc))
        else:
            files['OTHER'].append((f, doc))
    
    return files


def build_document_index(files: List[Tuple[str, str]]) -> Dict[str, str]:
    """
    Construye índice: documento_normalizado -> nombre_archivo
    """
    index = {}
    for filename, doc in files:
        if doc:
            norm_doc = normalize_document(doc)
            if norm_doc:
                # Si ya existe, mantener el primero encontrado
                if norm_doc not in index:
                    index[norm_doc] = filename
    return index


# ==================== LÓGICA DE VERIFICACIÓN ====================

def verify_documents(input_docs: List[str], crc_files: List[Tuple[str, str]], opf_files: List[Tuple[str, str]]) -> List[Dict]:
    """
    Verifica documentos contra archivos CRC y OPF.
    
    Retorna lista de diccionarios con:
    - documento: documento completo (ej: CC1234567890)
    - crc_archivo: archivo CRC encontrado (o '')
    - opf_archivo: archivo OPF encontrado (o '')
    - estado: descripción del estado
    """
    results = []
    
    # Construir índices
    crc_index = build_document_index(crc_files)
    opf_index = build_document_index(opf_files)
    
    # Conjuntos de documentos normalizados
    input_set = {}  # norm_doc -> original_doc
    crc_set = set(crc_index.keys())
    opf_set = set(opf_index.keys())
    
    # Normalizar input
    for doc in input_docs:
        doc_extracted = extract_document_full(doc)
        if doc_extracted:
            norm_doc = normalize_document(doc_extracted)
            if norm_doc:
                input_set[norm_doc] = doc_extracted
    
    # Determinar qué fuentes hay
    has_input = len(input_set) > 0
    has_crc = len(crc_files) > 0
    has_opf = len(opf_files) > 0
    
    # Caso 1: Solo hay INPUT vs CRC
    if has_input and has_crc and not has_opf:
        for norm_doc, orig_doc in sorted(input_set.items()):
            crc_file = crc_index.get(norm_doc, '')
            estado = "✅ Encontrado en CRC" if crc_file else "❌ No encontrado en CRC"
            results.append({
                'documento': orig_doc,
                'crc_archivo': crc_file,
                'opf_archivo': '',
                'estado': estado
            })
    
    # Caso 2: Solo hay INPUT vs OPF
    elif has_input and has_opf and not has_crc:
        for norm_doc, orig_doc in sorted(input_set.items()):
            opf_file = opf_index.get(norm_doc, '')
            estado = "✅ Encontrado en OPF" if opf_file else "❌ No encontrado en OPF"
            results.append({
                'documento': orig_doc,
                'crc_archivo': '',
                'opf_archivo': opf_file,
                'estado': estado
            })
    
    # Caso 3: Solo hay CRC vs OPF (sin INPUT)
    elif not has_input and has_crc and has_opf:
        all_docs = sorted(crc_set | opf_set)
        for norm_doc in all_docs:
            crc_file = crc_index.get(norm_doc, '')
            opf_file = opf_index.get(norm_doc, '')
            
            if crc_file and opf_file:
                estado = "✅ Coincide CRC y OPF"
            elif crc_file and not opf_file:
                estado = "⚠️ Solo en CRC"
            elif opf_file and not crc_file:
                estado = "⚠️ Solo en OPF"
            else:
                estado = "❌ Error"
            
            results.append({
                'documento': norm_doc,
                'crc_archivo': crc_file,
                'opf_archivo': opf_file,
                'estado': estado
            })
    
    # Caso 4: Hay INPUT, CRC y OPF (verificación completa)
    elif has_input and has_crc and has_opf:
        all_docs_norm = sorted(set(input_set.keys()) | crc_set | opf_set)
        
        for norm_doc in all_docs_norm:
            orig_doc = input_set.get(norm_doc, norm_doc)
            in_input = norm_doc in input_set
            crc_file = crc_index.get(norm_doc, '')
            opf_file = opf_index.get(norm_doc, '')
            
            # Determinar estado
            if in_input and crc_file and opf_file:
                estado = "✅ Completo (3/3)"
            elif in_input and crc_file and not opf_file:
                estado = "⚠️ Falta OPF (2/3)"
            elif in_input and opf_file and not crc_file:
                estado = "⚠️ Falta CRC (2/3)"
            elif in_input and not crc_file and not opf_file:
                estado = "❌ Solo en INPUT (1/3)"
            elif not in_input and crc_file and opf_file:
                estado = "⚠️ No en INPUT (2/2)"
            elif not in_input and crc_file:
                estado = "⚠️ Solo CRC, no en INPUT"
            elif not in_input and opf_file:
                estado = "⚠️ Solo OPF, no en INPUT"
            else:
                estado = "❌ Error"
            
            results.append({
                'documento': orig_doc,
                'crc_archivo': crc_file,
                'opf_archivo': opf_file,
                'estado': estado
            })
    
    # Caso 5: Solo hay INPUT (sin archivos)
    elif has_input and not has_crc and not has_opf:
        for norm_doc, orig_doc in sorted(input_set.items()):
            results.append({
                'documento': orig_doc,
                'crc_archivo': '',
                'opf_archivo': '',
                'estado': "❌ Sin archivos en carpeta"
            })
    
    # Caso 6: Solo hay CRC
    elif has_crc and not has_input and not has_opf:
        for norm_doc in sorted(crc_set):
            results.append({
                'documento': norm_doc,
                'crc_archivo': crc_index[norm_doc],
                'opf_archivo': '',
                'estado': "ℹ️ Solo archivos CRC"
            })
    
    # Caso 7: Solo hay OPF
    elif has_opf and not has_input and not has_crc:
        for norm_doc in sorted(opf_set):
            results.append({
                'documento': norm_doc,
                'crc_archivo': '',
                'opf_archivo': opf_index[norm_doc],
                'estado': "ℹ️ Solo archivos OPF"
            })
    
    return results


# ==================== APLICACIÓN GUI ====================

class PDFVerifierApp(ctk.CTkFrame):
    """Aplicación para verificar PDFs con prefijos CRC/OPF."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        self.folder_path = ""
        self._build_ui()
    
    def _build_ui(self):
        """Construye la interfaz."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self._build_top_panel()
        self._build_input_panel()
        self._build_results_panel()
        self._build_log_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # Carpeta
        ctk.CTkLabel(panel, text="📁 Carpeta:", width=80, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.folder_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona carpeta con archivos PDF")
        self.folder_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar", width=120, command=self._select_folder).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Botones de acción
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.verify_btn = ctk.CTkButton(btn_frame, text="🔍 Verificar", command=self._verify, fg_color="#1f6feb")
        self.verify_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.export_btn = ctk.CTkButton(btn_frame, text="💾 Exportar CSV", command=self._export_csv, fg_color="#27ae60")
        self.export_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._clear, fg_color="#e74c3c")
        self.clear_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    
    def _build_input_panel(self):
        """Panel de entrada de documentos."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.pack(fill="x", padx=6, pady=(6,4))
        
        ctk.CTkLabel(header, text="📝 Documentos a verificar (Ej: CC1234567890, TI9876543210)", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="📁 Importar Excel", width=120, command=self._import_excel).pack(side="right")
        
        # Textbox
        self.input_text = ctk.CTkTextbox(panel, height=100, font=ctk.CTkFont(family="Consolas", size=11))
        self.input_text.pack(fill="x", padx=6, pady=(0,6))
    
    def _build_results_panel(self):
        """Panel de resultados con tabla."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6,4))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="📊 Resultados", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        self.count_lbl = ctk.CTkLabel(header, text="0 registros", text_color="gray", anchor="e")
        self.count_lbl.grid(row=0, column=1, sticky="e")
        
        # Tabla
        table_frame = ctk.CTkFrame(panel)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        self._setup_table_style()
        
        cols = ("documento", "crc", "opf", "estado")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", style="Dark.Treeview")
        
        self.table.heading("documento", text="Documento")
        self.table.heading("crc", text="Archivo CRC")
        self.table.heading("opf", text="Archivo OPF")
        self.table.heading("estado", text="Estado")
        
        self.table.column("documento", width=150)
        self.table.column("crc", width=250)
        self.table.column("opf", width=250)
        self.table.column("estado", width=200)
        
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
    
    def _build_log_panel(self):
        """Panel de log."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=3, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(panel, text="📋 Registro", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=6, pady=(6,2))
        
        self.log_text = ctk.CTkTextbox(panel, height=80, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Listo para comenzar.")
    
    def _setup_table_style(self):
        """Configura estilo de tabla."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=26)
        style.configure("Dark.Treeview.Heading", background="#3b3b3b", foreground="white", borderwidth=1)
        style.map("Dark.Treeview", background=[("selected", "#1f6feb")], foreground=[("selected", "white")])
    
    def _log(self, level: str, message: str):
        """Agrega mensaje al log."""
        colors = {
            "INFO": "#7f8c8d",
            "SUCCESS": "#27ae60",
            "WARNING": "#f39c12",
            "ERROR": "#e74c3c"
        }
        
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{level}] {message}\n")
        
        last_line = self.log_text.index("end-2l")
        self.log_text.tag_add(level, last_line, "end-1c")
        self.log_text.tag_config(level, foreground=colors.get(level, "white"))
        
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update()
    
    def _select_folder(self):
        """Selecciona carpeta."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            self.folder_path = folder
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self._log("INFO", f"Carpeta: {folder}")
    
    def _import_excel(self):
        """Importa documentos desde Excel."""
        path = filedialog.askopenfilename(title="Seleccionar Excel", filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        
        try:
            wb = load_workbook(path, read_only=True, data_only=True)
            ws = wb.active
            
            docs = []
            for row in ws.iter_rows(min_row=1, values_only=True):
                for cell in row:
                    if cell:
                        doc = str(cell).strip()
                        if doc:
                            docs.append(doc)
            
            wb.close()
            
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", "\n".join(docs))
            
            self._log("SUCCESS", f"Importados {len(docs)} documentos.")
            
        except Exception as e:
            self._log("ERROR", f"Error importando: {e}")
    
    def _verify(self):
        """Ejecuta verificación."""
        if not self.folder_path:
            self._log("WARNING", "Selecciona una carpeta.")
            return
        
        # Limpiar tabla
        for item in self.table.get_children():
            self.table.delete(item)
        
        # Obtener documentos de input
        input_text = self.input_text.get("1.0", "end").strip()
        input_docs = [line.strip() for line in input_text.splitlines() if line.strip()]
        
        # Clasificar archivos
        self._log("INFO", "Clasificando archivos...")
        files = classify_files(self.folder_path)
        
        self._log("INFO", f"CRC: {len(files['CRC'])}, OPF: {len(files['OPF'])}, Otros: {len(files['OTHER'])}")
        
        # Log de archivos encontrados
        for filename, doc in files['CRC'][:5]:
            self._log("INFO", f"CRC: {filename} → {doc}")
        
        # Verificar
        self._log("INFO", "Verificando...")
        results = verify_documents(input_docs, files['CRC'], files['OPF'])
        
        # Mostrar resultados
        for r in results:
            self.table.insert("", "end", values=(
                r['documento'],
                r['crc_archivo'],
                r['opf_archivo'],
                r['estado']
            ))
        
        self.count_lbl.configure(text=f"{len(results)} registros")
        self._log("SUCCESS", f"✅ {len(results)} registros.")
    
    def _export_csv(self):
        """Exporta a CSV."""
        if not self.table.get_children():
            self._log("WARNING", "Sin resultados.")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Documento", "Archivo CRC", "Archivo OPF", "Estado"])
                
                for item in self.table.get_children():
                    writer.writerow(self.table.item(item, "values"))
            
            self._log("SUCCESS", f"✅ Exportado: {path}")
            
        except Exception as e:
            self._log("ERROR", f"Error: {e}")
    
    def _clear(self):
        """Limpia datos."""
        self.input_text.delete("1.0", "end")
        for item in self.table.get_children():
            self.table.delete(item)
        self.count_lbl.configure(text="0 registros")
        self._log("INFO", "Limpiado.")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Verificador CRC/OPF")
    root.geometry("1000x750")
    root.minsize(900, 650)
    app = PDFVerifierApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()