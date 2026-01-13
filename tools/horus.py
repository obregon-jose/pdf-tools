import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import requests
import threading
import time
import random
from openpyxl import load_workbook, Workbook
import os

class HorusApp(ctk. CTkFrame):
    """
    Aplicación para consulta de afiliados en Horus Health. 
    Diseño basado en el modelo PDFSplitterApp.
    """
    
    # Constantes de la API
    DOC_TYPES = {"CC": 1, "TI": 2, "RC": 3}
    LOGIN_URL = "https://backend.horus-health.com/api/auth/validar-usuario"
    BASE_URL = "https://backend.horus-health.com/api/afiliados/consultar-afiliado"
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # ===== ESTADO DE LA APLICACIÓN =====
        self. token = None
        self.excel_docs = []
        self. is_processing = False
        
        # Variables observables
        self.input_mode_var = ctk.StringVar(value="Manual")
        
        # ===== CONSTRUIR UI =====
        self._create_widgets()
    
    # ==================== CONSTRUCCIÓN DE UI ====================
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz siguiendo el diseño del modelo."""
        
        # ===== FRAME SUPERIOR - LOGIN (contenedor compacto) =====
        login_frame = ctk.CTkFrame(self)
        login_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: Correo electrónico
        lbl_email = ctk.CTkLabel(login_frame, text="Correo:", width=70, anchor="w")
        lbl_email.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.email_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Ingresa tu correo electrónico",
            width=400
        )
        self.email_entry.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        
        # Fila 1: Contraseña
        lbl_password = ctk.CTkLabel(login_frame, text="Contraseña:", width=70, anchor="w")
        lbl_password. grid(row=1, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self. password_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Ingresa tu contraseña",
            width=400,
            show="*"
        )
        self.password_entry.grid(row=1, column=1, padx=(0, 6), pady=4, sticky="we")
        
        # Botón conectar y estado
        self.login_button = ctk.CTkButton(
            login_frame,
            text="Conectar",
            width=140,
            command=self._on_login,
            fg_color="#1f6feb"  # Azul del modelo
        )
        self.login_button.grid(row=0, column=2, rowspan=2, padx=(0, 6), pady=4)
        
        self.status_label = ctk.CTkLabel(
            login_frame,
            text="⚫ DESCONECTADO",
            text_color="red",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=120
        )
        self.status_label.grid(row=0, column=3, rowspan=2, padx=(0, 6), pady=4)
        
        login_frame.grid_columnconfigure(1, weight=1)
        
        # ===== FRAME DE ENTRADA DE DATOS =====
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: Modo de entrada
        lbl_mode = ctk.CTkLabel(input_frame, text="Modo:", width=70, anchor="w")
        lbl_mode.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.mode_selector = ctk.CTkSegmentedButton(
            input_frame,
            values=["Manual", "Excel"],
            command=self._on_mode_changed,
            width=200
        )
        self.mode_selector.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="w")
        self.mode_selector.set("Manual")
        
        # Botón seleccionar Excel (oculto inicialmente)
        self.select_excel_button = ctk. CTkButton(
            input_frame,
            text="Seleccionar Excel",
            width=140,
            command=self._on_select_excel
        )
        
        # Label archivo Excel (oculto inicialmente)
        self.excel_file_label = ctk.CTkLabel(
            input_frame,
            text="(ninguno)",
            text_color="gray",
            anchor="w"
        )
        
        # Fila 1: Espaciador
        spacer = ctk.CTkFrame(input_frame, height=2)
        spacer.grid(row=1, column=0, columnspan=4)
        
        # Fila 2: Botones de acción
        btn_frame = ctk.CTkFrame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        
        self.query_button = ctk.CTkButton(
            btn_frame,
            text="🔍 Consultar Afiliados",
            command=self._on_query,
            fg_color="#1f6feb"  # Azul del modelo
        )
        self.query_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self.export_button = ctk.CTkButton(
            btn_frame,
            text="📥 Exportar a Excel",
            command=self._on_export_excel,
            fg_color="#f0ad4e",  # Amarillo/naranja del modelo
            text_color="black"
        )
        self.export_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        
        self.clear_button = ctk.CTkButton(
            btn_frame,
            text="🧹 Limpiar Todo",
            command=self._on_clear_all
        )
        self.clear_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        input_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE ENTRADA DE DOCUMENTOS =====
        self.docs_frame = ctk.CTkFrame(self)
        self.docs_frame.pack(fill="x", padx=6, pady=6)
        
        # Nota informativa
        self.info_note = ctk.CTkLabel(
            self.docs_frame,
            text="Nota:  Ingresa los documentos en formato TIPO+NÚMERO (ej: CC123456789). Uno por línea.",
            text_color="gray",
            font=("Arial", 12, "bold")
        )
        self.info_note.grid(row=0, column=0, sticky="w", padx=4, pady=(2, 4))
        
        # Área de texto para documentos
        self.docs_textbox = ctk.CTkTextbox(
            self.docs_frame,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.docs_textbox.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        
        self.docs_frame.grid_rowconfigure(1, weight=1)
        self.docs_frame.grid_columnconfigure(0, weight=1)
        
        # ===== PANEL DE RESULTADOS (TABLA) =====
        self.results_frame = ctk. CTkFrame(self)
        self.results_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Nota de resultados
        self.results_note = ctk.CTkLabel(
            self.results_frame,
            text="📊 Resultados de la consulta",
            text_color="gray",
            font=("Arial", 12, "bold")
        )
        self.results_note.grid(row=0, column=0, sticky="w", padx=4, pady=(2, 4))
        
        # Contador de resultados
        self.counter_label = ctk.CTkLabel(
            self.results_frame,
            text="0 registros",
            text_color="gray",
            anchor="e"
        )
        self.counter_label.grid(row=0, column=1, sticky="e", padx=4, pady=(2, 4))
        
        # Frame para la tabla con scrollbars
        table_container = ctk.CTkFrame(self.results_frame)
        table_container.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=2)
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # Configurar estilo de la tabla para modo oscuro
        self._setup_table_style()
        
        # Tabla de resultados
        columns = ("documento", "nombre", "estado", "ips")
        self.results_table = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            style="Dark.Treeview"
        )
        
        # Configurar encabezados
        self.results_table.heading("documento", text="Documento")
        self.results_table.heading("nombre", text="Nombre Completo")
        self.results_table.heading("estado", text="Estado")
        self.results_table.heading("ips", text="IPS")
        
        # Configurar anchos de columna
        self.results_table.column("documento", width=120, minwidth=100)
        self.results_table.column("nombre", width=300, minwidth=200)
        self.results_table.column("estado", width=150, minwidth=100)
        self.results_table.column("ips", width=200, minwidth=150)
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(table_container, orient="vertical", command=self.results_table.yview)
        scroll_x = ttk.Scrollbar(table_container, orient="horizontal", command=self.results_table. xview)
        self.results_table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # Posicionar tabla y scrollbars
        self.results_table.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        self.results_frame.grid_rowconfigure(1, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        # ===== FRAME INFERIOR (Estado y Progreso) =====
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=6, pady=6)
        
        # Barra de progreso
        self.progressbar = ctk.CTkProgressBar(bottom_frame, height=12, corner_radius=5)
        self.progressbar. pack(fill="x", padx=6, pady=(6, 2))
        self.progressbar.set(0)
        
        # Etiqueta de estado
        self.process_status_label = ctk.CTkLabel(
            bottom_frame,
            text="⏳ Esperando acción...",
            text_color="gray",
            anchor="w"
        )
        self.process_status_label.pack(fill="x", padx=6, pady=(2, 6))
    
    def _setup_table_style(self):
        """Configura el estilo de la tabla para modo oscuro."""
        style = ttk.Style()
        
        # Configurar colores para modo oscuro
        style.theme_use("default")
        
        style.configure(
            "Dark.Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0,
            rowheight=28
        )
        
        style.configure(
            "Dark. Treeview.Heading",
            background="#3b3b3b",
            foreground="white",
            borderwidth=1
        )
        
        style. map(
            "Dark.Treeview",
            background=[("selected", "#1f6feb")],
            foreground=[("selected", "white")]
        )
    
    # ==================== MANEJADORES DE EVENTOS ====================
    
    def _on_mode_changed(self, choice):
        """Maneja el cambio de modo de entrada (Manual/Excel)."""
        if choice == "Manual":
            # Ocultar controles de Excel
            self.select_excel_button.grid_forget()
            self.excel_file_label.grid_forget()
            
            # Habilitar textbox
            self.docs_textbox.configure(state="normal")
            self.info_note.configure(
                text="Nota: Ingresa los documentos en formato TIPO+NÚMERO (ej: CC123456789). Uno por línea."
            )
        else:
            # Mostrar controles de Excel
            self. select_excel_button.grid(row=0, column=2, padx=(6, 4), pady=4)
            self.excel_file_label.grid(row=0, column=3, padx=(0, 6), pady=4, sticky="w")
            
            # Limpiar y deshabilitar textbox
            self.docs_textbox.configure(state="normal")
            self.docs_textbox.delete("1.0", "end")
            self.docs_textbox.configure(state="disabled")
            self.info_note.configure(
                text="Nota: Selecciona un archivo Excel con los documentos.  Se leerán desde la fila 3, columnas C y D."
            )
    
    def _on_select_excel(self):
        """Abre diálogo para seleccionar archivo Excel."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )
        
        if not file_path:
            return
        
        if not file_path.lower().endswith(".xlsx"):
            messagebox.showerror("Archivo inválido", "Solo se permiten archivos .xlsx")
            return
        
        self._load_excel_file(file_path)
    
    def _load_excel_file(self, file_path):
        """Carga documentos desde archivo Excel."""
        try:
            wb = load_workbook(filename=file_path, read_only=True, data_only=True)
            ws = wb.active
            
            loaded = []
            skipped = 0
            
            # Crear conjunto de documentos existentes para evitar duplicados
            existing_set = set()
            existing_set.update([d.strip() for d in self.excel_docs if d and d.strip()])
            
            # Incluir documentos en la tabla
            try:
                for item in self.results_table.get_children():
                    vals = self.results_table.item(item, "values")
                    if vals and vals[0]: 
                        existing_set.add(str(vals[0]).strip())
            except Exception: 
                pass
            
            # Leer filas del Excel (desde fila 3, columnas C y D)
            for row in ws.iter_rows(min_row=3, values_only=True):
                col_c = "" if len(row) < 3 or row[2] is None else str(row[2])
                col_d = "" if len(row) < 4 or row[3] is None else str(row[3])
                val = f"{col_c}{col_d}".strip()
                
                if val:
                    if val in existing_set:
                        skipped += 1
                    else:
                        loaded. append(val)
                        existing_set.add(val)
            
            # Agregar nuevos documentos
            self.excel_docs.extend(loaded)
            
            # Actualizar label de archivo
            self.excel_file_label.configure(
                text=f"📁 {os.path.basename(file_path)}",
                text_color="white"
            )
            
            # Mostrar documentos en textbox (máximo 500)
            try:
                self.docs_textbox.configure(state="normal")
                display_docs = self.excel_docs[:500]
                self.docs_textbox.delete("1.0", "end")
                self.docs_textbox. insert("1.0", "\n".join(display_docs))
                self.docs_textbox. configure(state="disabled")
            except Exception:
                pass
            
            messagebox.showinfo(
                "Importado",
                f"✓ Importados {len(loaded)} documentos.\n⚠️ Omitidos {skipped} duplicados."
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{str(e)}")
    
    def _on_clear_all(self):
        """Limpia todos los datos y resultados."""
        # Limpiar textbox
        self.docs_textbox.configure(state="normal")
        self.docs_textbox.delete("1.0", "end")
        if self.mode_selector.get() == "Excel":
            self.docs_textbox.configure(state="disabled")
        
        # Limpiar tabla
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        
        # Limpiar estado
        self.excel_docs.clear()
        self.excel_file_label.configure(text="(ninguno)", text_color="gray")
        self.counter_label.configure(text="0 registros")
        self.progressbar.set(0)
        self.process_status_label.configure(text="⏳ Esperando acción.. .", text_color="gray")
        
        messagebox.showinfo("Limpiar", "Se han limpiado todos los datos y resultados.")
    
    # ==================== LOGIN ====================
    
    def _on_login(self):
        """Realiza el inicio de sesión en la API."""
        email = self.email_entry.get().strip()
        password = self. password_entry.get().strip()
        
        if not email or not password:
            messagebox. showwarning("Campos incompletos", "Debes ingresar correo y contraseña.")
            return
        
        payload = {"email": email, "password": password}
        
        try: 
            response = requests.post(self.LOGIN_URL, json=payload, timeout=10)
            data = response.json()
            
            if "token" in data:
                self. token = data["token"]
                self.status_label.configure(text="🟢 CONECTADO", text_color="green")
                messagebox.showinfo("Conectado", "✓ Inicio de sesión exitoso.")
            else:
                self.token = None
                self.status_label.configure(text="�� DESCONECTADO", text_color="red")
                messagebox.showerror("Error", "Credenciales inválidas.")
                
        except Exception as e:
            self.token = None
            self. status_label.configure(text="⚫ DESCONECTADO", text_color="red")
            messagebox.showerror("Error", f"No se pudo conectar:\n{str(e)}")
    
    # ==================== CONSULTAS ====================
    
    def _get_document_list(self):
        """Obtiene la lista de documentos según el modo de entrada."""
        mode = self.mode_selector.get()
        
        if mode == "Manual":
            text = self.docs_textbox. get("1.0", "end").strip()
            return [line.strip() for line in text.splitlines() if line.strip()]
        else:
            return self.excel_docs. copy()
    
    def _query_affiliate(self, document):
        """Consulta un afiliado individual en la API."""
        if not self.token:
            return document, "DESCONECTADO", "", ""
        
        # Extraer tipo y número del documento
        doc_type = ''.join([c for c in document if c. isalpha()]).upper()
        doc_number = ''.join([c for c in document if c.isdigit()])
        
        type_id = self.DOC_TYPES.get(doc_type)
        if not type_id or not doc_number:
            return document, "REVISAR (formato inválido)", "", ""
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        url = f"{self.BASE_URL}/{doc_number}/{type_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                self.status_label.configure(text="⚫ DESCONECTADO", text_color="red")
                return document, "TOKEN INVÁLIDO", "", ""
            
            if response.status_code == 200:
                data = response.json()
                
                # Construir nombre completo
                name = " ".join(filter(None, [
                    data.get("primer_nombre"),
                    data.get("segundo_nombre"),
                    data. get("primer_apellido"),
                    data.get("segundo_apellido")
                ])).strip()
                
                if not name:
                    name = "REVISAR (sin nombre)"
                
                status = data.get("estado_afiliado", {}).get("nombre", "REVISAR")
                ips = data.get("ips", {}).get("nombre", "REVISAR")
                
                return document, name, status, ips
            
            return document, f"REVISAR ({response.status_code})", "", ""
            
        except Exception as e:
            return document, f"ERROR ({str(e)})", "", ""
    
    def _on_query(self):
        """Ejecuta la consulta de afiliados."""
        if not self.token:
            messagebox.showwarning("Sin conexión", "Debes iniciar sesión antes de consultar.")
            return
        
        documents = self._get_document_list()
        
        if not documents:
            messagebox.showwarning("Sin documentos", "Debes ingresar o importar documentos.")
            return
        
        # Limpiar tabla anterior
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        
        # Deshabilitar botones durante el proceso
        self.query_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.is_processing = True
        
        def query_task():
            total = len(documents)
            
            for idx, doc in enumerate(documents):
                # Consultar afiliado
                d, n, e, i = self._query_affiliate(doc)
                
                # Insertar en tabla (desde hilo principal)
                self.after(0, lambda vals=(d, n, e, i): self.results_table.insert("", "end", values=vals))
                
                # Actualizar progreso
                progress = (idx + 1) / total
                self.after(0, lambda p=progress, c=idx+1, t=total: self._update_progress(p, c, t))
                
                # Esperar entre consultas (evitar saturar la API)
                time.sleep(random.uniform(2, 3))
            
            # Finalizar
            self.after(0, self._on_query_complete)
        
        # Iniciar hilo de consulta
        threading.Thread(target=query_task, daemon=True).start()
    
    def _update_progress(self, progress, current, total):
        """Actualiza la barra de progreso y el estado."""
        self.progressbar.set(progress)
        self.process_status_label.configure(
            text=f"⏳ Consultando...  {current}/{total} ({int(progress*100)}%)",
            text_color="orange"
        )
        self.counter_label.configure(text=f"{current} registros")
    
    def _on_query_complete(self):
        """Maneja la finalización de las consultas."""
        self.is_processing = False
        self.query_button.configure(state="normal")
        self.export_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        
        total = len(self.results_table.get_children())
        self.progressbar.set(1)
        self.process_status_label.configure(
            text=f"✅ Consultas finalizadas. {total} registros procesados.",
            text_color="green"
        )
        
        messagebox.showinfo("Completado", f"✓ Consultas finalizadas.\n{total} registros procesados.")
    
    # ==================== EXPORTAR EXCEL ====================
    
    def _on_export_excel(self):
        """Exporta los resultados a un archivo Excel."""
        if not self.results_table.get_children():
            messagebox.showwarning("Sin datos", "No hay datos para exportar.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
            title="Guardar como"
        )
        
        if not file_path:
            return
        
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Afiliados"
            
            # Encabezados
            ws. append(["Tipo Doc", "Número", "Nombre", "Estado", "IPS"])
            
            # Procesar filas
            for item in self.results_table.get_children():
                doc, nombre, estado, ips = self. results_table.item(item, "values")
                
                # Separar tipo y número
                tipo = "". join([c for c in doc if c.isalpha()]).upper()
                numero = "". join([c for c in doc if c.isdigit()])
                
                ws.append([tipo, numero, nombre, estado, ips])
            
            wb. save(file_path)
            
            messagebox.showinfo(
                "Exportado",
                f"✓ Los datos fueron exportados correctamente.\n\n{file_path}"
            )
            
        except Exception as e: 
            messagebox.showerror("Error", f"No se pudo exportar:\n{str(e)}")

        
        