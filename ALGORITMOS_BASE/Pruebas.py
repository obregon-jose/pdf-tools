import os
import re
import customtkinter as ctk
from tkinter import ttk, filedialog
from typing import List, Tuple, Optional


class InvoiceNumberUpdaterApp(ctk.CTkFrame):
    """Aplicación para actualizar número de factura en archivos CRC/OPF."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        self.folder_path: str = ""
        self.current_invoice: str = ""
        
        self._build_ui()
    
    def _build_ui(self):
        """Construye la interfaz."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_top_panel()
        self._build_files_panel()
        self._build_log_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # Fila 1: Selección de carpeta
        ctk.CTkLabel(panel, text="📁 Carpeta:", width=100, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=6, sticky="w")
        self.folder_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona carpeta con archivos CRC/OPF")
        self.folder_entry.grid(row=0, column=1, columnspan=2, padx=4, pady=6, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar", width=120, command=self._select_folder).grid(row=0, column=3, padx=(4,6), pady=6)
        
        # Fila 2: Factura actual y nuevo número (2 columnas)
        ctk.CTkLabel(panel, text="📋 Factura actual:", width=100, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=(6,4), pady=6, sticky="w")
        self.current_invoice_lbl = ctk.CTkLabel(panel, text="---", text_color="gray", anchor="w", width=150)
        self.current_invoice_lbl.grid(row=1, column=1, padx=4, pady=6, sticky="w")
        
        ctk.CTkLabel(panel, text="🔢 Nuevo número:", anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=1, column=2, padx=(20,4), pady=6, sticky="w")
        self.new_invoice_entry = ctk.CTkEntry(panel, placeholder_text="Nuevo número", width=150)
        self.new_invoice_entry.grid(row=1, column=3, padx=(4,6), pady=6, sticky="ew")
        
        # Fila 3: Botones
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=6, pady=(4,6))
        btn_frame.grid_columnconfigure((0,1), weight=1)
        
        self.update_btn = ctk.CTkButton(btn_frame, text="✏️ Actualizar número de factura", command=self._update_invoice, fg_color="#1f6feb")
        self.update_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._clear, fg_color="#e74c3c")
        self.clear_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
    
    def _build_files_panel(self):
        """Panel con lista de archivos."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6,4))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="📄 Archivos en la carpeta", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        self.count_lbl = ctk.CTkLabel(header, text="0 archivos", text_color="gray", anchor="e")
        self.count_lbl.grid(row=0, column=1, sticky="e")
        
        # Tabla
        table_frame = ctk.CTkFrame(panel)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        self._setup_table_style()
        
        cols = ("archivo", "factura")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", style="Dark.Treeview")
        
        self.table.heading("archivo", text="Archivo")
        self.table.heading("factura", text="Factura")
        
        self.table.column("archivo", width=550, anchor="w")
        self.table.column("factura", width=120, anchor="center")
        
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll_y.set)
        
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
    
    def _build_log_panel(self):
        """Panel de log."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        self.log_text = ctk.CTkTextbox(panel, height=60, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Selecciona una carpeta con archivos CRC/OPF.")
    
    def _setup_table_style(self):
        """Configura estilo de tabla."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=26)
        style.configure("Dark.Treeview.Heading", background="#3b3b3b", foreground="white", borderwidth=1)
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
    
    def _extract_invoice_number(self, filename: str) -> Optional[str]:
        """Extrae el número de factura (entre IPSP y _)."""
        pattern = r'IPSP(\d+)_'
        match = re.search(pattern, filename, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _get_crc_opf_files(self) -> List[Tuple[str, Optional[str]]]:
        """Obtiene archivos CRC/OPF con su número de factura."""
        files = []
        
        if not os.path.exists(self.folder_path):
            return files
        
        for f in sorted(os.listdir(self.folder_path)):
            if not f.lower().endswith('.pdf'):
                continue
            
            name_upper = f.upper()
            if name_upper.startswith('CRC') or name_upper.startswith('OPF'):
                invoice = self._extract_invoice_number(f)
                files.append((f, invoice))
        
        return files
    
    def _select_folder(self):
        """Selecciona carpeta y carga archivos."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta")
        if not folder:
            return
        
        self.folder_path = folder
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, folder)
        
        self._load_files()
    
    def _load_files(self):
        """Carga archivos en la tabla."""
        # Limpiar tabla
        for item in self.table.get_children():
            self.table.delete(item)
        
        files = self._get_crc_opf_files()
        
        if not files:
            self._log("WARNING", "No se encontraron archivos CRC/OPF.")
            self.current_invoice_lbl.configure(text="---", text_color="gray")
            self.count_lbl.configure(text="0 archivos")
            return
        
        # Detectar número común
        invoices = set()
        
        for filename, invoice in files:
            factura_text = f"IPSP{invoice}" if invoice else "Sin número"
            self.table.insert("", "end", values=(filename, factura_text))
            
            if invoice:
                invoices.add(invoice)
        
        # Mostrar factura actual
        if len(invoices) == 1:
            self.current_invoice = list(invoices)[0]
            self.current_invoice_lbl.configure(text=f"IPSP{self.current_invoice}", text_color="#3b82f6")
            self.new_invoice_entry.delete(0, "end")
            self.new_invoice_entry.insert(0, self.current_invoice)
            self._log("SUCCESS", f"Detectado: IPSP{self.current_invoice} en {len(files)} archivos.")
        elif len(invoices) > 1:
            self.current_invoice = ""
            self.current_invoice_lbl.configure(text="Múltiples", text_color="#f39c12")
            self._log("WARNING", f"Múltiples facturas: {', '.join(['IPSP'+i for i in sorted(invoices)])}")
        else:
            self.current_invoice = ""
            self.current_invoice_lbl.configure(text="Sin número", text_color="gray")
            self._log("INFO", f"{len(files)} archivos sin número de factura.")
        
        self.count_lbl.configure(text=f"{len(files)} archivos")
    
    def _generate_new_filename(self, original: str, new_invoice: str) -> str:
        """Genera nuevo nombre con el número de factura actualizado."""
        # Reemplazar IPSP{número}_ o IPSP_
        pattern = r'(IPSP)(\d*)(_)'
        return re.sub(pattern, rf'\g<1>{new_invoice}\g<3>', original, flags=re.IGNORECASE)
    
    def _update_invoice(self):
        """Actualiza el número de factura en los archivos."""
        new_invoice = self.new_invoice_entry.get().strip()
        
        # Validaciones
        if not self.folder_path:
            self._log("ERROR", "❌ Selecciona una carpeta primero.")
            return
        
        if not new_invoice:
            self._log("ERROR", "❌ Debes ingresar un número de factura.")
            return
        
        if not new_invoice.isdigit():
            self._log("ERROR", "❌ El número de factura debe contener solo dígitos.")
            return
        
        files = self._get_crc_opf_files()
        
        if not files:
            self._log("WARNING", "No hay archivos para renombrar.")
            return
        
        # Renombrar
        success = 0
        errors = 0
        
        for original, current_invoice in files:
            new_name = self._generate_new_filename(original, new_invoice)
            
            if original == new_name:
                continue
            
            original_path = os.path.join(self.folder_path, original)
            new_path = os.path.join(self.folder_path, new_name)
            
            try:
                if os.path.exists(new_path):
                    errors += 1
                    continue
                
                os.rename(original_path, new_path)
                success += 1
                
            except Exception:
                errors += 1
        
        # Resultado
        if success > 0:
            if errors == 0:
                self._log("SUCCESS", f"✅ {success} archivos actualizados a IPSP{new_invoice}.")
            else:
                self._log("WARNING", f"⚠️ {success} actualizados, {errors} errores.")
            
            # Recargar
            self._load_files()
        else:
            self._log("INFO", "No hubo cambios (mismo número o errores).")
    
    def _clear(self):
        """Limpia todo."""
        self.folder_path = ""
        self.current_invoice = ""
        
        self.folder_entry.delete(0, "end")
        self.new_invoice_entry.delete(0, "end")
        self.current_invoice_lbl.configure(text="---", text_color="gray")
        self.count_lbl.configure(text="0 archivos")
        
        for item in self.table.get_children():
            self.table.delete(item)
        
        self._log("INFO", "Limpiado.")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Actualizador de Factura")
    root.geometry("800x550")
    root.minsize(700, 450)
    app = InvoiceNumberUpdaterApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()