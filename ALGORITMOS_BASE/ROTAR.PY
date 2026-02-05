import os
import fitz
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
from io import BytesIO
from typing import Optional, List
import threading


class PDFRotatorApp(ctk.CTkFrame):
    """Aplicación para rotar páginas de documentos PDF."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        self.pdf_path: str = ""
        self.pdf_doc: Optional[fitz.Document] = None
        self.page_count: int = 0
        self.thumbnails: List[ctk.CTkImage] = []
        self.page_cards: List[ctk.CTkFrame] = []
        self.check_vars: List[ctk.BooleanVar] = []
        self.preview_rotation: int = 0
        self.num_columns: int = 4
        
        self._build_ui()
        self.master.bind("<Configure>", self._on_window_resize)
    
    def _build_ui(self):
        """Construye la interfaz."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_top_panel()
        self._build_pages_panel()
        self._build_log_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # Fila 1: Selección de PDF
        ctk.CTkLabel(panel, text="📄 PDF:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.pdf_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona un archivo PDF")
        self.pdf_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.pdf_entry.bind("<Return>", lambda e: self._load_from_entry())
        ctk.CTkButton(panel, text="Seleccionar", width=120, command=self._select_pdf).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Fila 2: Opciones de rotación
        options_frame = ctk.CTkFrame(panel, fg_color="transparent")
        options_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        
        # Grados de rotación
        ctk.CTkLabel(options_frame, text="Rotación:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0,4))
        self.rotation_var = ctk.StringVar(value="90")
        self.rotation_combo = ctk.CTkComboBox(
            options_frame,
            values=["90", "180", "270"],
            variable=self.rotation_var,
            width=80,
            state="readonly",
            command=self._update_preview_rotation
        )
        self.rotation_combo.pack(side="left", padx=4)
        
        # Dirección
        ctk.CTkLabel(options_frame, text="Dirección:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15,4))
        self.direction_var = ctk.StringVar(value="derecha")
        self.direction_combo = ctk.CTkComboBox(
            options_frame,
            values=["derecha", "izquierda"],
            variable=self.direction_var,
            width=100,
            state="readonly",
            command=self._update_preview_rotation
        )
        self.direction_combo.pack(side="left", padx=4)
        
        # Botón preview
        self.preview_btn = ctk.CTkButton(
            options_frame,
            text="👁️ Preview",
            width=100,
            command=self._toggle_preview,
            fg_color="#6c757d"
        )
        self.preview_btn.pack(side="left", padx=(15,4))
        self.preview_active = False
        
        # Contador de selección
        self.counter_lbl = ctk.CTkLabel(options_frame, text="0 páginas seleccionadas", text_color="gray")
        self.counter_lbl.pack(side="right", padx=6)
        
        # Fila 3: Botones de acción
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=6, pady=(0,6))
        btn_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.select_all_btn = ctk.CTkButton(btn_frame, text="☑️ Seleccionar todo", command=self._select_all, fg_color="#6c757d")
        self.select_all_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.deselect_all_btn = ctk.CTkButton(btn_frame, text="☐ Deseleccionar", command=self._deselect_all, fg_color="#6c757d")
        self.deselect_all_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        self.rotate_btn = ctk.CTkButton(btn_frame, text="🔄 Rotar seleccionadas", command=self._rotate_pdf, fg_color="#1f6feb")
        self.rotate_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._clear, fg_color="#e74c3c")
        self.clear_btn.grid(row=0, column=3, padx=4, pady=4, sticky="ew")
    
    def _build_pages_panel(self):
        """Panel de páginas con scroll."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        
        self.scroll_frame = ctk.CTkScrollableFrame(panel)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        
        self._update_grid_columns()
        self._show_empty_message()
    
    def _build_log_panel(self):
        """Panel de log."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(panel, text="📋 Registro", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=6, pady=(6,2))
        
        self.log_text = ctk.CTkTextbox(panel, height=70, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Selecciona un PDF. Marca las páginas que deseas rotar.")
    
    def _log(self, level: str, message: str):
        """Agrega mensaje al log."""
        colors = {"INFO": "#7f8c8d", "SUCCESS": "#27ae60", "WARNING": "#f39c12", "ERROR": "#e74c3c"}
        
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{level}] {message}\n")
        
        last_line = self.log_text.index("end-2l")
        self.log_text.tag_add(level, last_line, "end-1c")
        self.log_text.tag_config(level, foreground=colors.get(level, "white"))
        
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update()
    
    def _show_empty_message(self, message="📂 Selecciona un PDF para ver sus páginas"):
        """Muestra mensaje vacío."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(self.scroll_frame, text=message, font=ctk.CTkFont(size=14), text_color="gray").pack(pady=40)
    
    def _update_grid_columns(self):
        """Configura columnas del grid."""
        for i in range(10):
            try:
                self.scroll_frame.grid_columnconfigure(i, weight=0)
            except:
                pass
        
        for i in range(self.num_columns):
            self.scroll_frame.grid_columnconfigure(i, weight=1)
    
    def _on_window_resize(self, event):
        """Ajusta columnas al redimensionar."""
        if event.widget != self.master:
            return
        
        width = self.master.winfo_width()
        
        if width < 700:
            new_columns = 3
        elif width < 900:
            new_columns = 4
        elif width < 1100:
            new_columns = 5
        else:
            new_columns = 6
        
        if new_columns != self.num_columns and self.page_cards:
            self.num_columns = new_columns
            self._reorganize_grid()
    
    def _reorganize_grid(self):
        """Reorganiza el grid de páginas."""
        if not self.page_cards:
            return
        
        self._update_grid_columns()
        
        for idx, card in enumerate(self.page_cards):
            row = idx // self.num_columns
            col = idx % self.num_columns
            card.grid(row=row, column=col, padx=6, pady=6, sticky="n")
    
    def _select_pdf(self):
        """Abre diálogo para seleccionar PDF."""
        path = filedialog.askopenfilename(title="Seleccionar PDF", filetypes=[("PDF", "*.pdf")])
        if path:
            self._load_pdf(path)
    
    def _load_from_entry(self):
        """Carga PDF desde el entry."""
        path = self.pdf_entry.get().strip()
        if not path:
            return
        
        full_path = os.path.abspath(os.path.expanduser(path))
        
        if not os.path.exists(full_path):
            self._log("ERROR", f"Archivo no encontrado: {full_path}")
            return
        
        if not full_path.lower().endswith('.pdf'):
            self._log("ERROR", "El archivo debe ser un PDF.")
            return
        
        self._load_pdf(full_path)
    
    def _load_pdf(self, path: str):
        """Carga el PDF."""
        try:
            if self.pdf_doc:
                self.pdf_doc.close()
            
            self.pdf_doc = fitz.open(path)
            self.pdf_path = path
            self.page_count = len(self.pdf_doc)
            
            self.pdf_entry.delete(0, "end")
            self.pdf_entry.insert(0, path)
            
            self._log("INFO", f"Cargando: {os.path.basename(path)} ({self.page_count} páginas)...")
            
            threading.Thread(target=self._load_pages, daemon=True).start()
            
        except Exception as e:
            self._log("ERROR", f"Error al cargar PDF: {e}")
    
    def _generate_thumbnail(self, page_number: int, rotation: int = 0) -> Optional[Image.Image]:
        """Genera miniatura de una página."""
        try:
            page = self.pdf_doc[page_number]
            
            # Aplicar rotación para preview
            matrix = fitz.Matrix(0.2, 0.2)
            if rotation:
                matrix = matrix * fitz.Matrix(rotation)
            
            pix = page.get_pixmap(matrix=matrix)
            img_data = pix.tobytes("ppm")
            img = Image.open(BytesIO(img_data))
            
            # Rotar imagen PIL si hay preview rotation
            if rotation:
                img = img.rotate(-rotation, expand=True)
            
            return img
        except Exception as e:
            print(f"[WARN] Error miniatura {page_number}: {e}")
            return None
    
    def _load_pages(self):
        """Carga todas las páginas."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.thumbnails.clear()
        self.page_cards.clear()
        self.check_vars.clear()
        self.preview_active = False
        self.preview_btn.configure(text="👁️ Preview", fg_color="#6c757d")
        
        try:
            for i in range(self.page_count):
                var = ctk.BooleanVar(value=False)
                
                # Card
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color="#3a3a3a",
                    corner_radius=8,
                    border_width=2,
                    border_color="#1f1f1f"
                )
                
                row = i // self.num_columns
                col = i % self.num_columns
                card.grid(row=row, column=col, padx=6, pady=6, sticky="n")
                
                # Miniatura
                img = self._generate_thumbnail(i)
                if img:
                    img_width, img_height = img.size
                    ctk_img = ctk.CTkImage(light_image=img, size=(img_width, img_height))
                    
                    lbl_img = ctk.CTkLabel(card, image=ctk_img, text="", corner_radius=6)
                    lbl_img.pack(padx=6, pady=(6,4))
                    
                    # Guardar referencia a la imagen y label
                    card._image = ctk_img
                    card._image_label = lbl_img
                    card._original_image = img.copy()
                    self.thumbnails.append(ctk_img)
                    
                    # Número de página
                    page = self.pdf_doc[i]
                    rotation_text = f" ({page.rotation}°)" if page.rotation else ""
                    
                    num_lbl = ctk.CTkLabel(
                        lbl_img,
                        text=f"Pág. {i+1}{rotation_text}",
                        font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="white",
                        fg_color="#1f1f1f",
                        corner_radius=4,
                        padx=4,
                        pady=2
                    )
                    num_lbl.place(relx=1, rely=1, anchor="se", x=-4, y=-4)
                    card._num_label = num_lbl
                
                # Checkbox
                chk = ctk.CTkCheckBox(
                    card,
                    text="Rotar",
                    variable=var,
                    font=ctk.CTkFont(size=11),
                    command=self._update_counter,
                    corner_radius=4
                )
                chk.pack(padx=6, pady=(0,6))
                
                self.check_vars.append(var)
                self.page_cards.append(card)
                card._page_index = i
            
            self._update_counter()
            self._log("SUCCESS", f"Cargadas {self.page_count} páginas.")
            
        except Exception as e:
            self._log("ERROR", f"Error cargando páginas: {e}")
    
    def _update_counter(self):
        """Actualiza contador de páginas seleccionadas."""
        selected = sum(1 for var in self.check_vars if var.get())
        total = len(self.check_vars)
        
        if selected > 0:
            self.counter_lbl.configure(text=f"🔄 {selected} de {total} páginas para rotar", text_color="#3b82f6")
        else:
            self.counter_lbl.configure(text=f"0 de {total} páginas seleccionadas", text_color="gray")
    
    def _select_all(self):
        """Selecciona todas las páginas."""
        for var in self.check_vars:
            var.set(True)
        self._update_counter()
    
    def _deselect_all(self):
        """Deselecciona todas las páginas."""
        for var in self.check_vars:
            var.set(False)
        self._update_counter()
    
    def _toggle_preview(self):
        """Activa/desactiva preview de rotación."""
        if not self.pdf_doc:
            self._log("WARNING", "Primero selecciona un PDF.")
            return
        
        self.preview_active = not self.preview_active
        
        if self.preview_active:
            self.preview_btn.configure(text="👁️ Preview ON", fg_color="#27ae60")
            self._update_preview_rotation()
        else:
            self.preview_btn.configure(text="👁️ Preview", fg_color="#6c757d")
            self._restore_original_thumbnails()
    
    def _update_preview_rotation(self, *args):
        """Actualiza preview de rotación en páginas seleccionadas."""
        if not self.preview_active or not self.pdf_doc:
            return
        
        grados = int(self.rotation_var.get())
        direccion = self.direction_var.get()
        
        if direccion == "izquierda":
            grados = -grados
        
        self._log("INFO", f"Preview: {abs(grados)}° hacia la {direccion}")
        
        for i, card in enumerate(self.page_cards):
            if not hasattr(card, '_original_image'):
                continue
            
            if self.check_vars[i].get():
                # Rotar imagen
                rotated_img = card._original_image.rotate(-grados, expand=True)
                new_ctk_img = ctk.CTkImage(light_image=rotated_img, size=(rotated_img.width, rotated_img.height))
                card._image_label.configure(image=new_ctk_img)
                card._image = new_ctk_img
                
                # Actualizar label
                page = self.pdf_doc[i]
                new_rotation = (page.rotation + grados) % 360
                card._num_label.configure(text=f"Pág. {i+1} → {new_rotation}°")
            else:
                # Restaurar original
                self._restore_card_thumbnail(card, i)
    
    def _restore_original_thumbnails(self):
        """Restaura miniaturas originales."""
        for i, card in enumerate(self.page_cards):
            self._restore_card_thumbnail(card, i)
    
    def _restore_card_thumbnail(self, card, index: int):
        """Restaura miniatura original de una card."""
        if not hasattr(card, '_original_image'):
            return
        
        original_img = card._original_image
        new_ctk_img = ctk.CTkImage(light_image=original_img, size=(original_img.width, original_img.height))
        card._image_label.configure(image=new_ctk_img)
        card._image = new_ctk_img
        
        # Restaurar label
        if self.pdf_doc:
            page = self.pdf_doc[index]
            rotation_text = f" ({page.rotation}°)" if page.rotation else ""
            card._num_label.configure(text=f"Pág. {index+1}{rotation_text}")
    
    def _rotate_pdf(self):
        """Rota las páginas seleccionadas."""
        if not self.pdf_doc:
            self._log("WARNING", "Primero selecciona un PDF.")
            return
        
        selected_pages = [i for i, var in enumerate(self.check_vars) if var.get()]
        
        if not selected_pages:
            self._log("WARNING", "Selecciona al menos una página para rotar.")
            return
        
        try:
            grados = int(self.rotation_var.get())
            direccion = self.direction_var.get()
            
            if direccion == "izquierda":
                grados = 360 - grados
            
            self._log("INFO", f"Rotando {len(selected_pages)} página(s)...")
            self.update()
            
            # Rotar páginas seleccionadas
            for i in selected_pages:
                page = self.pdf_doc[i]
                new_rotation = (page.rotation + grados) % 360
                page.set_rotation(new_rotation)
            
            # Generar nombre de salida
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            output_dir = os.path.dirname(self.pdf_path)
            output_name = f"{base_name}_rotado.pdf"
            output_path = os.path.join(output_dir, output_name)
            
            # Evitar sobrescribir
            counter = 1
            while os.path.exists(output_path):
                output_name = f"{base_name}_rotado_{counter}.pdf"
                output_path = os.path.join(output_dir, output_name)
                counter += 1
            
            # Guardar
            self.pdf_doc.save(output_path, garbage=4, deflate=True)
            
            self._log("SUCCESS", f"✅ Guardado: {output_name}")
            self._log("SUCCESS", f"📄 {len(selected_pages)} página(s) rotadas {self.rotation_var.get()}° {direccion}")
            
            # Desactivar preview y recargar
            self.preview_active = False
            self.preview_btn.configure(text="👁️ Preview", fg_color="#6c757d")
            self._load_pdf(output_path)
            
        except Exception as e:
            self._log("ERROR", f"Error al rotar: {e}")
    
    def _clear(self):
        """Limpia todo."""
        if self.pdf_doc:
            self.pdf_doc.close()
            self.pdf_doc = None
        
        self.pdf_path = ""
        self.page_count = 0
        self.thumbnails.clear()
        self.page_cards.clear()
        self.check_vars.clear()
        self.preview_active = False
        self.preview_btn.configure(text="👁️ Preview", fg_color="#6c757d")
        
        self.pdf_entry.delete(0, "end")
        self.counter_lbl.configure(text="0 páginas seleccionadas", text_color="gray")
        
        self._show_empty_message()
        self._log("INFO", "Limpiado.")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Rotador de PDF")
    root.geometry("900x700")
    root.minsize(700, 550)
    app = PDFRotatorApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()