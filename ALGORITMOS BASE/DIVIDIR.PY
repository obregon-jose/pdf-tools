#!/usr/bin/env python3
"""
pdf_splitter.py

Aplicación GUI para dividir un archivo PDF en páginas o extraer rangos de páginas.
Usa customtkinter para la interfaz y pypdf para manipular PDFs.

Requisitos:
    pip install customtkinter pypdf

Buenas prácticas aplicadas:
- Separación en funciones, tipado y docstrings.
- Manejo de errores con mensajes al usuario.
- Threading para no bloquear la interfaz.
- Validación de entrada (rangos).
- Uso de pathlib para rutas.
- Mensajes de estado y barra de progreso.
"""

from __future__ import annotations

import logging
import re
import threading
from pathlib import Path
from typing import List, Optional, Tuple

import customtkinter as ctk
from pypdf import PdfReader, PdfWriter
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory

# --- Configuración básica ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


# --- Utilidades ---
def parse_page_ranges(ranges: str, max_page: int) -> Optional[List[int]]:
    """
    Parse a page range string like "1-3,5,7-9" into a sorted list of 0-based page indices.
    Returns None if parsing fails or indices out of bounds.
    """
    if not ranges:
        return list(range(max_page))

    page_nums = set()
    token_re = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$")
    for part in ranges.split(","):
        part = part.strip()
        if not part:
            continue
        m = token_re.match(part)
        if not m:
            return None
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        if start < 1 or end < start:
            return None
        # convert to 0-based indices
        for p in range(start - 1, end):
            if p < 0 or p >= max_page:
                return None
            page_nums.add(p)
    return sorted(page_nums)


def safe_write_pdf(writer: PdfWriter, out_path: Path) -> None:
    """
    Escribe el PdfWriter a disco de forma segura.
    """
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        writer.write(f)
    tmp.replace(out_path)


# --- Lógica de división ---
def split_pdf(
    input_path: Path,
    output_dir: Path,
    ranges_text: str,
    progress_callback=None,
    status_callback=None,
) -> Tuple[int, int]:
    """
    Divide el PDF. Si ranges_text está vacío, se separa cada página en un archivo separado.
    Si se especifica un rango, extrae solo esas páginas en archivos separados (por página).
    Returns: (success_count, fail_count)
    """
    logging.info("Abriendo PDF: %s", input_path)
    try:
        reader = PdfReader(str(input_path))
    except Exception as e:
        logging.exception("No se pudo abrir el PDF")
        raise RuntimeError(f"No se pudo abrir el PDF: {e}")

    num_pages = len(reader.pages)
    logging.info("Páginas encontradas: %d", num_pages)

    page_indices = parse_page_ranges(ranges_text, num_pages)
    if page_indices is None:
        raise ValueError("Rangos inválidos o fuera de límites.")

    total = len(page_indices)
    success = 0
    fail = 0

    for i, page_idx in enumerate(page_indices, start=1):
        try:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_idx])
            out_name = f"{input_path.stem}_page_{page_idx + 1}.pdf"
            out_path = output_dir / out_name
            safe_write_pdf(writer, out_path)
            success += 1
            logging.info("Escrito: %s", out_path)
        except Exception as e:
            logging.exception("Error escribiendo página %d", page_idx + 1)
            fail += 1
        finally:
            if progress_callback:
                progress_callback(i / total)
            if status_callback:
                status_callback(f"Procesadas {i}/{total}")

    return success, fail


