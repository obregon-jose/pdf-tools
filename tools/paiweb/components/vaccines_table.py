"""Componente tabla de vacunas"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from utils import format_date


class VaccinesTable(ctk.CTkFrame):
    """Tabla de vacunas con funcionalidad de copiado"""
    
    def __init__(self, master, vaccines_data, **kwargs):
        super().__init__(master, **kwargs)
        self.vaccines_data = vaccines_data
        self.configure(fg_color="#1e1e1e", corner_radius=6)
        self.selected_cell = None
        self._build_table()
    
    def _build_table(self):
        """Construye la tabla de vacunas"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview",
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=25
        )
        style.configure("Treeview.Heading",
            background="#1f6feb",
            foreground="#ffffff",
            borderwidth=1,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview",
            background=[("selected", "#14b97d")],
            foreground=[("selected", "#ffffff")]
        )
        
        columns = ("num", "edad", "dosis", "fecha", "biologico", "lote", "fabricante", "institucion")
        
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            height=8,
            selectmode="browse"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        self.tree.heading("num", text="#")
        self.tree.heading("edad", text="Edad trazadora")
        self.tree.heading("dosis", text="Dosis")
        self.tree.heading("fecha", text="Fecha de aplicación")
        self.tree.heading("biologico", text="Biológico")
        self.tree.heading("lote", text="Lote")
        self.tree.heading("fabricante", text="Fabricante")
        self.tree.heading("institucion", text="Institución")
        
        self.tree.column("num", width=40, anchor="center", minwidth=40)
        self.tree.column("edad", width=120, anchor="w", minwidth=80)
        self.tree.column("dosis", width=120, anchor="w", minwidth=80)
        self.tree.column("fecha", width=110, anchor="center", minwidth=90)
        self.tree.column("biologico", width=200, anchor="w", minwidth=150)
        self.tree.column("lote", width=100, anchor="w", minwidth=80)
        self.tree.column("fabricante", width=150, anchor="w", minwidth=100)
        self.tree.column("institucion", width=250, anchor="w", minwidth=150)
        
        for idx, vaccine in enumerate(self.vaccines_data, 1):
            values = (
                idx,
                vaccine.get("edad", "N/A"),
                vaccine.get("dosis", "N/A"),
                format_date(vaccine.get("fechaAplicacion", "")),
                vaccine.get("biologico", "N/A"),
                vaccine.get("lote", "N/A") or "N/A",
                vaccine.get("fabricante", "N/A"),
                vaccine.get("institucionVacunadora", "N/A")
            )
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=values, tags=(tag,))
        
        self.tree.tag_configure("evenrow", background="#2b2b2b")
        self.tree.tag_configure("oddrow", background="#333333")
        
        self.tree.bind("<ButtonRelease-1>", self._on_click)
        self.tree.bind("<Double-Button-1>", self._on_double_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Control-c>", self._copy_cell)
        self.tree.bind("<Control-C>", self._copy_cell)
        
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="📋 Copiar celda (Ctrl+C)", command=lambda: self._copy_cell(None))
        self.context_menu.add_command(label="📄 Copiar fila completa", command=self._copy_row)
        self.context_menu.add_command(label="📊 Copiar todas las filas", command=self._copy_all_rows)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        help_label = ctk.CTkLabel(
            self,
            text="💡 Tip: Click en celda → Ctrl+C para copiar | Doble click para copiar rápido",
            font=ctk.CTkFont(size=10),
            text_color="#7f8c8d"
        )
        help_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
    
    def _on_motion(self, event):
        region = self.tree.identify("region", event.x, event.y)
        self.tree.configure(cursor="hand2" if region == "cell" else "")
    
    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if item and column:
                self.tree.selection_set(item)
                self.selected_cell = (item, column)
    
    def _on_double_click(self, event):
        self._on_click(event)
        if self.selected_cell:
            self._copy_cell(None)
    
    def _copy_cell(self, event):
        if not self.selected_cell:
            return "break"
        
        item, column = self.selected_cell
        col_index = int(column.replace('#', '')) - 1
        values = self.tree.item(item)["values"]
        
        if col_index < len(values):
            cell_value = str(values[col_index])
            self.clipboard_clear()
            self.clipboard_append(cell_value)
        
        return "break"
    
    def _copy_row(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0])["values"]
        text = "\t".join(str(v) for v in values)
        self.clipboard_clear()
        self.clipboard_append(text)
    
    def _copy_all_rows(self):
        headers = [self.tree.heading(col)["text"] for col in self.tree["columns"]]
        lines = ["\t".join(headers)]
        
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            lines.append("\t".join(str(v) for v in values))
        
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
    
    def _show_context_menu(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if item and column:
                self.tree.selection_set(item)
                self.selected_cell = (item, column)
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()