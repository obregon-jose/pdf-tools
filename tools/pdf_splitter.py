import os
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox


class PDFSplitterApp(ctk.CTkFrame):
    """Aplicación para dividir PDF en páginas individuales con nombres personalizados."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        self.pdf_path = ""
        self.page_count = 0
        self.last_split = None
        self.entries = []
        self.labels = []
        
        self.manual_var = ctk.BooleanVar(value=False)
        self.prefix_var = tk.StringVar(value="")
        self.prefix_var.trace_add("write", lambda *_: self._update_preview())
        
        self._build_ui()
    
    def _build_ui(self):
        """Construye la interfaz."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_top_panel()
        self._build_preview_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # PDF entrada
        ctk.CTkLabel(panel, text="PDF:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.pdf_entry = ctk.CTkEntry(panel, placeholder_text="Ruta del PDF")
        self.pdf_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar PDF", width=130, command=self._select_pdf).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Carpeta salida
        ctk.CTkLabel(panel, text="Salida:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=(6,4), pady=4, sticky="w")
        self.out_entry = ctk.CTkEntry(panel, placeholder_text="Carpeta de salida (opcional)")
        self.out_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar", width=130, command=self._select_output).grid(row=1, column=2, padx=(4,6), pady=4)
        
        # Prefijo y checkbox
        ctk.CTkLabel(panel, text="Prefijo:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=(6,4), pady=4, sticky="w")
        self.prefix_entry = ctk.CTkEntry(panel, textvariable=self.prefix_var, width=250)
        self.prefix_entry.grid(row=2, column=1, padx=4, pady=4, sticky="w")
        
        self.manual_cb = ctk.CTkCheckBox(panel, text="Agregar nombres por página", variable=self.manual_var, command=self._toggle_manual)
        self.manual_cb.grid(row=2, column=2, padx=(4,6), pady=4, sticky="w")
        
        # Botones de acción
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.split_btn = ctk.CTkButton(btn_frame, text="📄 Dividir PDF", command=self._split_pdf, fg_color="#1f6feb")
        self.split_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.undo_btn = ctk.CTkButton(btn_frame, text="↶ Deshacer", command=self._undo, fg_color="#f0ad4e", text_color="black", state="disabled")
        self.undo_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._clear_names, fg_color="#e74c3c")
        self.clear_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    
    def _build_preview_panel(self):
        """Panel de previsualización de páginas."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        self.info_lbl = ctk.CTkLabel(panel, text="ℹ️ Sin modo manual, los archivos se nombran: Página 1, Página 2...", text_color="gray", font=ctk.CTkFont(size=11))
        self.info_lbl.grid(row=0, column=0, sticky="w", padx=8, pady=(6,2))
        
        self.scroll_frame = ctk.CTkScrollableFrame(panel)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
    
    def _select_pdf(self):
        """Selecciona archivo PDF."""
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        
        self.pdf_path = path
        self.pdf_entry.delete(0, "end")
        self.pdf_entry.insert(0, path)
        
        if not self.out_entry.get().strip():
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, os.path.dirname(path))
        
        self._load_preview()
    
    def _select_output(self):
        """Selecciona carpeta de salida."""
        folder = filedialog.askdirectory()
        if folder:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, folder)
    
    def _load_preview(self):
        """Carga la vista previa de páginas."""
        try:
            doc = fitz.open(self.pdf_path)
            self.page_count = doc.page_count
            doc.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{e}")
            self.page_count = 0
            return
        
        # Limpiar preview anterior
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.entries.clear()
        self.labels.clear()
        
        prefix = self.prefix_var.get().strip()
        prefix_txt = f"{prefix}_" if prefix else ""
        
        for i in range(self.page_count):
            # Label de previsualización
            lbl = ctk.CTkLabel(self.scroll_frame, text=f"Página {i+1} → {prefix_txt}", anchor="w")
            lbl.grid(row=i, column=0, padx=(6,4), pady=3, sticky="w")
            
            # Entry para nombre personalizado
            entry = ctk.CTkEntry(self.scroll_frame, placeholder_text=f"Documento {i+1}")
            entry.grid(row=i, column=1, padx=(4,6), pady=3, sticky="ew")
            entry.bind("<KeyRelease>", lambda e, idx=i: self._update_label(idx))
            
            self.labels.append(lbl)
            self.entries.append(entry)
            
            # Ocultar si no está en modo manual
            if not self.manual_var.get():
                lbl.grid_remove()
                entry.grid_remove()
        
        self.split_btn.configure(state="normal" if self.page_count > 0 else "disabled")
    
    def _update_label(self, idx):
        """Actualiza el label de previsualización de una página."""
        if idx >= len(self.entries):
            return
        
        entry = self.entries[idx]
        body = entry.get().strip()
        prefix = self.prefix_var.get().strip()
        prefix_txt = f"{prefix}_" if prefix else ""
        
        preview = f"Página {idx+1} → {prefix_txt}{body}" if body else f"Página {idx+1} → {prefix_txt}"
        self.labels[idx].configure(text=preview)
    
    def _update_preview(self):
        """Actualiza todos los labels cuando cambia el prefijo."""
        for i in range(len(self.labels)):
            self._update_label(i)
    
    def _toggle_manual(self):
        """Muestra/oculta campos de nombres personalizados."""
        manual = self.manual_var.get()
        
        for lbl, entry in zip(self.labels, self.entries):
            if manual:
                lbl.grid()
                entry.grid()
            else:
                lbl.grid_remove()
                entry.grid_remove()
        
        if manual:
            self.info_lbl.grid_remove()
        else:
            self.info_lbl.grid()
    
    def _clear_names(self):
        """Limpia todos los campos de nombres."""
        for entry in self.entries:
            entry.delete(0, "end")
        self._update_preview()
    
    def _split_pdf(self):
        """Divide el PDF en páginas individuales."""
        pdf_path = self.pdf_entry.get().strip() or self.pdf_path
        
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Selecciona un PDF válido.")
            return
        
        # Validar campos si está en modo manual
        if self.manual_var.get():
            empty = [str(i+1) for i, e in enumerate(self.entries) if not e.get().strip()]
            if empty:
                messagebox.showerror("Error", f"Campos vacíos en páginas: {', '.join(empty)}")
                return
        
        output_dir = self.out_entry.get().strip() or os.path.dirname(pdf_path)
        os.makedirs(output_dir, exist_ok=True)
        
        prefix = self.prefix_var.get().strip()
        manual = self.manual_var.get()
        
        try:
            doc = fitz.open(pdf_path)
            created = []
            
            for i in range(doc.page_count):
                # Generar nombre
                if manual and i < len(self.entries):
                    body = self.entries[i].get().strip()
                    name = f"{prefix}_{body}" if prefix else body
                else:
                    name = f"Página_{i+1}"
                
                # Limpiar nombre
                safe_name = "".join(c for c in name if c not in r'\/:*?"<>|').strip() or f"Página_{i+1}"
                
                # Crear ruta única
                path = os.path.join(output_dir, f"{safe_name}.pdf")
                counter = 1
                while os.path.exists(path):
                    path = os.path.join(output_dir, f"{safe_name} ({counter}).pdf")
                    counter += 1
                
                # Guardar página
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                new_doc.save(path, garbage=4, deflate=True)
                new_doc.close()
                created.append(path)
            
            doc.close()
            
            # Eliminar original
            removed = False
            try:
                os.remove(pdf_path)
                removed = True
            except:
                pass
            
            self.last_split = {
                "original_path": pdf_path,
                "created_files": created,
                "original_removed": removed
            }
            self.undo_btn.configure(state="normal")
            
            msg = f"✅ {len(created)} archivos creados."
            if removed:
                msg += "\nPDF original eliminado."
            messagebox.showinfo("Éxito", msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al dividir:\n{e}")
    
    def _undo(self):
        """Deshace la última división."""
        if not self.last_split:
            return
        
        orig = self.last_split["original_path"]
        created = self.last_split["created_files"]
        
        if os.path.exists(orig):
            messagebox.showinfo("Info", "El original ya existe.")
            self.last_split = None
            self.undo_btn.configure(state="disabled")
            return
        
        try:
            # Reconstruir original
            new_doc = fitz.open()
            for path in created:
                if os.path.exists(path):
                    sub = fitz.open(path)
                    new_doc.insert_pdf(sub)
                    sub.close()
            new_doc.save(orig, garbage=4, deflate=True)
            new_doc.close()
            
            # Eliminar páginas
            deleted = 0
            for path in created:
                try:
                    os.remove(path)
                    deleted += 1
                except:
                    pass
            
            messagebox.showinfo("Deshacer", f"✅ Original restaurado.\n{deleted} archivos eliminados.")
            
            self.last_split = None
            self.undo_btn.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al deshacer:\n{e}")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("PDF Splitter")
    root.geometry("750x600")
    root.minsize(650, 500)
    app = PDFSplitterApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()