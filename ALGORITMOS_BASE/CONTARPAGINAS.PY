import os
import fitz
import customtkinter as ctk
from tkinter import ttk, filedialog
from typing import List, Tuple
import threading


class PDFPageCounterApp(ctk.CTkFrame):
    """Aplicación para contar páginas de archivos PDF en una carpeta."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        self.folder_path: str = ""
        self.pdf_data: List[Tuple[str, int]] = []
        self.total_pages: int = 0
        
        self._build_ui()
    
    def _build_ui(self):
        """Construye la interfaz."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_top_panel()
        self._build_table_panel()
        self._build_bottom_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # Fila 1: Selección de carpeta
        ctk.CTkLabel(panel, text="📁 Carpeta:", width=70, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.folder_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona una carpeta con archivos PDF")
        self.folder_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar", width=120, command=self._select_folder).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Fila 2: Botones y estadísticas
        stats_frame = ctk.CTkFrame(panel, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        stats_frame.grid_columnconfigure(1, weight=1)
        
        # Botones
        btn_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
        btn_frame.pack(side="left")
        
        self.count_btn = ctk.CTkButton(btn_frame, text="📊 Contar páginas", command=self._count_pages, fg_color="#1f6feb", width=140)
        self.count_btn.pack(side="left", padx=(0,8))
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._clear, fg_color="#e74c3c", width=100)
        self.clear_btn.pack(side="left")
        
        # Estadísticas
        self.stats_frame = ctk.CTkFrame(stats_frame, fg_color="#2b2b2b", corner_radius=8)
        self.stats_frame.pack(side="right", padx=(8,0))
        
        self.files_lbl = ctk.CTkLabel(self.stats_frame, text="📄 0 archivos", font=ctk.CTkFont(size=12))
        self.files_lbl.pack(side="left", padx=12, pady=6)
        
        ctk.CTkLabel(self.stats_frame, text="|", text_color="gray").pack(side="left")
        
        self.pages_lbl = ctk.CTkLabel(self.stats_frame, text="📑 0 páginas", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3b82f6")
        self.pages_lbl.pack(side="left", padx=12, pady=6)
    
    def _build_table_panel(self):
        """Panel con tabla de resultados."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        
        self._setup_table_style()
        
        # Tabla
        table_frame = ctk.CTkFrame(panel)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        cols = ("archivo", "paginas")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", style="Dark.Treeview")
        
        self.table.heading("archivo", text="Archivo PDF", command=lambda: self._sort_table("archivo"))
        self.table.heading("paginas", text="Páginas", command=lambda: self._sort_table("paginas"))
        
        self.table.column("archivo", width=500, anchor="w")
        self.table.column("paginas", width=100, anchor="center")
        
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll_y.set)
        
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        
        # Eventos
        self.table.bind("<Double-1>", self._copy_filename)
        self.table.bind("<Control-c>", self._copy_filename)
        
        # Ordenamiento
        self.sort_column = "archivo"
        self.sort_reverse = False
    
    def _build_bottom_panel(self):
        """Panel inferior con campo de copia y log."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(1, weight=1)
        
        # Campo de copia
        ctk.CTkLabel(panel, text="📋 Copiar:", width=70, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=6, sticky="w")
        self.copy_entry = ctk.CTkEntry(panel, placeholder_text="Doble clic en un archivo para copiar su nombre")
        self.copy_entry.grid(row=0, column=1, padx=4, pady=6, sticky="ew")
        
        copy_btn = ctk.CTkButton(panel, text="📋 Copiar", width=80, command=self._copy_to_clipboard, fg_color="#6c757d")
        copy_btn.grid(row=0, column=2, padx=(4,6), pady=6)
        
        # Log
        self.log_text = ctk.CTkTextbox(panel, height=50, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(0,6))
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Selecciona una carpeta con archivos PDF.")
    
    def _setup_table_style(self):
        """Configura estilo de tabla."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=28)
        style.configure("Dark.Treeview.Heading", background="#3b3b3b", foreground="white", borderwidth=1, font=("Arial", 10, "bold"))
        style.map("Dark.Treeview", background=[("selected", "#1f6feb")], foreground=[("selected", "white")])
    
    def _log(self, level: str, message: str):
        """Agrega mensaje al log."""
        colors = {"INFO": "#7f8c8d", "SUCCESS": "#27ae60", "WARNING": "#f39c12", "ERROR": "#e74c3c"}
        
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", f"[{level}] {message}")
        self.log_text.tag_add(level, "1.0", "end")
        self.log_text.tag_config(level, foreground=colors.get(level, "white"))
        self.log_text.configure(state="disabled")
        self.update()
    
    def _select_folder(self):
        """Abre diálogo para seleccionar carpeta."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            self.folder_path = folder
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self._count_pages()
    
    def _count_pages(self):
        """Cuenta páginas de todos los PDFs."""
        if not self.folder_path:
            path = self.folder_entry.get().strip()
            if path and os.path.isdir(path):
                self.folder_path = path
            else:
                self._log("WARNING", "Selecciona una carpeta válida.")
                return
        
        self._log("INFO", "Contando páginas...")
        self.update()
        
        threading.Thread(target=self._count_pages_thread, daemon=True).start()
    
    def _count_pages_thread(self):
        """Hilo para contar páginas."""
        # Limpiar tabla
        for item in self.table.get_children():
            self.table.delete(item)
        
        self.pdf_data.clear()
        self.total_pages = 0
        errors = 0
        
        # Buscar PDFs
        pdf_files = sorted([f for f in os.listdir(self.folder_path) if f.lower().endswith('.pdf')])
        
        if not pdf_files:
            self._log("WARNING", "No se encontraron archivos PDF en la carpeta.")
            self._update_stats(0, 0)
            return
        
        # Procesar cada PDF
        for filename in pdf_files:
            filepath = os.path.join(self.folder_path, filename)
            
            try:
                with fitz.open(filepath) as doc:
                    pages = doc.page_count
                    self.pdf_data.append((filename, pages))
                    self.total_pages += pages
                    self.table.insert("", "end", values=(filename, pages))
            except Exception as e:
                self.pdf_data.append((filename, -1))
                self.table.insert("", "end", values=(filename, "ERROR"), tags=("error",))
                errors += 1
        
        # Configurar tag de error
        self.table.tag_configure("error", foreground="#e74c3c")
        
        # Fila de total
        self.table.insert("", "end", values=("", ""), tags=("separator",))
        self.table.insert("", "end", values=("📊 TOTAL", self.total_pages), tags=("total",))
        self.table.tag_configure("total", font=("Arial", 11, "bold"))
        self.table.tag_configure("separator", font=("Arial", 4))
        
        # Actualizar estadísticas
        self._update_stats(len(pdf_files), self.total_pages)
        
        if errors > 0:
            self._log("WARNING", f"Completado con {errors} error(es). Total: {self.total_pages} páginas en {len(pdf_files)} archivos.")
        else:
            self._log("SUCCESS", f"✅ {self.total_pages} páginas en {len(pdf_files)} archivos PDF.")
    
    def _update_stats(self, files: int, pages: int):
        """Actualiza estadísticas."""
        self.files_lbl.configure(text=f"📄 {files} archivos")
        self.pages_lbl.configure(text=f"📑 {pages:,} páginas")
    
    def _sort_table(self, column: str):
        """Ordena la tabla por columna."""
        if column == self.sort_column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Obtener datos (excluyendo total y separador)
        items = []
        for item in self.table.get_children():
            values = self.table.item(item, "values")
            if values[0] and values[0] != "📊 TOTAL":
                items.append(values)
        
        # Ordenar
        if column == "archivo":
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        else:
            items.sort(key=lambda x: int(x[1]) if str(x[1]).isdigit() else -1, reverse=self.sort_reverse)
        
        # Limpiar y repoblar
        for item in self.table.get_children():
            self.table.delete(item)
        
        for filename, pages in items:
            if pages == "ERROR":
                self.table.insert("", "end", values=(filename, pages), tags=("error",))
            else:
                self.table.insert("", "end", values=(filename, pages))
        
        # Re-agregar total
        self.table.insert("", "end", values=("", ""), tags=("separator",))
        self.table.insert("", "end", values=("📊 TOTAL", self.total_pages), tags=("total",))
    
    def _copy_filename(self, event=None):
        """Copia nombre de archivo al entry."""
        selection = self.table.selection()
        if not selection:
            return
        
        values = self.table.item(selection[0], "values")
        filename = values[0]
        
        if not filename or filename == "📊 TOTAL":
            return
        
        self.copy_entry.delete(0, "end")
        self.copy_entry.insert(0, filename)
        self.copy_entry.select_range(0, "end")
        self.copy_entry.focus()
        
        self._log("INFO", f"Copiado: {filename}")
    
    def _copy_to_clipboard(self):
        """Copia contenido del entry al portapapeles."""
        text = self.copy_entry.get().strip()
        if not text:
            return
        
        self.clipboard_clear()
        self.clipboard_append(text)
        self._log("SUCCESS", f"📋 Copiado al portapapeles: {text}")
    
    def _clear(self):
        """Limpia todo."""
        self.folder_path = ""
        self.pdf_data.clear()
        self.total_pages = 0
        
        self.folder_entry.delete(0, "end")
        self.copy_entry.delete(0, "end")
        
        for item in self.table.get_children():
            self.table.delete(item)
        
        self._update_stats(0, 0)
        self._log("INFO", "Limpiado.")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Contador de Páginas PDF")
    root.geometry("800x600")
    root.minsize(700, 500)
    app = PDFPageCounterApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()