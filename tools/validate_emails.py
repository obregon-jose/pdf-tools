import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import dns.resolver
import pandas as pd
import re
import unicodedata
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from dataclasses import dataclass
from typing import Optional, List
import threading

# ==================== DATACLASS PARA ERRORES ====================
@dataclass
class EmailError:
    """Clase para almacenar información de errores en correos."""
    row: int
    email: str
    error_type: str
    detail:  str = ""


# ==================== CLASE VALIDADOR ====================
class EmailValidator:
    """
    Clase encargada de toda la lógica de validación de correos.
    Valida formato, caracteres y dominios MX.
    """
    
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    EMAIL_COLUMN_NAMES = ['correo', 'email', 'e-mail', 'mail', 'correo electrónico', 'correo electronico']
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Elimina acentos y caracteres especiales Unicode."""
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))
    
    def is_valid_email(self, email: str) -> bool:
        """Valida el formato del correo electrónico."""
        email = email.strip()
        email = self.normalize_text(email)
        if not email or any(ord(c) > 127 for c in email):
            return False
        return self.EMAIL_PATTERN.fullmatch(email) is not None
    
    @lru_cache(maxsize=500)
    def is_valid_domain(self, domain: str) -> bool:
        """Valida que el dominio tenga registros MX válidos (con caché)."""
        try:
            dns.resolver.resolve(domain, 'MX', lifetime=3)
            return True
        except Exception:
            return False
    
    def find_email_column(self, columns: List[str]) -> Optional[str]:
        """Busca automáticamente la columna que contiene correos."""
        columns_lower = [col.lower().strip() for col in columns]
        for name in self.EMAIL_COLUMN_NAMES:
            if name in columns_lower:
                return columns[columns_lower.index(name)]
        return None
    
    def validate_single_email(self, idx: int, email: str) -> Optional[EmailError]:
        """Valida un correo individual y retorna el error si existe."""
        if pd.isna(email):
            return None
        
        email = str(email).strip()
        
        if '@' not in email:
            return EmailError(idx, email, "FORMATO", "Falta el carácter '@'")
        
        user, domain = email.split('@', 1)
        
        if any(ord(c) > 127 for c in user):
            return EmailError(idx, email, "CARACTERES", "Usuario contiene acentos o caracteres no permitidos")
        
        clean_email = self.normalize_text(email)
        
        if not self.is_valid_email(clean_email):
            return EmailError(idx, email, "FORMATO", "Formato de correo inválido")
        
        clean_domain = clean_email.split('@')[1]
        if not self.is_valid_domain(clean_domain):
            return EmailError(idx, email, "DOMINIO", f"Dominio inválido ({clean_domain})")
        
        return None


class ValidateEmailApp(ctk.CTkFrame):
    """
    Aplicación principal con interfaz gráfica moderna.
    Diseño basado en el modelo PDFSplitterApp.
    """
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # Estado de la aplicación
        self.file_path:  Optional[str] = None
        self.validator = EmailValidator()
        self.is_processing = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz siguiendo el diseño del modelo."""
        
        # ===== FRAME SUPERIOR (contenedor único con espaciado compacto) =====
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: Entrada de archivo Excel + botón seleccionar
        lbl_file = ctk.CTkLabel(top_frame, text="Excel:", width=50, anchor="w")
        lbl_file.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.file_entry = ctk.CTkEntry(
            top_frame, 
            placeholder_text="Escribe la ruta del archivo Excel o usa Seleccionar", 
            width=500
        )
        self.file_entry.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        
        btn_select_file = ctk.CTkButton(
            top_frame, 
            text="Seleccionar Excel", 
            width=140, 
            command=self._on_select_file
        )
        btn_select_file.grid(row=0, column=2, padx=(0, 6), pady=4)
        
        # Fila 2: Espaciador pequeño
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=2, column=0, columnspan=3)
        
        # Fila 3: Botones de acción (Validar, Revisar mismo archivo, Limpiar)
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        
        self.validate_button = ctk.CTkButton(
            btn_frame, 
            text="Validar Correos", 
            command=self._on_validate,
            fg_color="#1f6feb"  # Azul del modelo
        )
        self.validate_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self.review_button = ctk.CTkButton(
            btn_frame, 
            text="Revisar Mismo Archivo", 
            command=self._on_review_same_file,
            fg_color="#f0ad4e",  # Amarillo/naranja del modelo
            text_color="black"
        )
        self.review_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        self.review_button.configure(state="disabled")
        
        self.clear_button = ctk.CTkButton(
            btn_frame, 
            text="Limpiar Resultados", 
            command=self._on_clear_results
        )
        self.clear_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE RESULTADOS (sin título, márgenes compactos) =====
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame. pack(fill="both", expand=True, padx=6, pady=6)
        
        # Nota informativa
        # self.info_note = ctk.CTkLabel(
        #     self.results_frame,
        #     text="Nota: El validador detectará automáticamente la columna de correos (correo, email, mail, etc. )",
        #     text_color="gray",
        #     font=("Arial", 12, "bold")
        # )
        # self.info_note.grid(row=0, column=0, sticky="w", padx=4, pady=(2, 4))
        
        # Área de texto para resultados con scroll
        self.results_textbox = ctk.CTkTextbox(
            self.results_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
            wrap="word"
        )
        self.results_textbox.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        
        self.results_frame.grid_rowconfigure(1, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        # ===== FRAME INFERIOR (Estado y Progreso) =====
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=6, pady=6)
        
        # Barra de progreso
        self.progressbar = ctk.CTkProgressBar(bottom_frame, height=12, corner_radius=5)
        self.progressbar. pack(fill="x", padx=6, pady=(6, 2))
        self.progressbar.set(0)
        
        # Etiqueta de estado
        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="⏳ Esperando archivo...",
            text_color="gray",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=6, pady=(2, 6))
    
    # ==================== MANEJADORES DE EVENTOS ====================
    
    def _on_select_file(self):
        """Abre diálogo para seleccionar archivo Excel."""
        if self.is_processing:
            messagebox. showwarning("Procesando", "Espera a que termine el proceso actual.")
            return
        
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[
                ("Archivos Excel", "*.xlsx *.xls"),
                ("Excel moderno", "*.xlsx"),
                ("Excel antiguo", "*.xls")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            self. file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self.info_label.configure(
                text=f"📁 {os.path.basename(file_path)}",
                text_color="white"
            )
            self.review_button.configure(state="normal")
    
    def _on_validate(self):
        """Inicia la validación del archivo seleccionado o escrito."""
        if self.is_processing:
            messagebox.showwarning("Procesando", "Espera a que termine el proceso actual.")
            return
        
        # Obtener ruta del entry o del estado
        file_path = self. file_entry.get().strip() or self.file_path
        
        if not file_path: 
            messagebox.showerror("Error", "No se ha seleccionado ni indicado un archivo Excel.")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "La ruta del archivo no existe.")
            return
        
        self.file_path = file_path
        self.review_button.configure(state="normal")
        self._process_file_async()
    
    def _on_review_same_file(self):
        """Vuelve a procesar el último archivo cargado."""
        if self. is_processing:
            messagebox.showwarning("Procesando", "Espera a que termine el proceso actual.")
            return
        
        if not self.file_path:
            messagebox. showinfo("Sin archivo", "Primero debes cargar un archivo Excel.")
            return
        
        if not os.path.exists(self.file_path):
            messagebox.showerror("Archivo no encontrado", "El archivo original ya no existe.")
            self.file_path = None
            self.review_button.configure(state="disabled")
            return
        
        self._process_file_async()
    
    def _on_clear_results(self):
        """Limpia el área de resultados."""
        self.results_textbox.delete("1.0", "end")
        self.progressbar.set(0)
        self.status_label.configure(text="⏳ Esperando archivo...", text_color="gray")
        messagebox.showinfo("Limpiar", "Se han limpiado los resultados de la validación.")
    
    # ==================== PROCESAMIENTO ====================
    
    def _process_file_async(self):
        """Inicia el procesamiento en un hilo separado."""
        self.is_processing = True
        self. validate_button.configure(state="disabled")
        self.review_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        
        thread = threading.Thread(target=self._process_file, daemon=True)
        thread.start()
    
    def _update_ui(self, func):
        """Ejecuta una función en el hilo principal de la UI."""
        self.after(0, func)
    
    def _process_file(self):
        """Procesa el archivo Excel con validación paralela."""
        
        def clean_and_start():
            self.results_textbox.delete("1.0", "end")
            self.progressbar.set(0)
            self.status_label. configure(text="⏳ Procesando.. .", text_color="orange")
        
        self._update_ui(clean_and_start)
        
        # Leer archivo Excel
        try:
            df = pd.read_excel(self.file_path, engine='openpyxl')
        except Exception as e:
            def show_error():
                self.results_textbox.insert("end", f"❌ Error al leer el archivo:\n{str(e)}\n")
                self.status_label.configure(text="⚠️ Error al leer el archivo", text_color="red")
                self._restore_buttons()
            self._update_ui(show_error)
            return
        
        # Buscar columna de correos
        email_column = self.validator.find_email_column(df.columns. tolist())
        if not email_column:
            def show_column_error():
                self.results_textbox.insert("end", "❌ No se encontró una columna de correos.\n")
                self.results_textbox.insert("end", f"\nColumnas disponibles:  {', '.join(df.columns.tolist())}\n")
                self.results_textbox.insert("end", "\n💡 Tip: Renombra la columna a 'correo', 'email' o 'mail'\n")
                self.status_label.configure(text="⚠️ Columna de correos no encontrada", text_color="red")
                self._restore_buttons()
            self._update_ui(show_column_error)
            return
        
        # Preparar datos
        emails = df[email_column].tolist()
        total = len(emails)
        errors:  List[EmailError] = []
        
        def show_start():
            self.results_textbox.insert("end", f"📄 Archivo:  {os.path.basename(self.file_path)}\n")
            # self.results_textbox.insert("end", f"📊 Total de registros: {total}\n")
            self.results_textbox.insert("end", "─" * 60 + "\n")
            self.results_textbox.insert("end", "🔍 Validando correos...\n\n")
        
        self._update_ui(show_start)
        
        # Validación paralela
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self.validator.validate_single_email, idx + 2, email): idx
                for idx, email in enumerate(emails)
            }
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                
                if result:
                    errors.append(result)
                    error = result
                    
                    def show_error(e=error):
                        icon = "❌" if e.error_type == "FORMATO" else "⚠️" if e.error_type == "DOMINIO" else "🚫"
                        self.results_textbox.insert("end", f"Fila {e.row}: '{e.email}' {icon} {e.detail}\n")
                        self. results_textbox.see("end")
                    
                    self._update_ui(show_error)
                
                progress = completed / total
                
                def update_progress(p=progress, c=completed, t=total):
                    self.progressbar.set(p)
                    self.status_label.configure(text=f"⏳ Procesando... {c}/{t} ({int(p*100)}%)")
                
                self._update_ui(update_progress)
        
        # Resumen final
        total_errors = len(errors)
        
        def show_summary():
            self.results_textbox.insert("end", "\n" + "═" * 60 + "\n")
            self.results_textbox.insert("end", "📊 RESUMEN DE VALIDACIÓN\n")
            self.results_textbox.insert("end", "═" * 60 + "\n\n")
            
            if total_errors == 0:
                self.results_textbox.insert("end", "✅ ¡EXCELENTE! Todos los correos son válidos.\n")
                self.status_label.configure(text="✅ Validación completada sin errores", text_color="green")
            else:
                format_errors = sum(1 for e in errors if e.error_type == "FORMATO")
                domain_errors = sum(1 for e in errors if e.error_type == "DOMINIO")
                char_errors = sum(1 for e in errors if e.error_type == "CARACTERES")
                
                self. results_textbox.insert("end", f"⚠️ Total de errores: {total_errors}\n\n")
                self.results_textbox.insert("end", f"   📝 Errores de formato: {format_errors}\n")
                self.results_textbox.insert("end", f"   🌐 Dominios inválidos: {domain_errors}\n")
                self.results_textbox.insert("end", f"   🔤 Caracteres inválidos: {char_errors}\n")
                self.results_textbox.insert("end", f"\n   ✅ Correos válidos:  {total - total_errors}/{total}\n")
                
                self.status_label.configure(
                    text=f"⚠️ {total_errors} errores de {total} correos",
                    text_color="orange"
                )
            
            self. results_textbox.see("end")
            self. progressbar.set(1)
            self._restore_buttons()
        
        self._update_ui(show_summary)
    
    def _restore_buttons(self):
        """Restaura el estado de los botones después del procesamiento."""
        self.is_processing = False
        self. validate_button.configure(state="normal")
        self.review_button.configure(state="normal")
        self.clear_button. configure(state="normal")
