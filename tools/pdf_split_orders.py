import os
import re
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict



# ==================== TEXTBOX CON PLACEHOLDER ====================

class CTkTextboxWithPlaceholder(ctk. CTkTextbox):
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
    
    def _on_focus_in(self, event=None):
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def _on_focus_out(self, event=None):
        content = self.get("1.0", "end").strip()
        if not content:
            self._show_placeholder()
    
    def get_content(self) -> str:
        if self.is_placeholder_active:
            return ""
        return self.get("1.0", "end").strip()
    
    def clear(self):
        self.delete("1.0", "end")
        self._show_placeholder()


# ==================== UTILIDADES ====================

def clean_filename(name: str) -> str:
    """Elimina caracteres no permitidos en nombres de archivo."""
    return re. sub(r'[\\/*? :"<>|]', "", name)


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


# ==================== APLICACIÓN PRINCIPAL ====================

class PDFSplitOrdersApp(ctk.CTkFrame):
    """
    Aplicación para dividir un PDF y renombrar cada página.
    Diseño basado en el modelo PDFSplitterApp. 
    """
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # ===== ESTADO =====
        self.pdf_path:  Optional[str] = None
        self.last_operation: Optional[Dict] = None
        self.page_count = 0
        
        # ===== CONSTRUIR UI =====
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # ===== FRAME SUPERIOR =====
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: PDF de entrada
        lbl_pdf = ctk.CTkLabel(top_frame, text="PDF:", width=60, anchor="w")
        lbl_pdf.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.pdf_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Selecciona el archivo PDF a dividir",
            width=500
        )
        self.pdf_entry.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        
        btn_select_pdf = ctk.CTkButton(
            top_frame,
            text="Seleccionar PDF",
            width=140,
            command=self._on_select_pdf
        )
        btn_select_pdf.grid(row=0, column=2, padx=(0, 6), pady=4)
        
        # Fila 1: Info del PDF
        # lbl_info_title = ctk.CTkLabel(top_frame, text="Info:", width=60, anchor="w")
        # lbl_info_title.grid(row=1, column=0, padx=(6, 4), pady=4, sticky="w")
        
        # self.info_label = ctk.CTkLabel(
        #     top_frame,
        #     text="Ningún archivo seleccionado",
        #     anchor="w",
        #     text_color="gray"
        # )
        # self.info_label. grid(row=1, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="w")
        
        # Fila 2: Carpeta de salida
        lbl_output = ctk.CTkLabel(top_frame, text="Salida:", width=60, anchor="w")
        lbl_output. grid(row=2, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self. output_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Carpeta de salida (opcional, usa la del PDF)",
            width=500
        )
        self.output_entry.grid(row=2, column=1, padx=(0, 6), pady=4, sticky="we")
        
        btn_select_output = ctk. CTkButton(
            top_frame,
            text="Seleccionar Carpeta",
            width=140,
            command=self._on_select_output
        )
        btn_select_output.grid(row=2, column=2, padx=(0, 6), pady=4)
        
        # Fila 3: Prefijo
        lbl_prefix = ctk. CTkLabel(top_frame, text="Prefijo:", width=60, anchor="w")
        lbl_prefix.grid(row=3, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.prefix_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Prefijo para los archivos",
            width=500
        )
        self.prefix_entry.grid(row=3, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="we")
        self.prefix_entry.insert(0, "OPF_900895359_IPSP_")
        
        # Fila 4: Espaciador
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=4, column=0, columnspan=3)
        
        # Fila 5: Botones de acción
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        
        self.process_button = ctk.CTkButton(
            btn_frame,
            text="✂️ Procesar PDF",
            command=self._on_process,
            fg_color="#1f6feb"
        )
        self.process_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self. undo_button = ctk.CTkButton(
            btn_frame,
            text="↶ Deshacer",
            command=self._on_undo,
            fg_color="#f0ad4e",
            text_color="black"
        )
        self.undo_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        self.undo_button.configure(state="disabled")
        
        self.clear_button = ctk.CTkButton(
            btn_frame,
            text="🧹 Limpiar nombres",
            command=self._on_clear
        )
        self.clear_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE NOMBRES =====
        self.names_frame = ctk.CTkFrame(self)
        self.names_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Header con nota y contador
        header_frame = ctk.CTkFrame(self.names_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=4, pady=(2, 4))
        
        # self.info_note = ctk.CTkLabel(
        #     header_frame,
        #     text="Nota: Ingresa un nombre por línea.  La cantidad debe coincidir con las páginas del PDF.",
        #     text_color="gray",
        #     font=("Arial", 12, "bold")
        # )
        # self.info_note.pack(side="left")
        
        self.counter_label = ctk.CTkLabel(
            header_frame,
            text="0 nombres | 0 páginas",
            text_color="gray"
        )
        self.counter_label.pack(side="right")
        
        # Área de texto con placeholder
        placeholder = "Ingresa los nombres de los documentos, uno por línea:\n\nEjemplo:\nCC1234567890\nTI0987654321\nRC1122334455\n\nCada línea corresponde a una página del PDF..."
        
        self.names_textbox = CTkTextboxWithPlaceholder(
            self.names_frame,
            placeholder_text=placeholder,
            placeholder_color="gray50",
            height=250,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.names_textbox.pack(fill="both", expand=True, padx=4, pady=2)
        
        # Binding para actualizar contador
        self.names_textbox.bind("<KeyRelease>", self._update_counter)
    
    # ==================== EVENTOS ====================
    
    def _on_select_pdf(self):
        """Selecciona el archivo PDF."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if file_path:
            self. pdf_path = file_path
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, file_path)
            
            # Auto-llenar carpeta de salida
            if not self.output_entry.get().strip():
                output_dir = os.path.dirname(file_path)
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, output_dir)
            
            self._load_pdf_info()
    
    def _load_pdf_info(self):
        """Carga información del PDF."""
        pdf_path = self.pdf_entry.get().strip()
        
        if not pdf_path or not os.path.exists(pdf_path):
            return
        
        try:
            doc = fitz.open(pdf_path)
            self.page_count = doc.page_count
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)
            doc.close()
            
            self.info_label.configure(
                text=f"✓ {self.page_count} páginas • {file_size:.2f} MB",
                text_color="#10b981"
            )
            self._update_counter()
            
        except Exception as e: 
            self.info_label.configure(
                text=f"❌ Error: {e}",
                text_color="red"
            )
            self. page_count = 0
    
    def _on_select_output(self):
        """Selecciona la carpeta de salida."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
    
    def _on_clear(self):
        """Limpia el campo de nombres."""
        self.names_textbox.clear()
        self._update_counter()
        messagebox.showinfo("Limpiar", "Se ha limpiado el listado de nombres.")
    
    def _update_counter(self, event=None):
        """Actualiza el contador de nombres vs páginas."""
        names = self._get_names_list()
        names_count = len(names)
        
        if self.page_count > 0:
            if names_count == self.page_count:
                self.counter_label.configure(
                    text=f"✓ {names_count} nombres | {self.page_count} páginas",
                    text_color="green"
                )
            elif names_count > self.page_count:
                self.counter_label.configure(
                    text=f"✕ {names_count} nombres | {self.page_count} páginas",
                    text_color="red"
                )
            else:
                self.counter_label.configure(
                    text=f"⚠️ {names_count} nombres | {self.page_count} páginas",
                    text_color="orange"
                )
        else:
            self.counter_label.configure(
                text=f"{names_count} nombres | 0 páginas",
                text_color="gray"
            )
    
    # ==================== OPERACIONES ====================
    
    def _get_names_list(self) -> List[str]:
        """Obtiene la lista de nombres del textbox."""
        text = self.names_textbox. get_content()
        
        if not text:
            return []
        
        lines = text.split('\n')
        return [line.strip() for line in lines if line.strip()]
    
    def _on_process(self):
        """Procesa el PDF."""
        # Obtener datos
        pdf_path = self.pdf_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        prefix = self.prefix_entry.get().strip()
        names = self._get_names_list()
        
        # Validaciones
        if not pdf_path: 
            messagebox.showerror("Error", "Selecciona un archivo PDF.")
            return
        
        if not os.path.exists(pdf_path):
            messagebox.showerror("Error", f"El archivo no existe:\n{pdf_path}")
            return
        
        if not names:
            messagebox.showerror("Error", "Ingresa los nombres de los documentos.")
            return
        
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        
        # Verificar cantidad de nombres
        try:
            doc = fitz.open(pdf_path)
            num_pages = doc.page_count
            doc.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{e}")
            return
        
        if len(names) != num_pages:
            messagebox.showerror(
                "Error",
                f"La cantidad de nombres ({len(names)}) no coincide con las páginas del PDF ({num_pages})."
            )
            return
        
        # Crear carpeta si no existe
        if not os. path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox. showerror("Error", f"No se pudo crear la carpeta:\n{e}")
                return
        
        # Confirmar
        response = messagebox.askyesno(
            "Confirmar",
            f"¿Dividir el PDF en {num_pages} archivos?\n\n"
            f"Prefijo: {prefix}\n"
            f"Carpeta:  {output_dir}"
        )
        
        if not response:
            return
        
        # Procesar
        try:
            doc = fitz.open(pdf_path)
            created_files:  List[str] = []
            
            for i, name in enumerate(names):
                # Crear nuevo documento con una página
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                
                # Generar nombre del archivo
                clean_name = clean_filename(name)
                file_name = f"{prefix}{clean_name}.pdf"
                file_path = os.path.join(output_dir, file_name)
                file_path = create_unique_path(file_path)
                
                # Guardar
                new_doc.save(file_path, garbage=4, deflate=True)
                new_doc.close()
                
                created_files.append(file_path)
                print(f"[INFO] Creado: {file_path}")
            
            doc.close()
            
            # Eliminar archivo original
            original_removed = False
            try:
                os.remove(pdf_path)
                original_removed = True
                print(f"[INFO] Original eliminado: {pdf_path}")
            except Exception as e: 
                print(f"[WARN] No se pudo eliminar el original: {e}")
            
            # Guardar estado para deshacer
            self.last_operation = {
                'original_path': pdf_path,
                'original_removed': original_removed,
                'created_files': created_files. copy()
            }
            self.undo_button.configure(state="normal")
            
            # Mensaje de éxito
            msg = f"Se han creado {len(created_files)} archivos PDF."
            if original_removed:
                msg += "\nEl archivo original ha sido eliminado."
            messagebox.showinfo("Éxito", msg)
            
        except Exception as e: 
            messagebox.showerror("Error", f"Hubo un error:\n{e}")
            print(f"[ERROR] {e}")
    
    def _on_undo(self):
        """Deshace la última operación."""
        if not self.last_operation:
            messagebox.showinfo("Info", "No hay operación para deshacer.")
            return
        
        created_files = self.last_operation. get('created_files', [])
        original_path = self.last_operation.get('original_path')
        original_removed = self. last_operation.get('original_removed', False)
        
        if not created_files:
            messagebox.showinfo("Info", "No hay archivos para eliminar.")
            self.last_operation = None
            self. undo_button.configure(state="disabled")
            return
        
        # Confirmar
        msg = f"¿Eliminar {len(created_files)} archivos creados?"
        if original_removed: 
            msg += "\n\n⚠️ El archivo original fue eliminado y se reconstruirá."
        
        response = messagebox.askyesno("Confirmar Deshacer", msg)
        
        if not response:
            return
        
        try:
            # Si el original fue eliminado, restaurarlo
            if original_removed and created_files:
                try:
                    # Reconstruir el PDF original desde las partes
                    merged_doc = fitz.open()
                    for file_path in created_files:
                        if os.path.exists(file_path):
                            src_doc = fitz.open(file_path)
                            merged_doc.insert_pdf(src_doc)
                            src_doc.close()
                    
                    merged_doc.save(original_path, garbage=4, deflate=True)
                    merged_doc.close()
                    print(f"[INFO] Original restaurado: {original_path}")
                except Exception as e:
                    print(f"[WARN] No se pudo restaurar el original:  {e}")
            
            # Eliminar archivos creados
            deleted_count = 0
            for file_path in created_files:
                if os.path.exists(file_path):
                    try: 
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        print(f"[WARN] No se pudo eliminar {file_path}: {e}")
            
            messagebox.showinfo(
                "Deshacer completado",
                f"Se eliminaron {deleted_count} archivos."
                + ("\nEl archivo original fue restaurado." if original_removed else "")
            )
            
            self.last_operation = None
            self.undo_button.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo deshacer:\n{e}")
            print(f"[ERROR] Deshacer:  {e}")

