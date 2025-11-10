import os
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

class PDFSplitterApp(ctk.CTkFrame):
    def __init__(self, master, go_home):
        super().__init__(master)

        # State
        self.pdf_path = ""
        self.page_count = 0
        # body entries (user-editable part)
        self.rename_entries = []
        # combined "Página N -> prefijo + contenido" labels (single label per row)
        self.combined_labels = []
        # Default: activar la opción de agregar nombres por página
        self.manual_rename_var = ctk.BooleanVar(value=True)
        self.last_split = None       # {'original': path, 'created_files': [...]}

        # Additional state for prefix & preview behavior
        self.prefix_var = tk.StringVar(value="OPF")
        self.base_names = []         # base names per page, e.g. "Página_1"
        self.user_edited = []        # optional flags per entry: True if user edited that entry

        # Track previous prefix so we can update labels consistently
        self.last_prefix = self.prefix_var.get().strip()

        # Top frame (single container) with compact spacing
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=6, pady=6)

        # Row 0: PDF path entry + Select button + Select output folder + Output entry
        lbl_pdf = ctk.CTkLabel(top_frame, text="PDF:", width=40, anchor="w")
        lbl_pdf.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")

        self.pdf_entry = ctk.CTkEntry(top_frame, placeholder_text="Escribe la ruta del PDF o usa Seleccionar", width=500)
        self.pdf_entry.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")

        btn_select_pdf = ctk.CTkButton(top_frame, text="Seleccionar PDF", width=140, command=self.on_select_pdf)
        btn_select_pdf.grid(row=0, column=2, padx=(0, 6), pady=4, )

        lbl_out = ctk.CTkLabel(top_frame, text="Salida:", width=60, anchor="w")
        lbl_out.grid(row=1, column=0, padx=(6, 4), pady=4, sticky="w")

        self.out_entry = ctk.CTkEntry(top_frame, placeholder_text="Carpeta de salida (opcional)", width=420)
        self.out_entry.grid(row=1, column=1, padx=(0, 6), pady=4, sticky="we")

        btn_out = ctk.CTkButton(top_frame, text="Seleccionar Carpeta", width=140, command=self.on_select_output_folder)
        btn_out.grid(row=1, column=2, padx=(0, 6), pady=4)

        # Row 2: prefix + manual rename checkbox (compact)
        lbl_prefix = ctk.CTkLabel(top_frame, text="Prefijo:", anchor="w", width=60)
        lbl_prefix.grid(row=2, column=0, padx=(6, 4), pady=4, sticky="w")

        # Use textvariable so we can trace changes and refresh preview automatically
        self.prefix_entry = ctk.CTkEntry(top_frame, width=220, textvariable=self.prefix_var)
        self.prefix_entry.grid(row=2, column=1, padx=(0, 6), pady=4, sticky="w")

        # Trace prefix changes to refresh preview automatically
        try:
            self.prefix_var.trace_add("write", lambda *args: self.on_prefix_change())
        except Exception:
            self.prefix_var.trace("w", lambda *args: self.on_prefix_change())

        self.manual_cb = ctk.CTkCheckBox(
            top_frame,
            text="Agregar Nombres a cada página",
            variable=self.manual_rename_var,
            command=self.on_toggle_manual_rename
        )
        self.manual_cb.grid(row=2, column=2, padx=(0, 6), pady=4, sticky="w")

        # Row 3: small spacer (keep compact)
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=3, column=0, columnspan=3)

        # Row 4: action buttons (Dividir, Deshacer, Limpiar nombres)
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="we", padx=6, pady=(0,4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)

        self.split_button = ctk.CTkButton(btn_frame, text="Dividir PDF", command=self.on_split_pdf, fg_color="#1f6feb")
        self.split_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")

        self.undo_button = ctk.CTkButton(btn_frame, text="Deshacer", command=self.on_undo,
                                         fg_color="#f0ad4e", text_color="black")
        self.undo_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        self.undo_button.configure(state="disabled")

        self.clear_names_button = ctk.CTkButton(btn_frame, text="Limpiar nombres", command=self.on_clear_names)
        self.clear_names_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")

        top_frame.grid_columnconfigure(1, weight=1)

        # Preview panel (no title), compact margins
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # NOTE: move the informative note into the preview panel (per request).
        # This note should appear when NOT renaming (manual_rename_var == False).
        self.rename_note = ctk.CTkLabel(
            self.preview_frame,
            text="Nota: Si no agregas nombres a cada pagina, los archivos se nombraran como Página 1, Página 2, Pagina 3...N",
            text_color="gray",
            font=("Arial", 12, "bold")
        )
        # Show only if manual rename is OFF
        if not self.manual_rename_var.get():
            self.rename_note.grid(row=0, column=0, sticky="w", padx=4, pady=(2,4))

        # Scrollable frame for pages (single-column now)
        self.scrollable_pages = ctk.CTkScrollableFrame(self.preview_frame, height=360)
        # place scrollable below the note (row 1)
        self.scrollable_pages.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        # ensure single column stretch
        try:
            self.scrollable_pages.grid_columnconfigure(0, weight=1)
        except Exception:
            pass

        self.pages_list_labels = []

    # --- UI Handlers ---
    def on_select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if not path:
            return
        self.pdf_path = path
        self.pdf_entry.delete(0, tk.END)
        self.pdf_entry.insert(0, path)
        self._load_pdf_preview(path)

    def _load_pdf_preview(self, path):
        try:
            doc = fitz.open(path)
            self.page_count = doc.page_count
            doc.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
            print(f"[ERROR] Abrir PDF: {e}")
            self.page_count = 0
            return

        # Clear previous preview widgets and state
        for child in self.scrollable_pages.winfo_children():
            child.destroy()
        self.combined_labels = []
        self.rename_entries = []
        self.base_names = []
        self.user_edited = []
        # reset last_prefix to current prefix so future replacements are consistent
        self.last_prefix = self.prefix_var.get().strip()

        prefix = self.prefix_var.get().strip()
        prefix_text = f"{prefix}_" if prefix else ""

        # Build single-column layout for pages: each item is a frame with combined label + entry
        for i in range(self.page_count):
            base_name = f"Página_{i+1}"
            self.base_names.append(base_name)
            self.user_edited.append(False)

            row = i
            col = 0

            # container for each page item with minimal spacing (reduced padding)
            page_item = ctk.CTkFrame(self.scrollable_pages)
            page_item.grid(row=row, column=col, padx=2, pady=2, sticky="we")
            # columns: 0=combined label, 1=entry
            page_item.grid_columnconfigure(1, weight=1)

            # combined label: "Página N    PREFIJO_"
            combined_text = f"Página {i+1} → {prefix_text}"
            combined_lbl = ctk.CTkLabel(page_item, text=combined_text, anchor="w")
            combined_lbl.grid(row=0, column=0, padx=(2, 6), pady=2, sticky="w")

            # body entry: editable part only (placeholder visible if empty)
            entry = ctk.CTkEntry(page_item, placeholder_text=f"# Documento de {base_name}")
            entry.grid(row=0, column=1, padx=(0, 6), pady=2, sticky="we")

            # bind events to update combined label live and mark edits
            entry.bind("<KeyRelease>", lambda e, idx=i: self._on_entry_key(idx))
            entry.bind("<FocusOut>", lambda e, idx=i: self._on_entry_key(idx))

            # store widgets
            self.combined_labels.append(combined_lbl)
            self.rename_entries.append(entry)

            # if manual rename is disabled, hide combined label and body entry
            if not self.manual_rename_var.get():
                combined_lbl.grid_remove()
                entry.grid_remove()

        self.split_button.configure(state="normal" if self.page_count > 0 else "disabled")

    def _on_entry_key(self, idx):
        """
        Update combined label for row idx to show: "Página N → PREFIJO_body"
        If the body is empty, the combined label will show prefix only.
        """
        if idx < 0 or idx >= len(self.rename_entries):
            return
        entry = self.rename_entries[idx]
        body = entry.get().strip()
        prefix = self.prefix_var.get().strip()
        prefix_text = f"{prefix}_" if prefix else ""
        combined = f"Página {idx+1} → {prefix_text}{body}" if body else f"Página {idx+1}  →  {prefix_text}"
        try:
            self.combined_labels[idx].configure(text=combined)
        except Exception:
            pass
        # mark edited
        if 0 <= idx < len(self.user_edited):
            self.user_edited[idx] = True

    def on_prefix_change(self):
        """
        When the prefix changes, update the combined label text for every page.
        Also refresh each combined label with the current content of the corresponding entry.
        """
        new_prefix = self.prefix_var.get().strip()
        prefix_text = f"{new_prefix}_" if new_prefix else ""
        for idx, comb_lbl in enumerate(self.combined_labels):
            try:
                body = ""
                if idx < len(self.rename_entries):
                    try:
                        body = self.rename_entries[idx].get().strip()
                    except Exception:
                        body = ""
                combined = f"Página {idx+1} → {prefix_text}{body}" if body else f"Página {idx+1} → {prefix_text}"
                comb_lbl.configure(text=combined)
            except Exception:
                pass
        # update last_prefix
        self.last_prefix = new_prefix

    def on_toggle_manual_rename(self):
        enabled = self.manual_rename_var.get()
        for idx, (comb_lbl, entry) in enumerate(zip(self.combined_labels, self.rename_entries)):
            if enabled:
                comb_lbl.grid()
                entry.grid()
            else:
                comb_lbl.grid_remove()
                entry.grid_remove()
        # show/hide the rename note in preview panel: note appears when NOT renaming
        if enabled:
            try:
                self.rename_note.grid_remove()
            except Exception:
                pass
        else:
            try:
                self.rename_note.grid(row=0, column=0, sticky="w", padx=4, pady=(2,4))
            except Exception:
                pass

    def on_clear_names(self):
        """
        Limpia el contenido de los campos dejando únicamente el prefijo visible en the combined label.
        """
        for idx, entry in enumerate(self.rename_entries):
            try:
                entry.delete(0, tk.END)
            except Exception:
                pass
            if idx < len(self.user_edited):
                self.user_edited[idx] = False
            # refresh combined label to show prefix only
            try:
                prefix = self.prefix_var.get().strip()
                prefix_text = f"{prefix}_" if prefix else ""
                self.combined_labels[idx].configure(text=f"Página {idx+1}  →  {prefix_text}")
            except Exception:
                pass
            if not self.manual_rename_var.get():
                entry.grid_remove()
        messagebox.showinfo("Limpiar nombres", "Se han eliminado los nombres editables dejando el prefijo visible en la vista.")

    def on_select_output_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta de salida")
        if not folder:
            return
        self.out_entry.delete(0, tk.END)
        self.out_entry.insert(0, folder)

    def _ensure_unique_filename(self, path, existing_paths=None):
        existing_paths = set(existing_paths or [])
        base, ext = os.path.splitext(path)
        candidate = path
        counter = 1
        while os.path.exists(candidate) or candidate in existing_paths:
            candidate = f"{base} ({counter}){ext}"
            counter += 1
        return candidate

    # --- Split / Undo logic ---
    def on_split_pdf(self):
        pdf_path = self.pdf_entry.get().strip() or self.pdf_path
        if not pdf_path:
            messagebox.showerror("Error", "No se ha seleccionado ni indicado un archivo PDF.")
            return
        if not os.path.exists(pdf_path):
            messagebox.showerror("Error", "La ruta del PDF no existe.")
            return

        # If manual naming is enabled, validate that every editable field has a value (numero de documento)
        if self.manual_rename_var.get():
            empty_pages = []
            for idx, entry in enumerate(self.rename_entries):
                try:
                    val = entry.get().strip()
                except Exception:
                    val = ""
                if not val:
                    empty_pages.append(str(idx+1))
            if empty_pages:
                pages_list = ", ".join(empty_pages)
                messagebox.showerror("Campos vacíos", f"Todos los campos deben contener un número de documento.\nPáginas con campo vacío: {pages_list}")
                return

        output_dir = self.out_entry.get().strip()
        if not output_dir:
            output_dir = os.path.dirname(pdf_path) or os.getcwd()

        try:
            output_dir = os.path.abspath(os.path.expanduser(output_dir))
        except Exception:
            output_dir = output_dir

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la carpeta de salida '{output_dir}': {e}")
            print(f"[ERROR] Crear carpeta salida: {e}")
            return

        prefix = self.prefix_var.get().strip()
        manual = self.manual_rename_var.get()

        try:
            doc = fitz.open(pdf_path)
            num_pages = doc.page_count
            created_files = []
            for i in range(num_pages):
                if manual and i < len(self.rename_entries):
                    body = self.rename_entries[i].get().strip()
                    # if user accidentally pasted prefix into body, strip it
                    if body and "_" in body and body.split("_", 1)[0] == prefix:
                        body = body.split("_", 1)[1]
                    # compose final name with prefix if present
                    final_name = f"{prefix}_{body}" if prefix else body
                else:
                    final_name = self.base_names[i] if i < len(self.base_names) else f"Página_{i+1}"

                safe_name = "".join(ch for ch in final_name if ch not in r'\/:*?"<>|').strip()
                if not safe_name:
                    safe_name = f"Página_{i+1}"

                intended = os.path.join(output_dir, f"{safe_name}.pdf")
                out_filename = self._ensure_unique_filename(intended, existing_paths=created_files)

                new_pdf = fitz.open()
                new_pdf.insert_pdf(doc, from_page=i, to_page=i)
                new_pdf.save(out_filename)
                new_pdf.close()
                created_files.append(out_filename)
                print(f"[INFO] Página {i+1}/{num_pages} escrita en: {out_filename}")

            doc.close()

            removed_original = False
            try:
                os.remove(pdf_path)
                removed_original = True
                print(f"[INFO] Archivo original eliminado: {pdf_path}")
            except Exception as e_rm:
                print(f"[WARN] No se pudo eliminar el original: {e_rm}")

            self.last_split = {
                "original_path": pdf_path,
                "created_files": created_files,
                "original_removed": removed_original
            }
            self.undo_button.configure(state="normal")

            if removed_original:
                messagebox.showinfo("Éxito", f"Se han creado {len(created_files)} archivos PDF y el original ha sido eliminado.")
            else:
                messagebox.showinfo("Éxito", f"Se han creado {len(created_files)} archivos PDF. No se eliminó el original.")

        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error al procesar el PDF: {e}")
            print(f"[ERROR] Al dividir PDF: {e}")

    def on_undo(self):
        if not self.last_split:
            messagebox.showinfo("Info", "No hay acción para deshacer.")
            return

        orig = self.last_split.get("original_path")
        created = self.last_split.get("created_files", [])
        orig_removed = self.last_split.get("original_removed", False)

        if not created:
            messagebox.showinfo("Info", "No hay archivos para deshacer.")
            return

        if os.path.exists(orig):
            messagebox.showinfo("Info", "El archivo original ya existe. Operación de deshacer cancelada.")
            self.last_split = None
            self.undo_button.configure(state="disabled")
            return

        try:
            new_doc = fitz.open()
            for page_file in created:
                if not os.path.exists(page_file):
                    raise FileNotFoundError(f"Falta archivo por página: {page_file}")
                sub = fitz.open(page_file)
                new_doc.insert_pdf(sub)
                sub.close()
            new_doc.save(orig)
            new_doc.close()
            print(f"[INFO] Original reconstruido en: {orig}")

            removed_any = []
            for f in created:
                try:
                    os.remove(f)
                    removed_any.append(f)
                except Exception as e:
                    print(f"[WARN] No se pudo borrar {f}: {e}")

            message = f"Original reconstruido en: {orig}.\nSe eliminaron {len(removed_any)} archivos por página."
            messagebox.showinfo("Deshacer completado", message)

            self.last_split = None
            self.undo_button.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo deshacer la operación: {e}")
            print(f"[ERROR] Deshacer: {e}")