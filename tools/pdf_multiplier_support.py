import os
import re
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict


# ==================== CONSTANTES ====================

MAX_NOMBRES = 10  # Límite máximo de nombres permitidos


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
    
    def _show_placeholder(self):
        """Muestra el texto placeholder."""
        self.delete("1.0", "end")
        self.insert("1.0", self.placeholder_text)
        self.configure(text_color=self.placeholder_color)
        self.is_placeholder_active = True
    
    def _hide_placeholder(self):
        """Oculta el texto placeholder."""
        if self.is_placeholder_active:
            self.delete("1.0", "end")
            self.configure(text_color=self.default_color)
            self.is_placeholder_active = False
    
    def _on_focus_in(self, event=None):
        """Evento al enfocar el textbox."""
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def _on_focus_out(self, event=None):
        """Evento al desenfocar el textbox."""
        content = self.get("1.0", "end").strip()
        if not content:
            self._show_placeholder()
    
    def get_content(self) -> str:
        """Obtiene el contenido real (sin placeholder)."""
        if self.is_placeholder_active:
            return ""
        return self.get("1.0", "end").strip()
    
    def clear(self):
        """Limpia el contenido y muestra el placeholder."""
        self. delete("1.0", "end")
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


# ==================== APLICACIÓN PRINCIPAL ====================

