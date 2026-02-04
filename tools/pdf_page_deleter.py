import os
import fitz
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image
from io import BytesIO
import threading


class PDFPageDeleterApp(ctk.CTkFrame):
    """Aplicación para eliminar páginas de documentos PDF."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        self.pdf_path = ""
        self.pdf_doc = None
        self.page_count = 0
        self.check_vars = []
        self.checkboxes = []
        self.thumbnails = []
        self.page_cards = []
        self.num_columns = 5
        self.last_operation = None
        
        self._create_widgets()
        self.master.bind("<Configure>", self._on_window_resize)
    
    def _create_widgets(self):
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
        
        # PDF
        ctk.CTkLabel(panel, text="PDF:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.pdf_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona el PDF")
        self.pdf_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.pdf_entry.bind("<Return>", lambda e: self._load_from_entry())
        ctk.CTkButton(panel, text="Seleccionar PDF", width=130, command=self._on_select_pdf).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Salida
        ctk.CTkLabel(panel, text="Salida:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=(6,4), pady=4, sticky="w")
        self.output_entry = ctk.CTkEntry(panel, placeholder_text="Carpeta de salida (opcional)")
        self.output_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar", width=130, command=self._on_select_output).grid(row=1, column=2, padx=(4,6), pady=4)
        
        # Nombre
        ctk.CTkLabel(panel, text="Nombre:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=(6,4), pady=4, sticky="w")
        self.name_entry = ctk.CTkEntry(panel, placeholder_text="Nombre del PDF resultante")
        self.name_entry.grid(row=2, column=1, columnspan=2, padx=4, pady=4, sticky="ew")
        
        # Botones
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.delete_btn = ctk.CTkButton(btn_frame, text="🗑️ Eliminar y Guardar", command=self._on_delete_pages, fg_color="#1f6feb")
        self.delete_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.undo_btn = ctk.CTkButton(btn_frame, text="↶ Deshacer", command=self._on_undo, fg_color="#f0ad4e", text_color="black", state="disabled")
        self.undo_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._on_clear, fg_color="#e74c3c")
        self.clear_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    
    def _build_pages_panel(self):
        """Panel de páginas."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6,4))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="ℹ️ Marca las páginas que deseas eliminar", text_color="gray", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        
        self.counter_lbl = ctk.CTkLabel(header, text="0 páginas seleccionadas", text_color="gray", anchor="e")
        self.counter_lbl.grid(row=0, column=1, sticky="e")
        
        # ScrollableFrame
        self.scroll_frame = ctk.CTkScrollableFrame(panel)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        
        self._update_grid_columns()
        self._show_empty_message()
    
    def _build_log_panel(self):
        """Panel de log."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(panel, text="📋 Registro", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=6, pady=(6,2))
        
        self.log_text = ctk.CTkTextbox(panel, height=90, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Listo para comenzar.")
    
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
    
    def _show_empty_message(self, message="📂 Selecciona un PDF para comenzar"):
        """Muestra mensaje vacío."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(self.scroll_frame, text=message, font=ctk.CTkFont(size=14), text_color="gray").pack(pady=40)
    
    def _on_select_pdf(self):
        """Selecciona PDF."""
        path = filedialog.askopenfilename(title="Seleccionar PDF", filetypes=[("PDF", "*.pdf")])
        if path:
            self._load_pdf(path)
    
    def _load_from_entry(self):
        """Carga PDF desde entry."""
        typed_path = self.pdf_entry.get().strip()
        if not typed_path:
            return
        
        full_path = os.path.abspath(os.path.expanduser(typed_path))
        
        if not os.path.exists(full_path):
            self._log("ERROR", f"El archivo no existe: {full_path}")
            return
        
        if not full_path.lower().endswith('.pdf'):
            self._log("ERROR", "El archivo debe ser un PDF.")
            return
        
        self._load_pdf(full_path)
    
    def _on_select_output(self):
        """Selecciona carpeta de salida."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)
            self._log("INFO", f"Carpeta de salida: {folder}")
    
    def _on_clear(self):
        """Limpia selección."""
        for var in self.check_vars:
            var.set(False)
        self._update_counter()
        self._log("INFO", "Selección limpiada.")
    
    def _on_window_resize(self, event):
        """Ajusta columnas al redimensionar."""
        if event.widget != self.master:
            return
        
        width = self.master.winfo_width()
        
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
        
        if new_columns != self.num_columns and self.checkboxes:
            self.num_columns = new_columns
            self._reorganize_grid()
    
    def _load_pdf(self, file_path):
        """Carga PDF."""
        self.pdf_path = file_path
        
        try:
            self.pdf_doc = fitz.open(file_path)
            self.page_count = len(self.pdf_doc)
            
            self.pdf_entry.delete(0, "end")
            self.pdf_entry.insert(0, file_path)
            
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, os.path.dirname(file_path))
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, f"{base_name}_nuevo")
            
            self._log("INFO", f"PDF cargado: {os.path.basename(file_path)} ({self.page_count} páginas)")
            
            threading.Thread(target=self._load_pages, daemon=True).start()
            
        except Exception as e:
            self._log("ERROR", f"No se pudo abrir el PDF: {e}")
    
    def _generate_thumbnail(self, page_number):
        """Genera miniatura."""
        try:
            page = self.pdf_doc[page_number]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
            img_data = pix.tobytes("ppm")
            return Image.open(BytesIO(img_data))
        except Exception as e:
            print(f"[WARN] Error miniatura {page_number}: {e}")
            return None
    
    def _load_pages(self):
        """Carga páginas."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.check_vars.clear()
        self.checkboxes.clear()
        self.thumbnails.clear()
        self.page_cards.clear()
        
        try:
            for i in range(self.page_count):
                var = ctk.BooleanVar()
                
                # Card con borde oscuro
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color="#d8d8d8",
                    corner_radius=8,
                    border_width=2,
                    border_color="#535353"
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
                    self.thumbnails.append(ctk_img)
                    
                    # Número de página
                    num_lbl = ctk.CTkLabel(
                        lbl_img,
                        text=f"Pág. {i+1}",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color="white",
                        fg_color="#1f1f1f",
                        corner_radius=4,
                        padx=6,
                        pady=2
                    )
                    num_lbl.place(relx=1, rely=1, anchor="se", x=-6, y=-6)
                
                # Checkbox
                chk = ctk.CTkCheckBox(
                    card,
                    text="Eliminar",
                    variable=var,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=self._update_counter,
                    corner_radius=4
                )
                chk.pack(padx=8, pady=(0,8))
                
                self.check_vars.append(var)
                self.checkboxes.append(chk)
                self.page_cards.append(card)
            
            self._update_counter()
            self._log("SUCCESS", f"Cargadas {self.page_count} páginas.")
            
        except Exception as e:
            self._log("ERROR", f"Error cargando páginas: {e}")
    
    def _update_grid_columns(self):
        """Configura grid."""
        for i in range(10):
            try:
                self.scroll_frame.grid_columnconfigure(i, weight=0)
            except:
                pass
        
        for i in range(self.num_columns):
            self.scroll_frame.grid_columnconfigure(i, weight=1)
    
    def _reorganize_grid(self):
        """Reorganiza grid."""
        if not self.page_cards:
            return
        
        self._update_grid_columns()
        
        for idx, card in enumerate(self.page_cards):
            row = idx // self.num_columns
            col = idx % self.num_columns
            card.grid(row=row, column=col, padx=6, pady=6, sticky="n")
    
    def _update_counter(self):
        """Actualiza contador."""
        selected = sum(1 for var in self.check_vars if var.get())
        total = len(self.check_vars)
        
        if selected > 0:
            self.counter_lbl.configure(text=f"🗑️ {selected} de {total} páginas para eliminar", text_color="#ef4444")
        else:
            self.counter_lbl.configure(text=f"0 de {total} páginas seleccionadas", text_color="gray")
    
    def _on_delete_pages(self):
        """Elimina páginas seleccionadas."""
        if not self.pdf_doc:
            self._log("WARNING", "Selecciona un PDF primero.")
            return
        
        pages_to_delete = [i for i, var in enumerate(self.check_vars) if var.get()]
        
        if not pages_to_delete:
            self._log("WARNING", "No hay páginas seleccionadas para eliminar.")
            return
        
        if len(pages_to_delete) == self.page_count:
            self._log("ERROR", "No puedes eliminar todas las páginas.")
            return
        
        self._log("INFO", f"Eliminando {len(pages_to_delete)} página(s)...")
        
        try:
            new_doc = fitz.open()
            
            for i in range(self.page_count):
                if i not in pages_to_delete:
                    new_doc.insert_pdf(self.pdf_doc, from_page=i, to_page=i)
            
            output_path = self._get_output_path()
            new_doc.save(output_path, garbage=4, deflate=True)
            new_doc.close()
            
            self.last_operation = {
                'original': self.pdf_path,
                'created': output_path,
                'deleted_pages': pages_to_delete.copy()
            }
            
            self.undo_btn.configure(state="normal")
            
            self._log("SUCCESS", f"✅ PDF guardado: {os.path.basename(output_path)}")
            self._log("SUCCESS", f"{self.page_count - len(pages_to_delete)} páginas → {output_path}")
            
            for var in self.check_vars:
                var.set(False)
            self._update_counter()
            
        except Exception as e:
            self._log("ERROR", f"Error procesando PDF: {e}")
    
    def _get_output_path(self):
        """Obtiene ruta de salida."""
        output_folder = self.output_entry.get().strip() or os.path.dirname(self.pdf_path)
        file_name = self.name_entry.get().strip() or f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_nuevo"
        
        if file_name.lower().endswith('.pdf'):
            file_name = file_name[:-4]
        
        output_path = os.path.join(output_folder, f"{file_name}.pdf")
        
        counter = 1
        base_path = output_path
        while os.path.exists(output_path):
            name_without_ext = os.path.splitext(base_path)[0]
            output_path = f"{name_without_ext} ({counter}).pdf"
            counter += 1
        
        return output_path
    
    def _on_undo(self):
        """Deshace operación."""
        if not self.last_operation:
            self._log("WARNING", "No hay operación para deshacer.")
            return
        
        created_file = self.last_operation.get('created')
        
        if not created_file or not os.path.exists(created_file):
            self._log("WARNING", "El archivo creado ya no existe.")
            self.last_operation = None
            self.undo_btn.configure(state="disabled")
            return
        
        self._log("INFO", "Deshaciendo operación...")
        
        try:
            os.remove(created_file)
            self._log("SUCCESS", f"✅ Archivo eliminado: {os.path.basename(created_file)}")
            
            self.last_operation = None
            self.undo_btn.configure(state="disabled")
            
        except Exception as e:
            self._log("ERROR", f"No se pudo eliminar: {e}")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("PDF Page Deleter")
    root.geometry("1000x750")
    root.minsize(850, 650)
    app = PDFPageDeleterApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()