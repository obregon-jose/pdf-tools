import os
import re
import requests
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_SEARCH_URL = "https://paiwebservices.paiweb.gov.co:8081/api/v2/Paciente/GetList"
API_CARNET_URL = "https://paiwebservices.paiweb.gov.co:8081/api/Carnet"

# Carpeta Descargas por defecto
DOWNLOADS_FOLDER = str(Path.home() / "Downloads") if (Path.home() / "Downloads").exists() else str(Path.home() / "Descargas")

# Opciones de formato de nombre de archivo
FILENAME_OPTIONS = [
    "Nombre Completo",
    "Nombre Completo + Documento",
    "Nombre Completo + Tipo + Documento",
    "Nombre Completo + Tipo_Documento"
]


def validar_token(token):
    try:
        res = requests.get(
            "https://paiwebservices.paiweb.gov.co:8081/api/Login/ValidateToken",
            cookies={"access_token": token},
            timeout=10, verify=False)
        return res.status_code == 200 and res.json() is True
    except Exception:
        return False


def nombre_completo(datos):
    partes = [
        datos.get("primerNombre", "").strip(),
        datos.get("segundoNombre", "").strip(),
        datos.get("primerApellido", "").strip(),
        datos.get("segundoApellido", "").strip()
    ]
    return " ".join([p for p in partes if p]).upper().strip()


def limpiar_nombre_archivo(nombre):
    base, ext = os.path.splitext(nombre)
    permitido = re.compile(r"[^\wÁÉÍÓÚáéíóúÑñ\s]+", re.UNICODE)
    base_limpio = permitido.sub("", base).strip()[:80]
    return base_limpio + ext


def generar_nombre_archivo(nombre_full, tdoc, ndoc, formato_idx):
    """Genera el nombre del archivo según el formato seleccionado."""
    if formato_idx == 0:
        nombre = f"{nombre_full}.pdf"
    elif formato_idx == 1:
        nombre = f"{nombre_full} {ndoc}.pdf"
    elif formato_idx == 2:
        nombre = f"{nombre_full} {tdoc}{ndoc}.pdf"
    else:
        nombre = f"{nombre_full} {tdoc}_{ndoc}.pdf"
    return limpiar_nombre_archivo(nombre)


def resolver_ruta(user_input):
    """Si empieza con / o es relativa, crea subcarpeta en Descargas."""
    user_input = user_input.strip()
    if not user_input:
        return DOWNLOADS_FOLDER
    if user_input.startswith('/') or user_input.startswith('\\') or not os.path.isabs(user_input):
        carpeta = os.path.join(DOWNLOADS_FOLDER, user_input.lstrip('/\\'))
    else:
        carpeta = user_input
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


