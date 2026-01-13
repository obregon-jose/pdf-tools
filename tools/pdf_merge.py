import os
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

class PDFMergerApp(ctk.CTkFrame):
    """
    Aplicación para unir múltiples archivos PDF en uno solo.
    Diseño basado en el modelo PDFSplitterApp.
    Utiliza fitz (PyMuPDF) para el procesamiento de PDFs.
    """
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # ===== ESTADO DE LA APLICACIÓN =====
        self.folder_path = ""
        self.checkbox_items = []          # Lista de tuplas (BooleanVar, filename)
        
        # Historial para deshacer
        self.last_operation = None
        
        # ===== CONSTRUIR UI =====
        self._create_widgets()
    
    # ==================== CONSTRUCCIÓN DE UI ====================
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz siguiendo el diseño del modelo."""
        
        # ===== FRAME SUPERIOR =====
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: Carpeta de entrada + botón seleccionar
        lbl_folder = ctk.CTkLabel(top_frame, text="Carpeta:", width=60, anchor="w")
        lbl_folder.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.folder_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Escribe la ruta de la carpeta o usa Seleccionar",
            width=500
        )
        self.folder_entry.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        self.folder_entry.bind("<Return>", lambda e: self._load_from_entry())
        
        btn_select_folder = ctk.CTkButton(
            top_frame,
            text="Seleccionar Carpeta",
            width=140,
            command=self._on_select_folder
        )
        btn_select_folder.grid(row=0, column=2, padx=(0, 6), pady=4)
        
        # Fila 1: Espaciador
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=1, column=0, columnspan=3)
        
        # Fila 2: Botones de acción
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        btn_frame.grid_columnconfigure(3, weight=1)
        
        self.merge_button = ctk.CTkButton(
            btn_frame,
            text="📑 Unir PDFs",
            command=self._on_merge_pdfs,
            fg_color="#1f6feb"
        )
        self.merge_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self. undo_button = ctk.CTkButton(
            btn_frame,
            text="↶ Deshacer",
            command=self._on_undo,
            fg_color="#f0ad4e",
            text_color="black"
        )
        self.undo_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        self.undo_button.configure(state="disabled")
        
        self.select_all_button = ctk. CTkButton(
            btn_frame,
            text="✓ Seleccionar todos",
            command=self._on_select_all
        )
        self.select_all_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        self.deselect_all_button = ctk.CTkButton(
            btn_frame,
            text="✗ Deseleccionar todos",
            command=self._on_deselect_all
        )
        self.deselect_all_button. grid(row=0, column=3, padx=6, pady=4, sticky="we")
        
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE ARCHIVOS PDF =====
        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Nota informativa
        self.info_note = ctk.CTkLabel(
            self.files_frame,
            text="Nota: Selecciona los archivos PDF que deseas unir.  El orden será alfabético.",
            text_color="gray",
            font=("Arial", 12, "bold")
        )
        self.info_note.pack(anchor="w", padx=4, pady=(2, 4))
        
        # ScrollableFrame para los checkboxes
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.files_frame,
            height=400
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=4, pady=2)
    
    # ==================== MANEJADORES DE EVENTOS ====================
    
    def _on_select_folder(self):
        """Abre diálogo para seleccionar carpeta."""
        folder_path = filedialog.askdirectory(title="Selecciona una carpeta con PDFs")
        if folder_path: 
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
            self._load_files(folder_path)
    
    def _load_from_entry(self):
        """Carga carpeta desde la ruta escrita."""
        typed_path = self.folder_entry.get().strip()
        if typed_path:
            self._load_files(typed_path)
    
    def _on_select_all(self):
        """Selecciona todos los checkboxes."""
        for var, _ in self.checkbox_items:
            var.set(True)
    
    def _on_deselect_all(self):
        """Deselecciona todos los checkboxes."""
        for var, _ in self.checkbox_items:
            var.set(False)
    
    # ==================== CARGA DE ARCHIVOS ====================
    
    def _load_files(self, folder_path):
        """Carga la carpeta y lista los archivos PDF."""
        # Limpiar checkboxes previos
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.checkbox_items.clear()
        self.folder_path = folder_path
        
        # Verificar que la carpeta existe
        if not os.path. exists(folder_path):
            messagebox.showerror("Error", f"La carpeta no existe:\n{folder_path}")
            return
        
        if not os.path.isdir(folder_path):
            messagebox.showerror("Error", "La ruta debe ser una carpeta, no un archivo.")
            return
        
        # Crear un checkbox por cada PDF
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".pdf"):
                var = ctk.BooleanVar(value=False)
                
                chk = ctk.CTkCheckBox(
                    self.scroll_frame,
                    text=filename,
                    variable=var,
                    font=ctk.CTkFont(size=12)
                )
                chk. pack(anchor="w", padx=5, pady=2)
                
                self.checkbox_items.append((var, filename))
        
        # Mostrar mensaje si no hay PDFs
        if not self.checkbox_items:
            lbl_empty = ctk.CTkLabel(
                self.scroll_frame,
                text="⚠️ No se encontraron archivos PDF en esta carpeta.",
                text_color="orange",
                font=ctk. CTkFont(size=14)
            )
            lbl_empty.pack(pady=20)
    
    # ==================== OPERACIONES PDF ====================
    
    def _on_merge_pdfs(self):
        """Une los archivos PDF seleccionados."""
        folder = self.folder_entry.get().strip()
        
        if not folder:
            messagebox.showwarning("Advertencia", "Selecciona una carpeta primero.")
            return
        
        # Filtrar PDFs marcados
        selected_files = [filename for var, filename in self.checkbox_items if var.get()]
        
        
        if len(selected_files) < 2:
            messagebox. showwarning("Advertencia", "Selecciona al menos 2 archivos PDF para unir.")
            return
        
        # Diálogo para guardar
        output_path = filedialog.asksaveasfilename(
            title="Guardar PDF unido como",
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")]
        )
        
        if not output_path:
            return
        
        try:
            # Crear documento nuevo con fitz
            merged_doc = fitz.open()
            
            for filename in selected_files:
                pdf_path = os.path.join(folder, filename)
                src_doc = fitz.open(pdf_path)
                merged_doc.insert_pdf(src_doc)
                src_doc.close()
            
            # Guardar documento unido
            merged_doc.save(output_path, garbage=4, deflate=True)
            merged_doc.close()
            
            # Guardar estado para deshacer
            self.last_operation = {
                'created': output_path,
                'source_files': selected_files. copy()
            }
            self.undo_button.configure(state="normal")
            
            messagebox.showinfo("Éxito", f"PDF unido creado:\n{output_path}")
            
        except Exception as e:
            messagebox. showerror("Error", f"Error durante la unión:\n{str(e)}")
    
    def _on_undo(self):
        """Deshace la última operación eliminando el archivo creado."""
        if not self.last_operation:
            messagebox.showinfo("Info", "No hay operación para deshacer.")
            return
        
        created_file = self.last_operation. get('created')
        
        if not created_file or not os.path.exists(created_file):
            messagebox. showwarning("Advertencia", "El archivo creado ya no existe.")
            self.last_operation = None
            self. undo_button.configure(state="disabled")
            return
        
        response = messagebox.askyesno(
            "Confirmar Deshacer",
            f"¿Eliminar el archivo creado?\n\n{created_file}"
        )
        
        if not response:
            return
        
        try:
            os.remove(created_file)
            messagebox.showinfo("Deshacer completado", f"Archivo eliminado:\n{created_file}")
            self.last_operation = None
            self.undo_button.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar:\n{str(e)}")