class PDFMultiplierSupportApp(ctk.CTkFrame):
    """
    Aplicación para multiplicar un PDF de 1 página con diferentes nombres.
    Recibe un PDF de una página y lo duplica con cada nombre proporcionado.
    Máximo 10 nombres permitidos. 
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
            placeholder_text="Selecciona el archivo PDF de 1 página",
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
        lbl_output.grid(row=2, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.output_entry = ctk.CTkEntry(
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
        lbl_prefix = ctk.CTkLabel(top_frame, text="Prefijo:", width=60, anchor="w")
        lbl_prefix.grid(row=3, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.prefix_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Prefijo para los archivos",
            width=500
        )
        self.prefix_entry.grid(row=3, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="we")
        self.prefix_entry.insert(0, "CRC_900895359_IPSP_")
        
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
            text="📄 Multiplicar PDF",
            command=self._on_process,
            fg_color="#1f6feb"
        )
        self.process_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self.undo_button = ctk.CTkButton(
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
        #     text=f"📋 Ingresa hasta {MAX_NOMBRES} nombres (uno por línea). El PDF se duplicará con cada nombre.",
        #     text_color="gray",
        #     font=("Arial", 12, "bold")
        # )
        # self.info_note.pack(side="left")
        
        self.counter_label = ctk. CTkLabel(
            header_frame,
            text=f"0 / {MAX_NOMBRES} nombres",
            text_color="gray"
        )
        self.counter_label.pack(side="right")
        
        # Área de texto con placeholder
        placeholder = (
            f"Ingresa los nombres para duplicar el PDF (máximo {MAX_NOMBRES}):\n\n"
            "Ejemplo:\n"
            "CC1234567890\n"
            "TI0987654321\n"
            "RC1122334455\n\n"
            "Se creará una copia del PDF por cada nombre..."
        )
        
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
            title="Seleccionar archivo PDF (1 página)",
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
        """Carga información del PDF y valida que tenga 1 página."""
        pdf_path = self.pdf_entry.get().strip()
        
        if not pdf_path or not os.path.exists(pdf_path):
            return
        
        try:
            doc = fitz.open(pdf_path)
            self.page_count = doc.page_count
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)
            doc.close()
            
            # Validar que sea de 1 página
            # if self.page_count == 1:
            #     self.info_label.configure(
            #         text=f"✓ {self.page_count} página • {file_size:.2f} MB",
            #         text_color="#10b981"
            #     )
            # else:
            #     self.info_label.configure(
            #         text=f"❌ El PDF tiene {self.page_count} páginas.  Solo se permite 1 página.",
            #         text_color="red"
            #     )
            
            self._update_counter()
            
        except Exception as e:
            self.info_label.configure(
                text=f"❌ Error:  {e}",
                text_color="red"
            )
            self. page_count = 0
    
    def _on_select_output(self):
        """Selecciona la carpeta de salida."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_entry. delete(0, tk.END)
            self.output_entry. insert(0, folder)
    
    def _on_clear(self):
        """Limpia el campo de nombres."""
        self.names_textbox.clear()
        self._update_counter()
        messagebox.showinfo("Limpiar", "Se ha limpiado el listado de nombres.")
    
    def _update_counter(self, event=None):
        """Actualiza el contador de nombres (máximo 10)."""
        names = self._get_names_list()
        names_count = len(names)
        
        # Actualizar color según cantidad
        if names_count == 0:
            color = "gray"
            icon = ""
        elif names_count <= MAX_NOMBRES:
            color = "green"
            icon = "✓ "
        else:
            color = "red"
            icon = "❌ "
        
        self.counter_label.configure(
            text=f"{icon}{names_count} / {MAX_NOMBRES} nombres",
            text_color=color
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
        """Procesa el PDF multiplicándolo por cada nombre."""
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
            messagebox.showerror("Error", "Ingresa al menos un nombre.")
            return
        
        # Validar máximo de nombres
        if len(names) > MAX_NOMBRES:
            messagebox.showerror(
                "Error",
                f"Máximo {MAX_NOMBRES} nombres permitidos.\nActualmente tienes {len(names)} nombres."
            )
            return
        
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        
        # Verificar que el PDF tenga 1 página
        try:
            doc = fitz. open(pdf_path)
            num_pages = doc.page_count
            doc.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{e}")
            return
        
        if num_pages != 1:
            messagebox.showerror(
                "Error",
                f"El PDF debe tener exactamente 1 página.\nEste PDF tiene {num_pages} páginas."
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
            f"¿Crear {len(names)} copias del PDF?\n\n"
            f"Prefijo: {prefix}\n"
            f"Carpeta:  {output_dir}\n\n"
            f"Nombres:\n" + "\n".join(f"  • {n}" for n in names[: 5]) +
            (f"\n  ...  y {len(names) - 5} más" if len(names) > 5 else "")
        )
        
        if not response: 
            return
        
        # Procesar - Multiplicar el PDF
        try:
            doc = fitz.open(pdf_path)
            created_files:  List[str] = []
            
            for name in names:
                # Crear nuevo documento con la única página
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=0, to_page=0)
                
                # Generar nombre del archivo (SIN ESPACIO en la extensión)
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
            
            # Guardar estado para deshacer (NO eliminamos el original)
            self.last_operation = {
                'original_path': pdf_path,
                'original_removed': False,
                'created_files': created_files.copy()
            }
            self.undo_button.configure(state="normal")
            
            # Mensaje de éxito
            messagebox.showinfo(
                "Éxito",
                f"✅ Se han creado {len(created_files)} copias del PDF.\n\n"
                f"El archivo original se mantiene intacto."
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error:\n{e}")
            print(f"[ERROR] {e}")
    
    def _on_undo(self):
        """Deshace la última operación eliminando los archivos creados."""
        if not self.last_operation:
            messagebox.showinfo("Info", "No hay operación para deshacer.")
            return
        
        created_files = self.last_operation. get('created_files', [])
        
        if not created_files: 
            messagebox.showinfo("Info", "No hay archivos para eliminar.")
            self.last_operation = None
            self. undo_button.configure(state="disabled")
            return
        
        # Confirmar
        response = messagebox.askyesno(
            "Confirmar Deshacer",
            f"¿Eliminar {len(created_files)} archivos creados?"
        )
        
        if not response:
            return
        
        try:
            # Eliminar archivos creados
            deleted_count = 0
            for file_path in created_files: 
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"[INFO] Eliminado: {file_path}")
                    except Exception as e: 
                        print(f"[WARN] No se pudo eliminar {file_path}: {e}")
            
            messagebox.showinfo(
                "Deshacer completado",
                f"Se eliminaron {deleted_count} archivos."
            )
            
            self.last_operation = None
            self.undo_button.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo deshacer:\n{e}")
            print(f"[ERROR] Deshacer:  {e}")

