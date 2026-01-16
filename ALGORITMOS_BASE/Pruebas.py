import os
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict


# ==================== CONFIGURACIÓN ====================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PDFMultiplierApp(ctk.CTkFrame):
    """
    Aplicación para multiplicar un PDF con diferentes nombres. 
    Diseño basado en el modelo PDFSplitterApp. 
    """
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # ===== ESTADO DE LA APLICACIÓN =====
        self.pdf_path: Optional[str] = None
        self.last_operation: Optional[Dict] = None  # Para deshacer
        
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
            placeholder_text="Selecciona el archivo PDF a multiplicar",
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
        
        # Fila 1: Carpeta de salida
        lbl_output = ctk.CTkLabel(top_frame, text="Salida:", width=60, anchor="w")
        lbl_output.grid(row=1, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.output_entry = ctk. CTkEntry(
            top_frame,
            placeholder_text="Carpeta de salida (opcional, usa la del PDF)",
            width=500
        )
        self.output_entry.grid(row=1, column=1, padx=(0, 6), pady=4, sticky="we")
        
        btn_select_output = ctk. CTkButton(
            top_frame,
            text="Seleccionar Carpeta",
            width=140,
            command=self._on_select_output
        )
        btn_select_output.grid(row=1, column=2, padx=(0, 6), pady=4)
        
        # Fila 2: Prefijo
        lbl_prefix = ctk. CTkLabel(top_frame, text="Prefijo:", width=60, anchor="w")
        lbl_prefix.grid(row=2, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.prefix_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Prefijo para los archivos (ej: CRC_900895359_IPSP)",
            width=500
        )
        self.prefix_entry.grid(row=2, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="we")
        self.prefix_entry.insert(0, "CRC_900895359_IPSP")
        
        # Fila 3: Espaciador
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=3, column=0, columnspan=3)
        
        # Fila 4: Botones de acción
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        
        self.multiply_button = ctk.CTkButton(
            btn_frame,
            text="📄 Generar Multiplicados",
            command=self._on_multiply,
            fg_color="#1f6feb"
        )
        self.multiply_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
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
            text="🧹 Limpiar",
            command=self._on_clear
        )
        self.clear_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE DOCUMENTOS =====
        self.docs_frame = ctk.CTkFrame(self)
        self.docs_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Nota informativa
        self.info_note = ctk.CTkLabel(
            self.docs_frame,
            text="Nota:  Ingresa los identificadores de documento (máx. 10). Uno por línea.  El PDF se copiará con cada nombre.",
            text_color="gray",
            font=("Arial", 12, "bold")
        )
        self.info_note.pack(anchor="w", padx=4, pady=(2, 4))
        
        # Área de texto para documentos
        self.docs_textbox = ctk.CTkTextbox(
            self.docs_frame,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.docs_textbox.pack(fill="both", expand=True, padx=4, pady=2)
        
        # Ejemplo placeholder
        self.docs_textbox.insert("1.0", "# Ejemplo:\n1001234567\n1009876543\n52123456")
    
    # ==================== EVENTOS ====================
    
    def _on_select_pdf(self):
        """Selecciona el archivo PDF."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*. pdf")]
        )
        
        if file_path:
            self.pdf_path = file_path
            self. pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, file_path)
            
            # Auto-llenar carpeta de salida
            if not self.output_entry.get().strip():
                output_dir = os.path.dirname(file_path)
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, output_dir)
    
    def _on_select_output(self):
        """Selecciona la carpeta de salida."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_entry.delete(0, tk. END)
            self.output_entry.insert(0, folder)
    
    def _on_clear(self):
        """Limpia todos los campos."""
        self.docs_textbox.delete("1.0", "end")
        messagebox.showinfo("Limpiar", "Se ha limpiado el listado de documentos.")
    
    # ==================== OPERACIONES ====================
    
    def _get_document_list(self) -> List[str]:
        """Obtiene la lista de documentos del textbox."""
        text = self.docs_textbox. get("1.0", "end").strip()
        lines = text.split('\n')
        
        # Filtrar líneas vacías y comentarios
        documents = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                documents.append(line)
        
        return documents
    
    def _create_unique_filename(self, base_path: str) -> str:
        """Crea un nombre de archivo único si ya existe."""
        if not os.path.exists(base_path):
            return base_path
        
        base, ext = os.path.splitext(base_path)
        counter = 1
        while True:
            new_path = f"{base} ({counter}){ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    def _on_multiply(self):
        """Genera los PDFs multiplicados."""
        # Obtener ruta del PDF
        pdf_path = self.pdf_entry.get().strip() or self.pdf_path
        
        if not pdf_path: 
            messagebox.showerror("Error", "No se ha seleccionado un archivo PDF.")
            return
        
        if not os.path.exists(pdf_path):
            messagebox.showerror("Error", f"El archivo no existe:\n{pdf_path}")
            return
        
        # Obtener prefijo
        prefix = self.prefix_entry.get().strip()
        if not prefix:
            messagebox. showerror("Error", "Por favor, ingresa un prefijo.")
            return
        
        # Obtener lista de documentos
        documents = self._get_document_list()
        
        if not documents:
            messagebox.showerror("Error", "No se han ingresado documentos válidos.")
            return
        
        if len(documents) > 10:
            messagebox.showerror("Error", "El número máximo de documentos es 10.")
            return
        
        # Obtener carpeta de salida
        output_dir = self.output_entry. get().strip()
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        
        # Crear carpeta si no existe
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la carpeta:\n{e}")
                return
        
        # Confirmar operación
        response = messagebox.askyesno(
            "Confirmar",
            f"¿Generar {len(documents)} copias del PDF?\n\n"
            f"Prefijo: {prefix}\n"
            f"Carpeta:  {output_dir}"
        )
        
        if not response:
            return
        
        try:
            # Abrir PDF original
            doc = fitz.open(pdf_path)
            
            created_files = []
            
            for document in documents:
                # Generar nombre del archivo
                file_name = f"{prefix}_{document}.pdf"
                file_path = os.path.join(output_dir, file_name)
                
                # Evitar sobrescribir
                file_path = self._create_unique_filename(file_path)
                
                # Crear copia del PDF
                new_pdf = fitz.open()
                new_pdf.insert_pdf(doc)
                new_pdf. save(file_path, garbage=4, deflate=True)
                new_pdf.close()
                
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
                'created_files': created_files. copy(),
                'documents': documents. copy()
            }
            self. undo_button.configure(state="normal")
            
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
            self.undo_button.configure(state="disabled")
            return
        
        # Confirmar
        msg = f"¿Eliminar {len(created_files)} archivos creados?"
        if original_removed: 
            msg += "\n\n⚠️ El archivo original fue eliminado y se reconstruirá desde una de las copias."
        
        response = messagebox.askyesno("Confirmar Deshacer", msg)
        
        if not response:
            return
        
        try:
            # Si el original fue eliminado, restaurarlo desde la primera copia
            if original_removed and created_files:
                first_copy = created_files[0]
                if os.path.exists(first_copy):
                    try:
                        # Copiar la primera copia como el original
                        doc = fitz.open(first_copy)
                        doc.save(original_path, garbage=4, deflate=True)
                        doc.close()
                        print(f"[INFO] Original restaurado: {original_path}")
                    except Exception as e:
                        print(f"[WARN] No se pudo restaurar el original: {e}")
            
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


# ==================== PUNTO DE ENTRADA ====================
if __name__ == "__main__": 
    root = ctk.CTk()
    root.title("📄 Multiplicar Soportes PDF")
    root.geometry("850x550")
    root.minsize(750, 450)
    
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    
    app = PDFMultiplierApp(root)
    app.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    root.mainloop()