# --- GUI ---
class PDFSplitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Splitter")
        self.geometry("640x320")
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Variables
        self.input_path_var = ctk.StringVar(value="")
        self.output_dir_var = ctk.StringVar(value="")
        self.ranges_var = ctk.StringVar(value="")  # e.g., "1-3,5,7-9"

        # Widgets
        self.create_widgets()

    def create_widgets(self):
        pad = 12
        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.pack(padx=pad, pady=pad, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Selecciona PDF a dividir:", anchor="w").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        input_entry = ctk.CTkEntry(frame, textvariable=self.input_path_var, width=420)
        input_entry.grid(row=1, column=0, padx=8, sticky="w")
        ctk.CTkButton(frame, text="Examinar...", command=self.browse_input).grid(row=1, column=1, padx=8)

        ctk.CTkLabel(frame, text="Directorio de salida:", anchor="w").grid(row=2, column=0, sticky="w", padx=8, pady=(10, 0))
        output_entry = ctk.CTkEntry(frame, textvariable=self.output_dir_var, width=420)
        output_entry.grid(row=3, column=0, padx=8, sticky="w")
        ctk.CTkButton(frame, text="Seleccionar...", command=self.browse_output).grid(row=3, column=1, padx=8)

        ctk.CTkLabel(frame, text="Rangos (ej. 1-3,5) — dejar vacío para todas las páginas:", anchor="w").grid(row=4, column=0, sticky="w", padx=8, pady=(10, 0))
        ranges_entry = ctk.CTkEntry(frame, textvariable=self.ranges_var, width=420)
        ranges_entry.grid(row=5, column=0, padx=8, sticky="w")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(12, 0), sticky="we")
        self.start_btn = ctk.CTkButton(btn_frame, text="Iniciar división", command=self.on_start)
        self.start_btn.pack(side="left", padx=(8, 6))
        ctk.CTkButton(btn_frame, text="Salir", command=self.quit).pack(side="right", padx=(6, 8))

        # Progress & status
        self.progress = ctk.CTkProgressBar(frame, width=520)
        self.progress.set(0.0)
        self.progress.grid(row=7, column=0, columnspan=2, padx=8, pady=(16, 4))
        self.status_label = ctk.CTkLabel(frame, text="Listo", anchor="w")
        self.status_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 8))

    def browse_input(self):
        path = askopenfilename(filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if path:
            self.input_path_var.set(path)
            # prefill output dir next to file
            p = Path(path)
            self.output_dir_var.set(str(p.parent))

    def browse_output(self):
        d = askdirectory()
        if d:
            self.output_dir_var.set(d)

    def on_start(self):
        input_path = Path(self.input_path_var.get().strip())
        output_dir = Path(self.output_dir_var.get().strip())
        ranges_text = self.ranges_var.get().strip()

        if not input_path.exists() or not input_path.is_file():
            messagebox.showerror("Error", "Selecciona un archivo PDF válido.")
            return
        if not output_dir.exists() or not output_dir.is_dir():
            messagebox.showerror("Error", "Selecciona un directorio de salida válido.")
            return

        # Disable start button while running
        self.start_btn.configure(state="disabled")
        self.progress.set(0.0)
        self.status_label.configure(text="Iniciando...")

        # Run splitting in background thread
        thread = threading.Thread(
            target=self._run_split_thread,
            args=(input_path, output_dir, ranges_text),
            daemon=True,
        )
        thread.start()

    def _run_split_thread(self, input_path: Path, output_dir: Path, ranges_text: str):
        try:
            success, fail = split_pdf(
                input_path,
                output_dir,
                ranges_text,
                progress_callback=self._set_progress,
                status_callback=self._set_status,
            )
        except Exception as e:
            logging.exception("Fallo en la operación")
            self._set_status(f"Error: {e}")
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        else:
            self._set_progress(1.0)
            msg = f"Operación completada. Éxitos: {success}, Fallos: {fail}"
            self._set_status(msg)
            messagebox.showinfo("Completado", msg)
        finally:
            # Re-enable start button en hilo de la UI
            self.after(0, lambda: self.start_btn.configure(state="normal"))

    # Callbacks para actualizar UI (asegurando ejecución en hilo principal)
    def _set_progress(self, value: float):
        self.after(0, lambda: self.progress.set(value))

    def _set_status(self, text: str):
        self.after(0, lambda: self.status_label.configure(text=text))


def main():
    app = PDFSplitterApp()
    app.mainloop()


if __name__ == "__main__":
    main()