import os
import fitz
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from io import BytesIO
import threading


class PDFPageDeleterApp(ctk.CTkFrame):
    """
    Aplicación para eliminar páginas de documentos PDF. 
    Diseño basado en el modelo PDFSplitterApp.
    """
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # ===== ESTADO DE LA APLICACIÓN =====
        # Archivo y documento
        self.pdf_path = ""
        self.pdf_doc = None
        
        # Páginas y selección
        self.page_count = 0
        self.check_vars = []              # Variables observables para checkboxes
        self.checkboxes = []              # Widgets de checkbox
        self.thumbnails = []              # Cache de imágenes CTkImage
        self.page_cards = []              # Cards de cada página
        
        # Configuración de layout
        self.num_columns = 5
        self.last_num_columns = 5
        
        # Operación y historial
        self.last_operation = None        # {'original': path, 'created': path, 'deleted_pages': [... ]}
        self.is_loading = False
        
        # ===== CONSTRUIR UI =====
        self._create_widgets()
        
        # ===== BINDING DE EVENTOS =====
        self. master.bind("<Configure>", self._on_window_resize)
    
    # ==================== CONSTRUCCIÓN DE UI ====================
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz siguiendo el diseño del modelo."""
        
        # ===== FRAME SUPERIOR (contenedor único con espaciado compacto) =====
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: PDF de entrada + botón seleccionar
        lbl_pdf = ctk.CTkLabel(top_frame, text="PDF:", width=50, anchor="w")
        lbl_pdf.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.pdf_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Escribe la ruta del PDF o usa Seleccionar",
            width=500
        )
        self.pdf_entry.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        self.pdf_entry.bind("<Return>", lambda e: self._load_from_entry())
        
        btn_select_pdf = ctk.CTkButton(
            top_frame,
            text="Seleccionar PDF",
            width=140,
            command=self._on_select_pdf
        )
        btn_select_pdf.grid(row=0, column=2, padx=(0, 6), pady=4)
        
        # Fila 2: Carpeta de salida
        lbl_output = ctk.CTkLabel(top_frame, text="Salida:", width=50, anchor="w")
        lbl_output.grid(row=2, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.output_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Carpeta de salida (opcional)",
            width=420
        )
        self.output_entry.grid(row=2, column=1, padx=(0, 6), pady=4, sticky="we")
        
        btn_output_folder = ctk.CTkButton(
            top_frame,
            text="Seleccionar Carpeta",
            width=140,
            command=self._on_select_output_folder
        )
        btn_output_folder.grid(row=2, column=2, padx=(0, 6), pady=4)
        
        # Fila 3: Nombre del archivo resultante
        lbl_name = ctk.CTkLabel(top_frame, text="Nombre:", width=50, anchor="w")
        lbl_name.grid(row=3, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self. name_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Nombre del PDF resultante (sin extensión)",
            width=500
        )
        self.name_entry.grid(row=3, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="we")
        
        # Fila 4: Espaciador pequeño (compacto)
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=4, column=0, columnspan=3)
        
        # Fila 5: Botones de acción (Eliminar, Deshacer, Limpiar selección)
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        
        self.delete_button = ctk.CTkButton(
            btn_frame,
            text="🗑️ Eliminar y Guardar",
            command=self._on_delete_pages,
            fg_color="#1f6feb"  # Azul del modelo
        )
        self.delete_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self. undo_button = ctk.CTkButton(
            btn_frame,
            text="↶ Deshacer",
            command=self._on_undo,
            fg_color="#f0ad4e",  # Amarillo/naranja del modelo
            text_color="black"
        )
        self.undo_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        self.undo_button.configure(state="disabled")
        
        self.clear_button = ctk.CTkButton(
            btn_frame,
            text="🧹 Limpiar selección",
            command=self._on_clear_selection
        )
        self.clear_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE PÁGINAS (sin título, márgenes compactos) =====
        self.pages_frame = ctk.CTkFrame(self)
        self.pages_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Nota informativa en el panel de páginas
        self.info_note = ctk.CTkLabel(
            self.pages_frame,
            text="Nota:  Marca las páginas que deseas eliminar del documento.",
            text_color="gray",
            font=("Arial", 12, "bold")
        )
        self.info_note.grid(row=0, column=0, sticky="w", padx=4, pady=(2, 4))
        
        # Contador de páginas seleccionadas
        self.counter_label = ctk.CTkLabel(
            self.pages_frame,
            text="",
            text_color="gray",
            anchor="e"
        )
        self.counter_label.grid(row=0, column=1, sticky="e", padx=4, pady=(2, 4))
        
        # ScrollableFrame para las páginas (grid responsivo)
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.pages_frame,
            height=360
        )
        self.scroll_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=2)
        
        self.pages_frame.grid_rowconfigure(1, weight=1)
        self.pages_frame.grid_columnconfigure(0, weight=1)
        
        self._update_grid_columns()
    
    # ==================== MANEJADORES DE EVENTOS ====================
    
    def _on_select_pdf(self):
        """Abre diálogo para seleccionar PDF."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            self._load_pdf(file_path)
    
    def _load_from_entry(self):
        """Carga PDF desde la ruta escrita en el entry."""
        typed_path = self.pdf_entry.get().strip()
        
        if not typed_path: 
            return
        
        # Resolver ruta relativa
        if not os.path.isabs(typed_path):
            home = os.path.expanduser("~")
            full_path = os.path.join(home, typed_path)
        else:
            full_path = typed_path
        
        # Validaciones
        if not os.path. exists(full_path):
            messagebox.showerror("Error", f"El archivo no existe:\n{full_path}")
            return
        
        if not full_path.lower().endswith('.pdf'):
            messagebox.showerror("Error", "El archivo debe ser un PDF")
            return
        
        self._load_pdf(full_path)
    
    def _on_select_output_folder(self):
        """Selecciona carpeta de salida."""
        folder = filedialog. askdirectory(title="Seleccionar carpeta de salida")
        
        if folder:
            self.output_entry.delete(0, tk. END)
            self.output_entry.insert(0, folder)
    
    def _on_window_resize(self, event):
        """Detecta cambios de tamaño y ajusta columnas."""
        if event.widget != self.master:
            return
        
        width = self.master.winfo_width()
        
        # Calcular columnas según ancho
        if width < 900:
            new_columns = 3
        elif width < 1100:
            new_columns = 4
        elif width < 1300:
            new_columns = 5
        elif width < 1500:
            new_columns = 6
        else:
            new_columns = 7
        
        # Si cambió, reorganizar
        if new_columns != self.num_columns and self.checkboxes:
            self. num_columns = new_columns
            self._reorganize_grid()
    
    def _on_clear_selection(self):
        """Limpia todas las selecciones de checkboxes."""
        for var in self.check_vars:
            var.set(False)
        self._update_counter()
        messagebox.showinfo("Limpiar selección", "Se han deseleccionado todas las páginas.")
    
    # ==================== CARGA DE PDF ====================
    
    def _load_pdf(self, file_path):
        """Carga el PDF y actualiza la UI."""
        self.pdf_path = file_path
        
        try:
            self.pdf_doc = fitz.open(file_path)
            self.page_count = len(self.pdf_doc)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Actualizar entry de ruta
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, file_path)
            
            # Configurar carpeta de salida por defecto
            input_folder = os.path.dirname(file_path)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, input_folder)
            
            # Configurar nombre por defecto
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, f"{base_name}_editado")
            
            # Actualizar info
            self. info_label.configure(
                text=f"✓ {self.page_count} páginas • {file_size_mb:.2f} MB",
                text_color="#10b981"
            )
            
            # Cargar páginas en hilo separado
            threading.Thread(target=self._load_pages, daemon=True).start()
            
        except Exception as e: 
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{str(e)}")
            print(f"[ERROR] Cargar PDF: {e}")
    
    def _generate_thumbnail(self, page_number):
        """Genera miniatura de una página del PDF."""
        try:
            page = self.pdf_doc[page_number]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
            img_data = pix.tobytes("ppm")
            
            image = Image.open(BytesIO(img_data))
            return image
        except Exception as e:
            print(f"[WARN] Error generando miniatura página {page_number}: {e}")
            return None
    
    def _load_pages(self):
        """Carga checkboxes y miniaturas en grid responsivo."""
        # Limpiar widgets anteriores
        for widget in self. scroll_frame.winfo_children():
            widget.destroy()
        
        self.check_vars. clear()
        self.checkboxes.clear()
        self.thumbnails.clear()
        self.page_cards.clear()
        
        try:
            for i in range(self.page_count):
                var = ctk.BooleanVar()
                
                # Card de página compacta
                page_card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color="gray20",
                    corner_radius=6,
                    border_width=1,
                    border_color="gray25"
                )
                
                row = i // self.num_columns
                col = i % self. num_columns
                page_card.grid(row=row, column=col, padx=4, pady=4, sticky="n")
                
                # Contenedor vertical
                content_frame = ctk.CTkFrame(page_card, fg_color="transparent")
                content_frame.pack(fill="both", expand=False, padx=0, pady=0)
                
                # ===== MINIATURA CON NÚMERO DE PÁGINA =====
                try:
                    img = self._generate_thumbnail(i)
                    if img: 
                        img_width, img_height = img.size
                        
                        # Frame para la miniatura
                        thumb_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                        thumb_frame.pack(fill="both", padx=0, pady=0)
                        
                        # Miniatura
                        ctk_img = ctk.CTkImage(light_image=img, size=(img_width, img_height))
                        lbl_img = ctk.CTkLabel(
                            thumb_frame,
                            image=ctk_img,
                            text="",
                            corner_radius=3
                        )
                        lbl_img.pack(fill="both", padx=0, pady=0)
                        self.thumbnails.append(ctk_img)
                        
                        # Número de página superpuesto
                        num_label = ctk.CTkLabel(
                            lbl_img,
                            text=f"Página {i + 1}",
                            font=ctk.CTkFont(size=12, weight="bold"),
                            text_color="white",
                            bg_color="transparent",
                            corner_radius=3
                        )
                        num_label.place(relx=1, rely=1, anchor="se", padx=4, pady=4)
                        
                except Exception as e:
                    print(f"[WARN] Error mostrando miniatura {i}: {e}")
                    # Si falla la miniatura, mostrar placeholder
                    placeholder = ctk.CTkLabel(
                        content_frame,
                        text=f"Página {i + 1}",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        width=100,
                        height=60
                    )
                    placeholder. pack(padx=4, pady=4)
                
                # ===== CHECKBOX ELIMINAR =====
                info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=3, pady=3)
                
                chk = ctk.CTkCheckBox(
                    info_frame,
                    text="Eliminar",
                    variable=var,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    command=self._update_counter,
                    corner_radius=3,
                    checkbox_width=18,
                    checkbox_height=18
                )
                chk. pack(anchor="w", pady=2, padx=2)
                
                self.check_vars.append(var)
                self.checkboxes.append(chk)
                self.page_cards.append(page_card)
            
            self._update_counter()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar las páginas:\n{str(e)}")
            print(f"[ERROR] Cargar páginas: {e}")
    
    def _update_grid_columns(self):
        """Configura grid con número correcto de columnas."""
        # Limpiar configuración anterior
        for i in range(10):
            try:
                self.scroll_frame.grid_columnconfigure(i, weight=0)
            except:
                pass
        
        # Configurar nuevas columnas
        for i in range(self.num_columns):
            self.scroll_frame.grid_columnconfigure(i, weight=1)
    
    def _reorganize_grid(self):
        """Reorganiza widgets cuando cambian las columnas."""
        if not self.page_cards:
            return
        
        self._update_grid_columns()
        
        for idx, page_card in enumerate(self.page_cards):
            row = idx // self.num_columns
            col = idx % self. num_columns
            page_card.grid(row=row, column=col, padx=4, pady=4, sticky="n")
    
    def _update_counter(self):
        """Actualiza el contador de páginas seleccionadas."""
        selected = sum(1 for var in self. check_vars if var.get())
        total = len(self.check_vars)
        
        if selected > 0:
            self.counter_label.configure(
                text=f"🗑️ {selected} de {total} páginas para eliminar",
                text_color="#ef4444"
            )
        else:
            self.counter_label.configure(
                text=f"0 de {total} páginas seleccionadas",
                text_color="gray"
            )
    
    # ==================== OPERACIONES PDF ====================
    
    def _on_delete_pages(self):
        """Elimina las páginas seleccionadas y guarda el PDF."""
        if not self.pdf_doc:
            messagebox. showwarning("Advertencia", "Por favor, seleccione un archivo PDF primero.")
            return
        
        pages_to_delete = [i for i, var in enumerate(self.check_vars) if var.get()]
        
        if not pages_to_delete:
            messagebox. showwarning("Advertencia", "No ha seleccionado ninguna página para eliminar.")
            return
        
        if len(pages_to_delete) == self.page_count:
            messagebox.showerror(
                "Error",
                "No se pueden eliminar todas las páginas.\nDebe quedar al menos una página en el PDF."
            )
            return
        
        # Confirmar operación
        response = messagebox.askyesno(
            "Confirmar",
            f"¿Está seguro de eliminar {len(pages_to_delete)} página(s)?\n\n"
            f"El PDF resultante tendrá {self.page_count - len(pages_to_delete)} página(s)."
        )
        
        if not response:
            return
        
        try:
            # Crear documento nuevo con las páginas no eliminadas
            new_doc = fitz.open()
            
            for i in range(self.page_count):
                if i not in pages_to_delete:
                    new_doc.insert_pdf(self.pdf_doc, from_page=i, to_page=i)
            
            # Obtener ruta de salida
            output_path = self._get_output_path()
            
            # Guardar documento
            new_doc.save(output_path, garbage=4, deflate=True)
            new_doc.close()
            
            # Guardar estado para deshacer
            self.last_operation = {
                'original':  self.pdf_path,
                'created': output_path,
                'deleted_pages': pages_to_delete. copy()
            }
            
            self. undo_button.configure(state="normal")
            
            # Mensaje de éxito
            messagebox.showinfo(
                "Éxito",
                f"✓ PDF generado correctamente\n\n"
                f"{self.page_count - len(pages_to_delete)} páginas guardadas en:\n{output_path}"
            )
            
            # Limpiar selección
            for var in self.check_vars:
                var.set(False)
            self._update_counter()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el PDF:\n{str(e)}")
            print(f"[ERROR] Eliminar páginas: {e}")
    
    def _get_output_path(self):
        """Obtiene la ruta de salida con manejo de duplicados."""
        output_folder = self.output_entry.get().strip()
        if not output_folder:
            output_folder = os.path.dirname(self.pdf_path)
        
        file_name = self.name_entry.get().strip()
        if not file_name:
            file_name = f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_editado"
        
        # Remover extensión si la incluyó el usuario
        if file_name. lower().endswith('.pdf'):
            file_name = file_name[:-4]
        
        output_path = os.path.join(output_folder, f"{file_name}.pdf")
        
        # Evitar sobrescribir archivos existentes
        counter = 1
        base_path = output_path
        while os.path.exists(output_path):
            name_without_ext = os.path.splitext(base_path)[0]
            output_path = f"{name_without_ext} ({counter}).pdf"
            counter += 1
        
        return output_path
    
    def _on_undo(self):
        """Deshace la última operación eliminando el archivo creado."""
        if not self. last_operation:
            messagebox.showinfo("Info", "No hay operación para deshacer.")
            return
        
        created_file = self.last_operation. get('created')
        
        if not created_file or not os.path.exists(created_file):
            messagebox. showwarning("Advertencia", "El archivo creado ya no existe.")
            self.last_operation = None
            self.undo_button.configure(state="disabled")
            return
        
        response = messagebox.askyesno(
            "Confirmar Deshacer",
            f"¿Está seguro de eliminar el archivo creado?\n\n{created_file}"
        )
        
        if not response: 
            return
        
        try: 
            os.remove(created_file)
            
            messagebox.showinfo(
                "Deshacer completado",
                f"El archivo ha sido eliminado:\n{created_file}"
            )
            
            self.last_operation = None
            self.undo_button.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el archivo:\n{str(e)}")
            print(f"[ERROR] Deshacer: {e}")


