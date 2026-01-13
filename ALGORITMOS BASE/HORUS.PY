import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
import time
import random
from openpyxl import load_workbook
import os

# ➕ AGREGADO (para exportar Excel)
from openpyxl import Workbook


class HorusApp:

    TIPOS_DOC = {"CC": 1, "TI": 2, "RC": 3}
    LOGIN_URL = "https://backend.horus-health.com/api/auth/validar-usuario"
    BASE_URL = "https://backend.horus-health.com/api/afiliados/consultar-afiliado"

    def __init__(self):
        self.TOKEN = None
        self.excel_docs = []

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Consulta de Afiliados Horus Health")
        self.root.geometry("1000x750")

        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.crear_ui_login()
        self.crear_ui_entrada()
        self.crear_ui_textbox()
        self.crear_ui_boton_consulta()
        self.crear_ui_tabla()

        self.modo_cambiado("Manual")

        self.root.mainloop()

    # -----------------------------------------
    # UI SECTIONS
    # -----------------------------------------

    def crear_ui_login(self):
        frame = ctk.CTkFrame(self.root)
        frame.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Correo:").grid(row=0, column=0, pady=6, padx=6, sticky="w")
        self.entry_correo = ctk.CTkEntry(frame)
        self.entry_correo.grid(row=0, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(frame, text="Contraseña:").grid(row=1, column=0, pady=6, padx=6, sticky="w")
        self.entry_password = ctk.CTkEntry(frame, show="*")
        self.entry_password.grid(row=1, column=1, pady=6, sticky="ew")

        self.btn_login = ctk.CTkButton(frame, text="Conectar", width=140, command=self.login_usuario)
        self.btn_login.grid(row=0, column=2, rowspan=2, padx=6, pady=6)

        self.label_estado = ctk.CTkLabel(frame, text="DESCONECTADO", text_color="red",
                                         font=("Arial", 13, "bold"))
        self.label_estado.grid(row=0, column=3, rowspan=2, padx=6)

    def crear_ui_entrada(self):
        frame = ctk.CTkFrame(self.root)
        frame.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Modo de entrada:").grid(row=0, column=0, padx=6, pady=6, sticky="w")

        self.mode_selector = ctk.CTkSegmentedButton(
            frame, values=["Manual", "Excel"], command=self.modo_cambiado
        )
        self.mode_selector.grid(row=0, column=1, padx=6, sticky="w")
        self.mode_selector.set("Manual")

        self.btn_select_excel = ctk.CTkButton(frame, text="Seleccionar archivo .xlsx",
                                              command=self.seleccionar_archivo_excel)
        self.label_excel_file = ctk.CTkLabel(frame, text="(ninguno)")

    def crear_ui_textbox(self):
        self.text_lista = ctk.CTkTextbox(self.root, height=220)
        self.text_lista.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.text_lista.grid_columnconfigure(0, weight=1)

    def crear_ui_boton_consulta(self):
        self.btn_consultar = ctk.CTkButton(self.root, text="Consultar Afiliados",
                                           command=self.ejecutar_consulta, width=220)
        self.btn_consultar.grid(row=4, column=0, pady=8)

        # ➕ AGREGADO: Botón Exportar Excel
        self.btn_exportar = ctk.CTkButton(
            self.root, text="Exportar a Excel", width=220, command=self.exportar_excel
        )
        self.btn_exportar.grid(row=5, column=0, pady=8)

    def crear_ui_tabla(self):
        frame = ctk.CTkFrame(self.root)
        frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=8)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        columns = ("documento", "nombre", "estado", "ips")
        self.tabla = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tabla.heading(col, text=col.capitalize())

        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.tabla.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)

        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        self.tabla.grid(row=0, column=0, sticky="nsew")

    # -----------------------------------------
    # LOGIN
    # -----------------------------------------

    def login_usuario(self):
        correo = self.entry_correo.get().strip()
        clave = self.entry_password.get().strip()

        if not correo or not clave:
            messagebox.showwarning("Campos incompletos", "Debes ingresar correo y contraseña.")
            return

        payload = {"email": correo, "password": clave}

        try:
            resp = requests.post(self.LOGIN_URL, json=payload, timeout=10)
            data = resp.json()

            if "token" in data:
                self.TOKEN = data["token"]
                self.label_estado.configure(text="CONECTADO", text_color="green")
                messagebox.showinfo("Conectado", "Inicio de sesión exitoso.")
            else:
                self.TOKEN = None
                self.label_estado.configure(text="DESCONECTADO", text_color="red")
                messagebox.showerror("Error", "Credenciales inválidas.")

        except Exception as e:
            self.TOKEN = None
            self.label_estado.configure(text="DESCONECTADO", text_color="red")
            messagebox.showerror("Error", f"No se pudo conectar: {e}")

    # -----------------------------------------
    # CONSULTAS
    # -----------------------------------------

    def consultar_afiliado(self, documento):
        if not self.TOKEN:
            return documento, "DESCONECTADO", "", ""

        tipo = ''.join([c for c in documento if c.isalpha()]).upper()
        numero = ''.join([c for c in documento if c.isdigit()])

        tipo_id = self.TIPOS_DOC.get(tipo)
        if not tipo_id or not numero:
            return documento, "REVISAR (inválido)", "", ""

        headers = {"Authorization": f"Bearer {self.TOKEN}", "Accept": "application/json"}
        url = f"{self.BASE_URL}/{numero}/{tipo_id}"

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 401:
                self.label_estado.configure(text="DESCONECTADO", text_color="red")
                return documento, "TOKEN INVALIDO", "", ""

            if response.status_code == 200:
                data = response.json()
                nombre = " ".join(filter(None, [
                    data.get("primer_nombre"),
                    data.get("segundo_nombre"),
                    data.get("primer_apellido"),
                    data.get("segundo_apellido")
                ])).strip()

                if not nombre:
                    nombre = "REVISAR (sin nombre)"

                estado = data.get("estado_afiliado", {}).get("nombre", "REVISAR")
                ips = data.get("ips", {}).get("nombre", "REVISAR")

                return documento, nombre, estado, ips

            return documento, f"REVISAR ({response.status_code})", "", ""

        except Exception as e:
            return documento, f"ERROR ({e})", "", ""

    def ejecutar_consulta(self):
        if not self.TOKEN:
            messagebox.showwarning("Sin conexión", "Debes iniciar sesión antes de consultar.")
            return

        documentos = self.obtener_lista_documentos()
        if not documentos:
            messagebox.showwarning("Sin documentos", "Debes ingresar o importar documentos.")
            return

        for row in self.tabla.get_children():
            self.tabla.delete(row)

        self.btn_consultar.configure(state="disabled")

        def tarea():
            for doc in documentos:
                d, n, e, i = self.consultar_afiliado(doc)
                self.tabla.insert("", "end", values=(d, n, e, i))
                time.sleep(random.uniform(2, 3))

            self.btn_consultar.configure(state="normal")
            messagebox.showinfo("Completado", "Consultas finalizadas.")

        threading.Thread(target=tarea, daemon=True).start()

    # -----------------------------------------
    # EXPORTAR A EXCEL (NUEVO)
    # -----------------------------------------

    def exportar_excel(self):
        if not self.tabla.get_children():
            messagebox.showwarning("Sin datos", "No hay datos para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Guardar como"
        )
        if not file_path:
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Afiliados"

            # Encabezados
            ws.append(["Tipo Doc", "Número", "Nombre", "Estado", "IPS"])

            # Procesar filas
            for item in self.tabla.get_children():
                doc, nombre, estado, ips = self.tabla.item(item, "values")

                tipo = "".join([c for c in doc if c.isalpha()]).upper()
                numero = "".join([c for c in doc if c.isdigit()])

                ws.append([tipo, numero, nombre, estado, ips])

            wb.save(file_path)
            messagebox.showinfo("Exportado", "Los datos fueron exportados correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    # -----------------------------------------
    # ENTRADAS
    # -----------------------------------------

    def obtener_lista_documentos(self):
        mode = self.mode_selector.get()
        if mode == "Manual":
            text = self.text_lista.get("1.0", "end").strip()
            return [l.strip() for l in text.splitlines() if l.strip()]
        else:
            return self.excel_docs.copy()

    def seleccionar_archivo_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return

        if not file_path.lower().endswith(".xlsx"):
            messagebox.showerror("Archivo inválido", "Solo se permiten archivos .xlsx")
            return

        try:
            wb = load_workbook(filename=file_path, read_only=True, data_only=True)
            ws = wb.active

            loaded = []
            skipped = 0

            # ➕ CORRECCIÓN (evita duplicados): crear conjunto de ya existentes
            existing_set = set()
            # incluir los ya en self.excel_docs
            existing_set.update([d.strip() for d in self.excel_docs if d and d.strip()])

            # incluir documentos en el TextBox (si hay)
            try:
                text_content = self.text_lista.get("1.0", "end").strip()
                text_items = [l.strip() for l in text_content.splitlines() if l.strip()]
                existing_set.update(text_items)
            except Exception:
                pass

            # incluir documentos que ya estén en la tabla
            try:
                for item in self.tabla.get_children():
                    vals = self.tabla.item(item, "values")
                    if vals:
                        doc_val = vals[0]
                        if doc_val and str(doc_val).strip():
                            existing_set.add(str(doc_val).strip())
            except Exception:
                pass

            for row in ws.iter_rows(min_row=3, values_only=True):
                c = "" if len(row) < 3 or row[2] is None else str(row[2])
                d = "" if len(row) < 4 or row[3] is None else str(row[3])
                val = f"{c}{d}".strip()
                if val:
                    if val in existing_set:
                        skipped += 1
                    else:
                        loaded.append(val)
                        existing_set.add(val)

            # agregar nuevos a self.excel_docs (sin duplicados)
            self.excel_docs.extend(loaded)

            self.label_excel_file.configure(text=os.path.basename(file_path))

            # actualizar text box con hasta 500 elementos (mostrando los actuales + nuevos)
            try:
                self.text_lista.configure(state="normal")
                # construir lista para mostrar: combinar existing items en el orden: self.excel_docs
                mostrar = self.excel_docs[:500]
                self.text_lista.delete("1.0", "end")
                self.text_lista.insert("1.0", "\n".join(mostrar))
                self.text_lista.configure(state="disabled")
            except Exception:
                pass

            messagebox.showinfo("Importado", f"Importados {len(loaded)} documentos. Omitidos {skipped} duplicados.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")

    # -----------------------------------------
    # CAMBIO DE MODO
    # -----------------------------------------

    def modo_cambiado(self, choice):
        if choice == "Manual":
            self.btn_select_excel.grid_forget()
            self.label_excel_file.grid_forget()

            self.text_lista.configure(state="normal", height=220)
        else:
            self.btn_select_excel.grid(row=2, column=1, sticky="w", padx=(10, 0))
            self.label_excel_file.grid(row=2, column=2, sticky="w", padx=(10, 0))

            self.text_lista.configure(state="normal")
            self.text_lista.delete("1.0", "end")
            self.text_lista.configure(state="disabled")
            self.text_lista.configure(height=80)


# -----------------------------------------
# INICIAR APP
# -----------------------------------------

HorusApp()
