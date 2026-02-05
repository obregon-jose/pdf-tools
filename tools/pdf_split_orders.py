import os
import re
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from typing import Optional, List, Dict, Tuple


# ==================== TEXTBOX CON PLACEHOLDER ====================

class CTkTextboxWithPlaceholder(ctk.CTkTextbox):
    """CTkTextbox con soporte para placeholder text."""
    
    def __init__(self, master, placeholder_text="", placeholder_color="gray50", **kwargs):
        super().__init__(master, **kwargs)
        
        self.placeholder_text = placeholder_text
        self.placeholder_color = placeholder_color
        self.default_color = self._text_color
        self.is_placeholder_active = False
        
        self._show_placeholder()
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Key>", self._on_key_press)
    
    def _show_placeholder(self):
        self.delete("1.0", "end")
        self.insert("1.0", self.placeholder_text)
        self.configure(text_color=self.placeholder_color)
        self.is_placeholder_active = True
    
    def _hide_placeholder(self):
        if self.is_placeholder_active:
            self.delete("1.0", "end")
            self.configure(text_color=self.default_color)
            self.is_placeholder_active = False
    
    def _on_click(self, event=None):
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def _on_focus_in(self, event=None):
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def _on_focus_out(self, event=None):
        content = self.get("1.0", "end").strip()
        if not content:
            self._show_placeholder()
    
    def _on_key_press(self, event=None):
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def get_content(self) -> str:
        if self.is_placeholder_active:
            return ""
        return self.get("1.0", "end").strip()
    
    def clear(self):
        self.is_placeholder_active = False
        self.delete("1.0", "end")
        self._show_placeholder()


# ==================== UTILIDADES ====================

def clean_filename(name: str) -> str:
    """Elimina caracteres no permitidos en nombres de archivo."""
    return re.sub(r'[\\/*?:"<>|]', "", name)


def create_unique_path(base_path: str) -> str:
    """Crea una ruta única si el archivo ya existe."""
    if not os.path.exists(base_path):
        return base_path
    
    base, ext = os.path.splitext(base_path)
    counter = 2
    
    while True:
        new_path = f"{base} ({counter}){ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def parse_names_input(text: str) -> Tuple[List[str], int]:
    """
    Parsea el input de nombres soportando dos formatos:
    1. Un nombre por línea (formato clásico)
    2. Nombre*cantidad (formato compacto)
    
    Retorna: (lista_expandida, total_páginas)
    """
    if not text:
        return [], 0
    
    expanded_names = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Buscar patrón: NOMBRE*CANTIDAD
        match = re.match(r'^(.+?)\s*\*\s*(\d+)$', line)
        
        if match:
            # Formato compacto: CC123*3
            name = match.group(1).strip()
            count = int(match.group(2))
            expanded_names.extend([name] * count)
        else:
            # Formato clásico: una línea = una página
            expanded_names.append(line)
    
    return expanded_names, len(expanded_names)


# ==================== APLICACIÓN PRINCIPAL ====================

