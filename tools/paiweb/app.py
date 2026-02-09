"""Aplicación principal de PAIWeb Carnets Manager"""
import os
import re
import time
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread

from config import DOWNLOADS_FOLDER, FILENAME_OPTIONS, ESQUEMAS_VACUNACION
from api_client import PAIWebAPIClient
from utils import nombre_completo, generar_nombre_archivo, resolver_ruta
from components import PatientVaccinePanel


class PAIWebCarnetsManager(ctk.CTkFrame):
    """Aplicación principal"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.area_font_default = 13
        self.pack(fill="both", expand=True)
        self._build_ui()
        self.patient_panels = []
        self.api_client = None
        self.token = ""

    def _build_ui(self):
        """Construye la interfaz de usuario"""
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky='nsew')

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=9)
        self.main_container.grid_rowconfigure(1, weight=1)

        self._build_top_panel()
        self._build_left_panel()
        self._build_right_panel()
        self._build_bottom_panel()

    def _build_top_panel(self):
        """Panel superior: Token y carpeta"""
        panel_top = ctk.CTkFrame(self.main_container)
        panel_top.grid(row=0, column=0, columnspan=2, sticky='ew', padx=6, pady=(8,3))
        panel_top.grid_columnconfigure(1, weight=1)

        lbl_token = ctk.CTkLabel(panel_top, text="🔑 Access Token:", width=120, anchor="w", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_token.grid(row=0, column=0, padx=(6,3), pady=3, sticky="w")
        self.tk_token = ctk.CTkEntry(panel_top, font=ctk.CTkFont(size=13))
        self.tk_token.grid(row=0, column=1, padx=4, pady=3, sticky="ew")
        btn_pegar_token = ctk.CTkButton(panel_top, text="Pegar token", command=self._paste_token, width=110, fg_color="#476cb2")
        btn_pegar_token.grid(row=0, column=2, padx=(6,2), pady=3, sticky="w")

        lbl_dest = ctk.CTkLabel(panel_top, text="📁 Carpeta destino:", width=120, anchor="w")
        lbl_dest.grid(row=1, column=0, padx=(6,3), pady=3, sticky="w")
        self.destino = ctk.CTkEntry(panel_top, font=ctk.CTkFont(size=12))
        self.destino.grid(row=1, column=1, padx=4, pady=3, sticky="ew")
        self.destino.insert(0, DOWNLOADS_FOLDER)
        btn_folder = ctk.CTkButton(panel_top, text="Seleccionar carpeta", command=self._choose_folder, width=120)
        btn_folder.grid(row=1, column=2, padx=(6,2), pady=3, sticky="w")

        lbl_formato = ctk.CTkLabel(panel_top, text="📝 Convención de nombre:", width=120, anchor="w")
        lbl_formato.grid(row=2, column=0, padx=(6,3), pady=3, sticky="w")
        self.formato_selector = ctk.CTkComboBox(panel_top, values=FILENAME_OPTIONS, state="readonly", font=ctk.CTkFont(size=12), width=280)
        self.formato_selector.grid(row=2, column=1, padx=4, pady=3, sticky="w")
        self.formato_selector.set(FILENAME_OPTIONS[0])

    def _build_left_panel(self):
        """Panel izquierdo: Entrada de documentos (10%)"""
        left_container = ctk.CTkFrame(self.main_container)
        left_container.grid(row=1, column=0, sticky="nsew", padx=(6,3), pady=5)
        left_container.grid_rowconfigure(1, weight=1)
        left_container.grid_columnconfigure(0, weight=1)

        lbl_docs = ctk.CTkLabel(left_container, text="📑 Documentos", font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        lbl_docs.grid(row=0, column=0, sticky="ew", padx=8, pady=(5,2))

        # Área de texto para documentos
        self.area = ctk.CTkTextbox(left_container, font=("Consolas", self.area_font_default), border_width=2)
        self.area.grid(row=1, column=0, sticky="nsew", padx=8, pady=5)

        # Botones de control
        btns_frame = ctk.CTkFrame(left_container, fg_color="transparent")
        btns_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=5)
        btns_frame.grid_columnconfigure(0, weight=1)
        btns_frame.grid_columnconfigure(1, weight=1)

        btn_paste = ctk.CTkButton(btns_frame, text="📋 Pegar", command=self._paste_clipboard, fg_color="#1f6feb")
        btn_paste.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        btn_clear = ctk.CTkButton(btns_frame, text="🧹 Limpiar", command=self._clear_all, fg_color="#e74c3c")
        btn_clear.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        self.btn_search = ctk.CTkButton(
            btns_frame, text="🔍 Buscar Vacunas",
            command=self._search_vaccines,
            fg_color="#14b97d", font=ctk.CTkFont(size=13, weight="bold"), height=40
        )
        self.btn_search.grid(row=1, column=0, columnspan=2, padx=2, pady=5, sticky="ew")

    def _build_right_panel(self):
        """Panel derecho: Resultados (90%)"""
        right_container = ctk.CTkFrame(self.main_container)
        right_container.grid(row=1, column=1, sticky="nsew", padx=(3,6), pady=5)
        right_container.grid_rowconfigure(1, weight=1)
        right_container.grid_columnconfigure(0, weight=1)

        # Header de resultados con filtros
        results_header = ctk.CTkFrame(right_container)
        results_header.grid(row=0, column=0, sticky="ew", padx=6, pady=(5,0))
        results_header.grid_columnconfigure(0, weight=1)

        self.lbl_results = ctk.CTkLabel(
            results_header, text="📋 Resultados (0 pacientes)",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        )
        self.lbl_results.grid(row=0, column=0, sticky="w", padx=8, pady=5)

        # Filtros en segunda fila
        filter_frame = ctk.CTkFrame(results_header, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0,5))

        ctk.CTkLabel(filter_frame, text="Esquema:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0,5))
        
        esquemas_list = ["Todos"] + list(ESQUEMAS_VACUNACION.keys())
        self.filter_esquema_var = tk.StringVar(value="Todos")
        self.filter_esquema_combo = ctk.CTkComboBox(
            filter_frame, variable=self.filter_esquema_var,
            values=esquemas_list, width=160, state="readonly",
            command=self._apply_filter, font=ctk.CTkFont(size=11)
        )
        self.filter_esquema_combo.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Vacuna:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(10,5))
        
        self.filter_var = tk.StringVar(value="Todas")
        self.filter_combo = ctk.CTkComboBox(
            filter_frame, variable=self.filter_var,
            values=["Todas"], width=180, state="readonly",
            command=self._apply_filter, font=ctk.CTkFont(size=11)
        )
        self.filter_combo.pack(side="left", padx=5)

        btn_select_all = ctk.CTkButton(
            filter_frame, text="✓ Todos", width=70,
            command=self._select_all, fg_color="#1f6feb", font=ctk.CTkFont(size=11)
        )
        btn_select_all.pack(side="left", padx=(10,2))

        btn_deselect_all = ctk.CTkButton(
            filter_frame, text="✗ Ninguno", width=70,
            command=self._deselect_all, fg_color="#6c757d", font=ctk.CTkFont(size=11)
        )
        btn_deselect_all.pack(side="left", padx=2)

        # Contenedor scrollable de resultados
        self.results_container = ctk.CTkScrollableFrame(
            right_container, fg_color="#0a0a0a",
            corner_radius=8, border_width=2, border_color="#2a2a2a"
        )
        self.results_container.grid(row=1, column=0, sticky="nsew", padx=6, pady=5)
        self.results_container.grid_columnconfigure(0, weight=1)

    def _build_bottom_panel(self):
        """Panel inferior: Botón de descarga y log"""
        bottom_container = ctk.CTkFrame(self.main_container)
        bottom_container.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(5,8))
        bottom_container.grid_columnconfigure(0, weight=1)

        # Botón de descarga
        self.btn_download = ctk.CTkButton(
            bottom_container, text="📥 Descargar Carnets Seleccionados",
            command=self._start_download, fg_color="#14b97d",
            font=ctk.CTkFont(size=15, weight="bold"), height=40
        )
        self.btn_download.grid(row=0, column=0, sticky="ew", padx=8, pady=(0,5))

        # Panel de log
        self.logbox = ctk.CTkTextbox(
            bottom_container, font=("Consolas", 10),
            corner_radius=8, border_width=2, height=80
        )
        self.logbox.grid(row=1, column=0, sticky="ew", padx=8, pady=(0,5))
        self.logbox.configure(state="disabled")
        self._log_info("Listo para comenzar. Ingresa documentos y busca vacunas.", "INFO")

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
            self._log_info(f"Se agregaron {added} documentos desde portapapeles.", "SUCCESS")
        except Exception:
            messagebox.showerror("Portapapeles", "No se pudo obtener el texto del portapapeles.")

    def _clear_all(self):
        self.area.delete("1.0", tk.END)
        self._clear_results()
        self._log_info("Panel limpiado completamente.", "INFO")

    def _clear_results(self):
        for widget in self.results_container.winfo_children():
            widget.destroy()
        self.patient_panels.clear()
        self.lbl_results.configure(text="📋 Resultados (0 pacientes)")
        self.filter_combo.configure(values=["Todas"])
        self.filter_var.set("Todas")

    def _get_documents(self):
        return [re.sub(r"\D", "", l.strip()) for l in self.area.get("1.0", "end").splitlines() 
                if l.strip() and len(re.sub(r"\D", "", l.strip())) > 3]

    def _get_filename_format_index(self):
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

    def _search_vaccines(self):
        Thread(target=self._search_vaccines_thread, daemon=True).start()

    def _search_vaccines_thread(self):
        """Busca las vacunas de todos los pacientes"""
        self.btn_search.configure(state="disabled", fg_color="#888")
        self.btn_download.configure(state="disabled", fg_color="#888")
        self.update()
        
        self.token = self.tk_token.get().strip()
        if not self.token:
            self._log_info("Ingresa tu access_token.", "ERROR")
            messagebox.showerror("Error de acceso", "Debes ingresar un access_token válido.")
            self.btn_search.configure(state="normal", fg_color="#14b97d")
            return

        self._log_info("Validando token...", "INFO")
        self.api_client = PAIWebAPIClient(self.token)
        
        if not self.api_client.validar_token():
            self._log_info("El access_token es inválido o expiró.", "ERROR")
            messagebox.showerror("Token inválido", "El access_token es inválido o expiró. Ingresa uno nuevo.")
            self.btn_search.configure(state="normal", fg_color="#14b97d")
            return

        documentos = self._get_documents()
        if not documentos:
            self._log_info("No se ingresaron números de documento.", "ERROR")
            messagebox.showerror("Falta documentos", "No se detectaron números de documento válidos.")
            self.btn_search.configure(state="normal", fg_color="#14b97d")
            return

        self._clear_results()

        total = len(documentos)
        self._log_info(f"Iniciando búsqueda de {total} pacientes...", "INFO")
        
        all_vaccines = set()
        
        for idx, ndoc in enumerate(documentos, 1):
            try:
                time.sleep(0.3)
                
                self._log_info(f"[{idx}/{total}] Buscando paciente {ndoc}...", "INFO")
                
                paciente = self.api_client.buscar_paciente(ndoc)
                
                if not paciente:
                    self._log_info(f"Paciente {ndoc} no encontrado en el sistema.", "WARN")
                    self._add_not_found_panel(ndoc)
                    continue
                
                paciente_id = paciente.get("pacienteId")
                
                if not paciente_id:
                    self._log_info(f"No se encontró pacienteId para el documento {ndoc}.", "WARN")
                    self._add_not_found_panel(ndoc)
                    continue
                
                nombre = nombre_completo(paciente)
                self._log_info(f"✓ Paciente encontrado: {nombre} (ID: {paciente_id})", "SUCCESS")
                
                time.sleep(0.3)
                self._log_info(f"[{idx}/{total}] Consultando vacunas del paciente ID {paciente_id}...", "INFO")
                
                vaccines = self.api_client.obtener_vacunas(paciente_id)
                
                for v in vaccines:
                    all_vaccines.add(v.get("biologico", "N/A"))
                
                self._log_info(f"✓ {len(vaccines)} vacunas encontradas.", "SUCCESS")
                self._add_patient_panel(paciente, vaccines)
                
            except Exception as ex:
                self._log_info(f"Error al procesar documento {ndoc}: {ex}", "ERROR")
                self._add_not_found_panel(ndoc)

        vaccine_list = ["Todas"] + sorted(list(all_vaccines))
        self.filter_combo.configure(values=vaccine_list)
        
        found_count = sum(1 for p in self.patient_panels if not p.is_not_found)
        not_found_count = sum(1 for p in self.patient_panels if p.is_not_found)
        self.lbl_results.configure(text=f"📋 Resultados ({found_count} encontrados, {not_found_count} no encontrados)")
        
        self._log_info(f"Búsqueda completada. {found_count} pacientes encontrados, {not_found_count} no encontrados.", "SUCCESS")
        self.btn_search.configure(state="normal", fg_color="#14b97d")
        self.btn_download.configure(state="normal", fg_color="#14b97d")

    def _add_patient_panel(self, patient_data, vaccines_data):
        panel = PatientVaccinePanel(
            self.results_container,
            patient_data, vaccines_data,
            download_callback=self._download_single_carnet,
            is_not_found=False
        )
        panel.grid(row=len(self.patient_panels), column=0, sticky="ew", padx=5, pady=5)
        self.patient_panels.append(panel)
    
    def _add_not_found_panel(self, documento):
        patient_data = {"numeroIdentificacion": documento}
        panel = PatientVaccinePanel(
            self.results_container,
            patient_data, [],
            download_callback=None,
            is_not_found=True
        )
        panel.grid(row=len(self.patient_panels), column=0, sticky="ew", padx=5, pady=5)
        self.patient_panels.append(panel)

    def _apply_filter(self, choice=None):
        filter_value = self.filter_var.get()
        filter_esquema = self.filter_esquema_var.get()
        
        visible_count = 0
        for panel in self.patient_panels:
            if panel.is_not_found:
                panel.grid()
                continue
            
            show_panel = True
            
            if filter_esquema != "Todos":
                if filter_esquema in panel.analisis_esquemas:
                    if not panel.analisis_esquemas[filter_esquema]["completo"]:
                        show_panel = False
                else:
                    show_panel = False
            
            if show_panel and filter_value != "Todas":
                has_vaccine = any(
                    v.get("biologico") == filter_value 
                    for v in panel.vaccines_data
                )
                if not has_vaccine:
                    show_panel = False
            
            if show_panel:
                panel.grid()
                visible_count += 1
            else:
                panel.grid_remove()
        
        not_found_count = sum(1 for p in self.patient_panels if p.is_not_found)
        self.lbl_results.configure(text=f"📋 Resultados ({visible_count} encontrados, {not_found_count} no encontrados)")

    def _select_all(self):
        for panel in self.patient_panels:
            if panel.winfo_viewable() and not panel.is_not_found:
                panel.selected_var.set(True)
        self._log_info("Todos los pacientes visibles seleccionados.", "INFO")

    def _deselect_all(self):
        for panel in self.patient_panels:
            if not panel.is_not_found:
                panel.selected_var.set(False)
        self._log_info("Todos los pacientes deseleccionados.", "INFO")

    def _download_single_carnet(self, patient_data):
        Thread(target=self._download_single_thread, args=(patient_data,), daemon=True).start()

    def _download_single_thread(self, patient_data):
        carpeta = resolver_ruta(self.destino.get(), DOWNLOADS_FOLDER)
        formato_idx = self._get_filename_format_index()
        
        tdoc = patient_data.get("tipoIdentificacionCodigo", "")
        ndoc = patient_data.get("numeroIdentificacion", "")
        fnac = patient_data.get("fechaNacimiento", "")[:10] if patient_data.get("fechaNacimiento") else ""
        nombre_full = nombre_completo(patient_data)
        
        self._log_info(f"Descargando carnet individual de {nombre_full}...", "INFO")
        
        try:
            file_name = generar_nombre_archivo(nombre_full, tdoc, ndoc, formato_idx)
            pdf_content = self.api_client.descargar_carnet(fnac, tdoc, ndoc, nombre_full)
            
            if pdf_content:
                path = os.path.join(carpeta, file_name)
                with open(path, "wb") as f:
                    f.write(pdf_content)
                self._log_info(f"✅ Carnet individual descargado: {file_name}", "SUCCESS")
                messagebox.showinfo("Descarga exitosa", f"Carnet descargado correctamente:\n{file_name}")
            else:
                self._log_info(f"❌ Error al descargar carnet de {nombre_full}", "ERROR")
                messagebox.showerror("Error de descarga", f"No se pudo descargar el carnet de {nombre_full}")
                
        except Exception as ex:
            self._log_info(f"❌ Error inesperado: {ex}", "ERROR")
            messagebox.showerror("Error", f"Error al descargar carnet: {ex}")

    def _start_download(self):
        Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        self.btn_download.configure(state="disabled", fg_color="#888")
        self.update()

        selected_patients = [p for p in self.patient_panels if p.is_selected() and p.winfo_viewable() and not p.is_not_found]
        
        if not selected_patients:
            self._log_info("No hay pacientes seleccionados para descargar.", "WARN")
            messagebox.showwarning("Sin selección", "Debes seleccionar al menos un paciente para descargar.")
            self.btn_download.configure(state="normal", fg_color="#14b97d")
            return

        carpeta = resolver_ruta(self.destino.get(), DOWNLOADS_FOLDER)
        formato_idx = self._get_filename_format_index()

        total = len(selected_patients)
        success, failed = 0, 0
        failed_list = []

        self._log_info(f"Iniciando descarga de {total} carnets...", "INFO")

        for idx, panel in enumerate(selected_patients, 1):
            try:
                time.sleep(0.3)
                
                patient = panel.get_patient_data()
                tdoc = patient.get("tipoIdentificacionCodigo", "")
                ndoc = patient.get("numeroIdentificacion", "")
                fnac = patient.get("fechaNacimiento", "")[:10] if patient.get("fechaNacimiento") else ""
                nombre_full = nombre_completo(patient)
                
                self._log_info(f"[{idx}/{total}] Descargando carnet de {nombre_full}...", "INFO")
                
                file_name = generar_nombre_archivo(nombre_full, tdoc, ndoc, formato_idx)
                pdf_content = self.api_client.descargar_carnet(fnac, tdoc, ndoc, nombre_full)
                
                if pdf_content:
                    path = os.path.join(carpeta, file_name)
                    with open(path, "wb") as f:
                        f.write(pdf_content)
                    self._log_info(f"✅ PDF guardado: {file_name}", "SUCCESS")
                    success += 1
                else:
                    self._log_info(f"❌ Error al descargar carnet de {nombre_full}", "ERROR")
                    failed_list.append(f"{nombre_full} ({ndoc})")
                    failed += 1
                    
            except Exception as ex:
                self._log_info(f"❌ Error inesperado: {ex}", "ERROR")
                failed_list.append(f"{nombre_full} ({ndoc}): {ex}")
                failed += 1

        self._log_info(f"FIN | Descargados: {success} | Fallidos: {failed}", "SUCCESS")
        self.btn_download.configure(state="normal", fg_color="#14b97d")

        if failed_list:
            messagebox.showwarning(
                "Descarga completada con errores",
                f"Descargados: {success}\nFallidos: {failed}\n\nRevisa el log para más detalles."
            )
        else:
            messagebox.showinfo(
                "Descarga completada",
                f"¡Listo!\n\nDescargados correctamente: {success}\nSin errores."
            )