class PAIWebCarnetsManager(ctk.CTkFrame):
    """
    Descarga masiva de carnets PDF de PAIWeb mostrando los no-descargados en panel derecho, oculto al inicio.
    El panel se adapta al tamaño y muestra los fallidos sólo al finalizar la ejecución.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.area_font_default = 13
        self.report_font_default = 12
        self.pack(fill="both", expand=True)
        self._build_ui()
        self.report_visible = False
        self._make_responsive()

    def _make_responsive(self):
        """Configura el resize y responsividad del contenido."""
        self.bind("<Configure>", self._resize_texts)

    def _resize_texts(self, event=None):
        w = self.winfo_width()
        font_area_size = max(12, min(20, int(w/65)))
        font_report_size = max(11, min(18, int(w/78)))
        self.area.configure(font=("Consolas", font_area_size))
        self.text_report.configure(font=("Consolas", font_report_size))

    def _build_ui(self):
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky='nsew')

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # === Panel superior: Token, Carpeta y Formato ===
        panel_top = ctk.CTkFrame(self.main_container)
        panel_top.grid(row=0, column=0, sticky='ew', padx=6, pady=(8,3))
        panel_top.grid_columnconfigure(1, weight=1)

        lbl_token = ctk.CTkLabel(panel_top, text="🔑 Access Token:", width=120, anchor="w", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_token.grid(row=0, column=0, padx=(6,3), pady=3, sticky="w")
        self.tk_token = ctk.CTkEntry(panel_top, font=ctk.CTkFont(size=13))
        self.tk_token.grid(row=0, column=1, padx=4, pady=3, sticky="ew")
        self.tk_token.insert(0, "")
        btn_pegar_token = ctk.CTkButton(panel_top, text="Pegar token", command=self._paste_token, width=110, fg_color="#476cb2")
        btn_pegar_token.grid(row=0, column=2, padx=(6,2), pady=3, sticky="w")

        lbl_dest = ctk.CTkLabel(panel_top, text="📁 Carpeta destino:", width=120, anchor="w")
        lbl_dest.grid(row=1, column=0, padx=(6,3), pady=3, sticky="w")
        self.destino = ctk.CTkEntry(panel_top, font=ctk.CTkFont(size=12))
        self.destino.grid(row=1, column=1, padx=4, pady=3, sticky="ew")
        self.destino.insert(0, DOWNLOADS_FOLDER)
        btn_folder = ctk.CTkButton(panel_top, text="Seleccionar carpeta", command=self._choose_folder, width=120)
        btn_folder.grid(row=1, column=2, padx=(6,2), pady=3, sticky="w")

        lbl_formato = ctk.CTkLabel(panel_top, text="📝 Convencio de nombre para archivos:", width=120, anchor="w")
        lbl_formato.grid(row=2, column=0, padx=(6,3), pady=3, sticky="w")
        self.formato_selector = ctk.CTkComboBox(panel_top, values=FILENAME_OPTIONS, state="readonly", font=ctk.CTkFont(size=12), width=280)
        self.formato_selector.grid(row=2, column=1, padx=4, pady=3, sticky="w")
        self.formato_selector.set(FILENAME_OPTIONS[0])

        # === Panel central: Documentos + Panel de errores (lado a lado) ===
        self.panel_docs_container = ctk.CTkFrame(self.main_container)
        self.panel_docs_container.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.panel_docs_container.grid_columnconfigure(0, weight=1)
        self.panel_docs_container.grid_rowconfigure(0, weight=1)

        # --- Panel izquierdo: Input de documentos ---
        panel_docs = ctk.CTkFrame(self.panel_docs_container)
        panel_docs.grid(row=0, column=0, sticky="nsew", padx=(0,0), pady=0)
        panel_docs.grid_columnconfigure(0, weight=1)
        panel_docs.grid_rowconfigure(1, weight=1)

        self.lbl_docs = ctk.CTkLabel(panel_docs, text="📑 Documentos: 0 (uno por línea)", font=ctk.CTkFont(size=13,weight="bold"))
        self.lbl_docs.grid(row=0, column=0, sticky="w", padx=(7,4), pady=(8,1), columnspan=2)
        self.area = ctk.CTkTextbox(panel_docs, font=("Consolas", self.area_font_default), border_width=2)
        self.area.grid(row=1, column=0, sticky="nsew", padx=(8,6), pady=(0,5))
        self.area.bind("<<Modified>>", self._on_text_edit)
        btns_panel = ctk.CTkFrame(panel_docs)
        btns_panel.grid(row=1, column=1, sticky="ns", padx=(2,7), pady=(0,5))
        btns_panel.grid_rowconfigure((0,1,2), weight=1)
        btn_paste = ctk.CTkButton(btns_panel, text="📋 Pegar Documentos", command=self._paste_clipboard, width=136, fg_color="#1f6feb")
        btn_paste.grid(row=0, column=0, pady=(4,4), sticky="ew")
        btn_limpiar = ctk.CTkButton(btns_panel, text="🧹 Limpiar panel", command=self._clear_docs, width=136, fg_color="#e74c3c", text_color="white")
        btn_limpiar.grid(row=1, column=0, pady=(2,4), sticky="ew")
        self.bt = ctk.CTkButton(
            btns_panel, text="🚀 Descargar Carnets",
            command=self._start_download, fg_color="#14b97d", font=ctk.CTkFont(size=15, weight="bold"),
            width=136, height=36
        )
        self.bt.grid(row=2, column=0, pady=(14,4), sticky="ew")

        # --- Panel derecho: Reporte de no descargados (oculto inicialmente, sin espacio reservado) ---
        self.panel_report = ctk.CTkFrame(self.panel_docs_container)
        self.panel_report.grid_columnconfigure(0, weight=1)
        self.panel_report.grid_rowconfigure(1, weight=1)

        self.lbl_report_title = ctk.CTkLabel(
            self.panel_report,
            text="❌ Documentos NO descargados",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e17055",
            anchor="w"
        )
        self.lbl_report_title.grid(row=0, column=0, padx=9, pady=(8,4), sticky="w")
        self.text_report = ctk.CTkTextbox(
            self.panel_report,
            font=("Consolas", self.report_font_default),
            border_width=2,
            text_color="#e17055"
        )
        self.text_report.grid(row=1, column=0, padx=8, pady=(0,8), sticky="nsew")

        # === Panel inferior: Log ===
        panel_action = ctk.CTkFrame(self.main_container)
        panel_action.grid(row=2, column=0, sticky="nsew", padx=7, pady=(3,8))
        panel_action.grid_columnconfigure(0, weight=1)
        panel_action.grid_rowconfigure(0, weight=1)
        self.logbox = ctk.CTkTextbox(
            panel_action,
            font=("Consolas", 11),
            corner_radius=12,
            border_color="#1f3552",
            height=120
        )
        self.logbox.grid(row=0, column=0, sticky="nsew", padx=4, pady=7)
        self.logbox.configure(state="disabled")
        self._log_info("Listo para comenzar.", "INFO")

    def _choose_folder(self):
        carpeta = filedialog.askdirectory(title="Selecciona carpeta destino")
        if carpeta:
            self.destino.delete(0, tk.END)
            self.destino.insert(0, carpeta)

    def _paste_token(self):
        try:
            t = self.clipboard_get().strip()
            self.tk_token.delete(0, tk.END)
            self.tk_token.insert(0, t)
            self._log_info("Token pegado desde portapapeles.", "SUCCESS")
        except Exception:
            messagebox.showerror("Portapapeles", "No se pudo obtener el token del portapapeles.")

    def _paste_clipboard(self):
        try:
            texto = self.clipboard_get()
            lines = [l.strip() for l in texto.replace("\r", "").split("\n") if l.strip()]
            added = 0
            for doc in lines:
                docnum = re.sub(r"\D", "", doc)
                if docnum:
                    self.area.insert("end", docnum + "\n")
                    added += 1
            self._update_doc_count()
            self._log_info(f"Se agregaron {added} documentos desde portapapeles.", "SUCCESS")
        except Exception:
            messagebox.showerror("Portapapeles", "No se pudo obtener el texto del portapapeles.")

    def _clear_docs(self):
        self.area.delete("1.0", tk.END)
        self._update_doc_count()
        self._log_info("Panel de documentos limpiado.", "INFO")
        self._hide_report_panel()

    def _on_text_edit(self, event=None):
        self.area.edit_modified(False)
        self._update_doc_count()

    def _get_documents(self):
        return [re.sub(r"\D", "", l.strip()) for l in self.area.get("1.0", "end").splitlines() if l.strip() and len(re.sub(r"\D", "", l.strip())) > 3]

    def _update_doc_count(self):
        count = len(self._get_documents())
        self.lbl_docs.configure(text=f"📑 Documentos: {count} (uno por línea)")

    def _get_filename_format_index(self):
        """Obtiene el índice del formato seleccionado."""
        try:
            return FILENAME_OPTIONS.index(self.formato_selector.get())
        except ValueError:
            return 0

    def _log_info(self, msg, t="INFO"):
        self.logbox.configure(state="normal")
        color = {"INFO":"#7f8c8d","ERROR":"#e74c3c","SUCCESS":"#27ae60","WARN":"#fbc531"}.get(t,"#636e72")
        try:
            self.logbox.insert("end", f"[{t}] {msg}\n")
        except Exception:
            self.logbox.insert("end", f"[{t}] (error codificación)\n")
        self.logbox.tag_config(t, foreground=color)
        self.logbox.tag_add(t, "end-2l", "end-1l")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")
        self.update()

    def _show_report_panel(self, docs_no_encontrados):
        self.text_report.configure(state="normal")
        self.text_report.delete("1.0", tk.END)
        for idx, item in enumerate(docs_no_encontrados, 1):
            self.text_report.insert("end", f"{idx}. {item}\n")
        self.text_report.configure(state="disabled")
        self.panel_docs_container.grid_columnconfigure(1, weight=1)
        self.panel_report.grid(row=0, column=1, sticky="nsew", padx=(5,0), pady=0)
        self.report_visible = True

    def _hide_report_panel(self):
        self.panel_report.grid_forget()
        self.panel_docs_container.grid_columnconfigure(1, weight=0)
        self.report_visible = False

    def _start_download(self):
        self.bt.configure(state="disabled", fg_color="#888")
        self.update()
        self._hide_report_panel()

        token = self.tk_token.get().strip()
        if not token:
            self._log_info("Ingresa tu access_token.","ERROR")
            messagebox.showerror("Error de acceso", "Debes ingresar un access_token válido.")
            self.bt.configure(state="normal", fg_color="#14b97d")
            return

        self._log_info("Validando token...", "INFO")
        if not validar_token(token):
            self._log_info("El access_token es inválido o expiró. Ingresa uno nuevo.","ERROR")
            messagebox.showerror("Token inválido","El access_token es inválido o expiró. Ingresa uno nuevo.")
            self.bt.configure(state="normal", fg_color="#14b97d")
            return

        documentos = self._get_documents()
        if not documentos:
            self._log_info("No se ingresaron números de documento.","ERROR")
            messagebox.showerror("Falta documentos", "No se detectaron números de documento válidos.")
            self.bt.configure(state="normal", fg_color="#14b97d")
            return

        carpeta = resolver_ruta(self.destino.get())
        formato_idx = self._get_filename_format_index()

        session = requests.Session()
        session.cookies.set("access_token", token)
        headers = {"Content-Type":"application/json"}

        total = len(documentos)
        success, failed = 0, 0
        docs_no_encontrados = []

        for idx, ndoc in enumerate(documentos, 1):
            self._log_info(f"-- [{idx}/{total}] Buscando datos de {ndoc}...", "INFO")
            payload = {
                "size": 10, "totalElements": 0, "totalPages": 0, "pageNumber": 0,
                "data": {
                    "numeroIdentificacion": ndoc,
                    "tipoDocumento": {},
                    "numeroIdentificacionCuidador": "",
                    "type": "basic"
                }
            }
            motivo_fallo = ""
            try:
                res = session.post(API_SEARCH_URL, json=payload, headers=headers, timeout=20, verify=False)
                jres = res.json() if res.status_code == 200 else {}
                if not jres or not jres.get('data'):
                    motivo_fallo = "No encontrado en sistema"
                    self._log_info(f"No encontrado: {ndoc}","WARN")
                    docs_no_encontrados.append(f"{ndoc}: {motivo_fallo}")
                    failed += 1
                    continue

                data_list = jres.get("data", [])
                if not data_list:
                    motivo_fallo = "No encontrado en sistema"
                    self._log_info(f"No encontrado: {ndoc}","WARN")
                    docs_no_encontrados.append(f"{ndoc}: {motivo_fallo}")
                    failed += 1
                    continue

                paciente = data_list[0]
                tdoc = paciente.get("tipoIdentificacionCodigo", "")
                ndoc_real = paciente.get("numeroIdentificacion", ndoc)
                fnac = paciente.get("fechaNacimiento", "")[:10]
                nombre_full = nombre_completo(paciente)
                payload_carnet = {
                    "fechaNacimiento": fnac,
                    "tipoDocumento": tdoc,
                    "numeroDocumento": ndoc_real,
                    "nombreCompleto": nombre_full
                }
                file_proposed = generar_nombre_archivo(nombre_full, tdoc, ndoc_real, formato_idx)
                self._log_info(f"Descargando carnet de {nombre_full}...", "INFO")

                carnet = session.post(API_CARNET_URL, json=payload_carnet, timeout=20, verify=False)
                if carnet.status_code == 200 and carnet.headers.get("Content-Type", "").startswith("application/pdf"):
                    try:
                        path = os.path.join(carpeta, file_proposed)
                        with open(path,"wb") as f:
                            f.write(carnet.content)
                        self._log_info(f"✅ PDF guardado: {file_proposed}","SUCCESS")
                        success += 1
                    except Exception as fileerr:
                        motivo_fallo = f"Error al guardar PDF: {file_proposed} - {fileerr}"
                        self._log_info(f"❌ {motivo_fallo}","ERROR")
                        docs_no_encontrados.append(f"{file_proposed}: {motivo_fallo}")
                        failed += 1
                else:
                    motivo_fallo = f"Error en descarga carnet ({nombre_full})"
                    self._log_info(f"❌ {motivo_fallo}: {ndoc_real}", "ERROR")
                    docs_no_encontrados.append(f"{file_proposed}: {motivo_fallo}")
                    failed += 1
            except Exception as ex:
                motivo_fallo = f"Error inesperado al descargar: {ex}"
                self._log_info(f"❌ {motivo_fallo} para {ndoc}", "ERROR")
                docs_no_encontrados.append(f"{ndoc}: {motivo_fallo}")
                failed += 1

        self._log_info(f"FIN | Descargados correctamente: {success} | Fallidos: {len(docs_no_encontrados)}","SUCCESS")
        self.bt.configure(state="normal", fg_color="#14b97d")

        if docs_no_encontrados:
            self._show_report_panel(docs_no_encontrados)
            messagebox.showwarning("Pendientes manuales", f"{len(docs_no_encontrados)} documento(s) NO descargados. Revisa el panel de resultados o repite manualmente.")
        else:
            self._hide_report_panel()
            messagebox.showinfo("Completado", f"Listo!\nDescargados correctamente: {success}\nSin pendientes.")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("PAIWeb Carnets Manager - Descarga Masiva de Carnets")
    root.geometry("1080x570")
    root.minsize(900,420)
    root.resizable(True, True)
    PAIWebCarnetsManager(root)
    root.mainloop()