class PDFSplitOrdersApp(ctk.CTkFrame):
    """Aplicación para dividir un PDF y renombrar cada página."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        self.pdf_path: Optional[str] = None
        self.last_operation: Optional[Dict] = None
        self.page_count = 0
        self._pdf_check_after_id = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_top_panel()
        self._build_names_panel()
        self._build_log_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # PDF
        ctk.CTkLabel(panel, text="PDF:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.pdf_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona o escribe la ruta del PDF")
        self.pdf_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        # Bindings para detectar cambios
        self.pdf_entry.bind("<KeyRelease>", self._on_pdf_path_change)
        self.pdf_entry.bind("<FocusOut>", self._on_pdf_path_change)
        self.pdf_entry.bind("<Return>", self._on_pdf_path_change)
        
        ctk.CTkButton(panel, text="Seleccionar", width=120, command=self._on_select_pdf).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Salida
        ctk.CTkLabel(panel, text="Salida:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=(6,4), pady=4, sticky="w")
        self.output_entry = ctk.CTkEntry(panel, placeholder_text="Carpeta de salida (opcional)")
        self.output_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar", width=120, command=self._on_select_output).grid(row=1, column=2, padx=(4,6), pady=4)
        
        # Prefijo
        ctk.CTkLabel(panel, text="Prefijo:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=(6,4), pady=4, sticky="w")
        self.prefix_entry = ctk.CTkEntry(panel, placeholder_text="Prefijo para archivos")
        self.prefix_entry.grid(row=2, column=1, columnspan=2, padx=4, pady=4, sticky="ew")
        self.prefix_entry.insert(0, "OPF_900895359_IPSP_")
        
        # Botones
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.process_btn = ctk.CTkButton(btn_frame, text="✂️ Dividir PDF", command=self._on_process, fg_color="#1f6feb")
        self.process_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.undo_btn = ctk.CTkButton(btn_frame, text="↶ Deshacer", command=self._on_undo, fg_color="#f0ad4e", text_color="black", state="disabled")
        self.undo_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._on_clear, fg_color="#e74c3c")
        self.clear_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    
    def _build_names_panel(self):
        """Panel de nombres."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6,4))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header,
            text="📝 Nombres (formato: CC123 o CC123*3 para repetir)",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.counter_lbl = ctk.CTkLabel(header, text="0 nombres | 0 páginas", text_color="gray", anchor="e")
        self.counter_lbl.grid(row=0, column=1, sticky="e")
        
        # Textbox
        placeholder = (
            "Formato 1 - Un nombre por línea:\n"
            "CC1234567890\n"
            "TI9876543210\n"
            "CC1234567890\n\n"
            "Formato 2 - Con multiplicador:\n"
            "CC1234567890*3\n"
            "TI9876543210*2\n"
            "RC1122334455"
        )
        
        self.names_textbox = CTkTextboxWithPlaceholder(
            panel,
            placeholder_text=placeholder,
            placeholder_color="gray50",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.names_textbox.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        self.names_textbox.bind("<KeyRelease>", self._update_counter)
    
    def _build_log_panel(self):
        """Panel de log."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(panel, text="📋 Registro", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=6, pady=(6,2))
        
        self.log_text = ctk.CTkTextbox(panel, height=90, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Listo. Soporta formatos: CC123 o CC123*3")
    
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
    
    def _on_pdf_path_change(self, event=None):
        """Detecta cambios en el input del PDF y actualiza automáticamente."""
        # Cancelar timer anterior si existe
        if self._pdf_check_after_id:
            try:
                self.after_cancel(self._pdf_check_after_id)
            except:
                pass
        
        # Programar verificación después de 500ms de inactividad
        self._pdf_check_after_id = self.after(500, self._check_pdf_path)
    
    def _check_pdf_path(self):
        """Verifica y carga info del PDF desde el input."""
        self._pdf_check_after_id = None
        path = self.pdf_entry.get().strip()
        
        if not path:
            self.page_count = 0
            self._update_counter()
            return
        
        # Expandir ruta si es relativa
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.expanduser(path))
        
        # Verificar si cambió la ruta
        if path == self.pdf_path:
            return
        
        # Verificar si existe y es PDF
        if os.path.exists(path) and path.lower().endswith('.pdf'):
            self.pdf_path = path
            self._load_pdf_info()
            
            # Auto-llenar carpeta de salida si está vacía
            if not self.output_entry.get().strip():
                self.output_entry.delete(0, "end")
                self.output_entry.insert(0, os.path.dirname(path))
        else:
            # Resetear si la ruta no es válida
            if self.pdf_path != path:
                self.page_count = 0
                self._update_counter()
    
    def _on_select_pdf(self):
        """Selecciona PDF mediante diálogo."""
        path = filedialog.askopenfilename(title="Seleccionar PDF", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        
        self.pdf_path = path
        self.pdf_entry.delete(0, "end")
        self.pdf_entry.insert(0, path)
        
        if not self.output_entry.get().strip():
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, os.path.dirname(path))
        
        self._load_pdf_info()
    
    def _load_pdf_info(self):
        """Carga info del PDF."""
        try:
            doc = fitz.open(self.pdf_path)
            self.page_count = doc.page_count
            file_size = os.path.getsize(self.pdf_path) / (1024 * 1024)
            doc.close()
            
            self._log("INFO", f"PDF: {os.path.basename(self.pdf_path)} ({self.page_count} págs, {file_size:.2f} MB)")
            self._update_counter()
            
        except Exception as e:
            self._log("ERROR", f"Error leyendo PDF: {e}")
            self.page_count = 0
            self._update_counter()
    
    def _on_select_output(self):
        """Selecciona carpeta."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta")
        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)
    
    def _on_clear(self):
        """Limpia nombres."""
        self.names_textbox.clear()
        self._update_counter()
        self._log("INFO", "Nombres limpiados.")
    
    def _update_counter(self, event=None):
        """Actualiza contador."""
        text = self.names_textbox.get_content()
        _, total_names = parse_names_input(text)
        
        if self.page_count > 0:
            if total_names == self.page_count:
                self.counter_lbl.configure(text=f"✓ {total_names} nombres | {self.page_count} páginas", text_color="green")
            elif total_names > self.page_count:
                self.counter_lbl.configure(text=f"❌ {total_names} nombres | {self.page_count} páginas (sobran)", text_color="red")
            else:
                self.counter_lbl.configure(text=f"⚠️ {total_names} nombres | {self.page_count} páginas (faltan)", text_color="orange")
        else:
            self.counter_lbl.configure(text=f"{total_names} nombres | 0 páginas", text_color="gray")
    
    def _on_process(self):
        """Procesa el PDF."""
        pdf_path = self.pdf_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        prefix = self.prefix_entry.get().strip()
        
        if not pdf_path or not os.path.exists(pdf_path):
            self._log("ERROR", "Selecciona un PDF válido.")
            return
        
        text = self.names_textbox.get_content()
        names, total_names = parse_names_input(text)
        
        if not names:
            self._log("ERROR", "Ingresa nombres.")
            return
        
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        
        # Verificar cantidad
        try:
            doc = fitz.open(pdf_path)
            num_pages = doc.page_count
            doc.close()
        except Exception as e:
            self._log("ERROR", f"Error abriendo PDF: {e}")
            return
        
        if len(names) != num_pages:
            self._log("ERROR", f"Nombres ({len(names)}) ≠ Páginas ({num_pages})")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        self._log("INFO", f"Dividiendo PDF en {num_pages} archivos...")
        
        try:
            doc = fitz.open(pdf_path)
            created_files = []
            
            for i, name in enumerate(names):
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                
                clean_name = clean_filename(name)
                file_name = f"{prefix}{clean_name}.pdf"
                file_path = os.path.join(output_dir, file_name)
                file_path = create_unique_path(file_path)
                
                new_doc.save(file_path, garbage=4, deflate=True)
                new_doc.close()
                created_files.append(file_path)
                
                if (i + 1) % 10 == 0 or i == num_pages - 1:
                    self._log("SUCCESS", f"Procesados [{i+1}/{num_pages}]")
            
            doc.close()
            
            # Eliminar original
            removed = False
            try:
                os.remove(pdf_path)
                removed = True
                self._log("WARNING", f"Original eliminado: {os.path.basename(pdf_path)}")
            except:
                pass
            
            self.last_operation = {
                'original_path': pdf_path,
                'original_removed': removed,
                'created_files': created_files.copy()
            }
            self.undo_btn.configure(state="normal")
            
            self._log("SUCCESS", f"✅ Completado: {len(created_files)} archivos")
            
        except Exception as e:
            self._log("ERROR", f"Error: {e}")
    
    def _on_undo(self):
        """Deshace operación."""
        if not self.last_operation:
            self._log("WARNING", "Sin operación para deshacer.")
            return
        
        created_files = self.last_operation.get('created_files', [])
        original_path = self.last_operation.get('original_path')
        original_removed = self.last_operation.get('original_removed', False)
        
        if not created_files:
            self._log("WARNING", "Sin archivos para eliminar.")
            self.last_operation = None
            self.undo_btn.configure(state="disabled")
            return
        
        self._log("INFO", "Deshaciendo...")
        
        try:
            # Restaurar original si fue eliminado
            if original_removed and created_files:
                merged_doc = fitz.open()
                for file_path in created_files:
                    if os.path.exists(file_path):
                        src = fitz.open(file_path)
                        merged_doc.insert_pdf(src)
                        src.close()
                
                merged_doc.save(original_path, garbage=4, deflate=True)
                merged_doc.close()
                self._log("SUCCESS", f"Original restaurado: {os.path.basename(original_path)}")
            
            # Eliminar archivos creados
            deleted = 0
            for file_path in created_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted += 1
                    except:
                        pass
            
            self._log("SUCCESS", f"✅ Eliminados {deleted} archivos")
            
            self.last_operation = None
            self.undo_btn.configure(state="disabled")
            
            # Restaurar path en el entry
            self.pdf_entry.delete(0, "end")
            self.pdf_entry.insert(0, original_path)
            self.pdf_path = original_path
            self._load_pdf_info()
            
        except Exception as e:
            self._log("ERROR", f"Error al deshacer: {e}")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("PDF Split & Rename")
    root.geometry("800x700")
    root.minsize(700, 600)
    app = PDFSplitOrdersApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()