#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REVISAR_CARNETS.py

Versión del GUI que mantiene tu flujo original para un PDF individual y además
permite seleccionar una carpeta con archivos .zip; cada .zip se extrae temporalmente,
se buscan los PDFs dentro y se procesa cada PDF exactamente igual que con el botón
"Seleccionar PDF", añadiendo una fila por PDF al archivo Excel de salida.
"""
import re
import threading
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Excel
from openpyxl import Workbook, load_workbook

# Manejo ZIP / temporales
import zipfile
import tempfile
import shutil
import sys
import traceback

# Intentar importar librerías opcionales
try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from pdf2image import convert_from_path
    from PIL import Image
    import pytesseract
except Exception:
    convert_from_path = None
    pytesseract = None

# Configuración
MAX_VACCINES = 5  # máximo vacunas a colocar en columnas separadas

# Encabezados solicitados
PERSON_HEADERS = ["Nombres", "Apellidos", "Documento", "Fecha Nacimiento", "Edad"]
VACCINE_FIELDS = ["Edad", "Vacuna", "Dosis", "FechaAplicacion", "Laboratorio", "NumeroDeLote", "IPS", "Vacunador", "VacunaRaw"]

DATE_RE_GENERIC = re.compile(
    r'([0-3]?\d[\/\-\.\s](?:[a-zA-Záéíóúñ]+|[01]?\d)[\/\-\.\s]\d{2,4}|\d{4}[\/\-\.\s][01]?\d[\/\-\.\s][0-3]?\d|\d{1,2}\s+de\s+[a-záéíóúñ]+(?:\s+de\s+\d{4})?)',
    re.IGNORECASE
)
DOC_RE = re.compile(r'(\d{6,20})')  # documento largo
AGE_AT_VAX_RE = re.compile(r'^\s*\d+\s*(?:meses|mes|años|año|años)?', re.IGNORECASE)
DOSE_WORDS = re.compile(r'\b(primera|segunda|tercera|refuerzo|dosis|completa|única|unica|refuerzo)\b', re.IGNORECASE)

KNOWN_VACCINES = [
    "covid", "covid-19", "influvac", "influenza", "gripe", "hepatitis", "srp", "sarampion", "rub[eé]ola",
    "parotiditis", "tetanus", "tdap", "polio", "rotavirus", "neumococo", "hpv", "varicela", "abbott"
]

# ---------------- Text extraction ----------------
def extract_text_with_pdfplumber(pdf_path):
    if pdfplumber is None:
        return ""
    texts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    texts.append(txt)
    except Exception:
        return ""
    return "\n".join(texts)

def extract_text_with_ocr(pdf_path, dpi=300):
    if convert_from_path is None or pytesseract is None:
        return ""
    texts = []
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        for img in images:
            if img.mode != "RGB":
                img = img.convert("RGB")
            txt = pytesseract.image_to_string(img, lang="spa+eng")
            texts.append(txt)
    except Exception:
        return ""
    return "\n".join(texts)

# ---------------- Heurísticas de parsing ----------------
def normalize_spaces(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or "")).strip()

def find_vaccine_block(lines):
    idxs = [i for i, ln in enumerate(lines) if re.search(r'(?i)vacun', ln)]
    if idxs:
        res = []
        for idx in idxs:
            res.extend(lines[idx: idx + 25])
        seen = []
        out = []
        for r in res:
            rr = normalize_spaces(r)
            if rr and rr not in seen:
                seen.append(rr)
                out.append(rr)
        return out
    res = []
    for ln in lines:
        for v in KNOWN_VACCINES:
            if re.search(r'\b' + re.escape(v) + r'\b', ln, re.IGNORECASE):
                res.append(normalize_spaces(ln))
                break
    return res

def locate_person_line(lines, vaccine_block):
    for i, ln in enumerate(lines):
        l = ln.lower()
        if (("nombre" in l or "nombres" in l or "apellidos" in l) and
            ("documento" in l or "identific" in l) and
            ("fecha" in l or "nacimiento" in l) and
            ("edad" in l)):
            if i + 1 < len(lines):
                return normalize_spaces(lines[i + 1])
    if vaccine_block and len(vaccine_block) >= 2:
        candidate = vaccine_block[1]
        if DOC_RE.search(candidate):
            return candidate
    for ln in lines:
        if DOC_RE.search(ln) and DATE_RE_GENERIC.search(ln):
            return normalize_spaces(ln)
    return None

def split_personal_line(line: str):
    if not line:
        return ("", "", "", "", "")
    ln = normalize_spaces(line)
    mdoc = DOC_RE.search(ln)
    if not mdoc:
        mdate = DATE_RE_GENERIC.search(ln)
        if mdate:
            date = normalize_spaces(mdate.group(1))
            before = ln[:mdate.start()].strip()
            parts = before.split()
            if len(parts) >= 2:
                apellidos = " ".join(parts[-2:])
                nombres = " ".join(parts[:-2]) or ""
            else:
                apellidos = before
                nombres = ""
            age = normalize_spaces(ln[mdate.end():])
            return (nombres, apellidos, "", date, age)
        return ("", "", "", "", "")
    doc = mdoc.group(1)
    before = ln[:mdoc.start()].strip()
    after = ln[mdoc.end():].strip()
    parts = before.split()
    if len(parts) >= 2:
        apellidos = " ".join(parts[-2:])
        nombres = " ".join(parts[:-2]) or ""
    elif len(parts) == 1:
        apellidos = parts[0]
        nombres = ""
    else:
        apellidos = ""
        nombres = ""
    mdate = DATE_RE_GENERIC.search(after)
    date = mdate.group(1) if mdate else ""
    age = ""
    if mdate:
        age = normalize_spaces(after[mdate.end():])
    else:
        m_age = re.search(r'(\d{1,3}\s*(?:años|año|meses|mes)(?:\s*-\s*\d+\s*\w+)*)', after, re.IGNORECASE)
        if m_age:
            age = m_age.group(1)
            before_age = after[:m_age.start()].strip()
            mdate2 = DATE_RE_GENERIC.search(before_age)
            date = mdate2.group(1) if mdate2 else ""
    return (normalize_spaces(nombres), normalize_spaces(apellidos), normalize_spaces(doc), normalize_spaces(date), normalize_spaces(age))

def parse_single_vaccine_line(line: str):
    raw = normalize_spaces(line)
    res = {f: "" for f in VACCINE_FIELDS}
    res["VacunaRaw"] = raw
    if not raw:
        return res
    m_age = AGE_AT_VAX_RE.match(raw)
    if m_age:
        res["Edad"] = m_age.group(0).strip()
        remaining = raw[m_age.end():].strip()
    else:
        remaining = raw
    mdate = DATE_RE_GENERIC.search(remaining)
    if mdate:
        res["FechaAplicacion"] = normalize_spaces(mdate.group(1))
        left = remaining[:mdate.start()].strip()
        right = remaining[mdate.end():].strip()
    else:
        left = remaining
        right = ""
    m_dose = DOSE_WORDS.search(left)
    if m_dose:
        res["Dosis"] = m_dose.group(1)
        vac_name = (left[:m_dose.start()] + left[m_dose.end():]).strip()
        res["Vacuna"] = normalize_spaces(vac_name)
    else:
        res["Vacuna"] = normalize_spaces(left)
    if right:
        tokens = right.split()
        lab = ""
        lote = ""
        ips = ""
        vacunador = ""
        if tokens:
            if re.match(r'^[A-ZÁÉÍÓÚÑ0-9\-]{2,}$', tokens[0]):
                lab = tokens[0]
                if len(tokens) >= 2:
                    lote = tokens[1]
                    ips_tokens = tokens[2:]
                    if '*' in ips_tokens:
                        idx = ips_tokens.index('*')
                        ips = " ".join(ips_tokens[:idx]).strip()
                        vacunador = " ".join(ips_tokens[idx + 1:]).strip()
                    else:
                        ips = " ".join(ips_tokens).strip()
            else:
                for i, t in enumerate(tokens):
                    if t.upper() in ("ABBOTT", "PFIZER", "MODERNA", "SINOVAC", "ASTRAZENECA"):
                        lab = t
                        lote = tokens[i + 1] if i + 1 < len(tokens) else ""
                        ips = " ".join(tokens[i + 2:]) if i + 2 < len(tokens) else ""
                        break
                if not lab:
                    ips = " ".join(tokens).strip()
        res["Laboratorio"] = normalize_spaces(lab)
        res["NumeroDeLote"] = normalize_spaces(lote)
        res["IPS"] = normalize_spaces(ips)
        res["Vacunador"] = normalize_spaces(vacunador)
    return res

# ---------------- Excel helpers ----------------
def build_header_row():
    headers = []
    headers.extend(PERSON_HEADERS)
    for i in range(1, MAX_VACCINES + 1):
        for f in VACCINE_FIELDS:
            headers.append(f"{f}_V{i}")
    return headers

def append_row_to_excel(path_xlsx, row_values):
    path = Path(path_xlsx)
    headers = build_header_row()
    if not path.exists():
        wb = Workbook()
        ws = wb.active
        ws.title = "vacunas"
        for col, h in enumerate(headers, start=1):
            ws.cell(row=1, column=col, value=h)
        for col, val in enumerate(row_values, start=1):
            ws.cell(row=2, column=col, value=val)
        wb.save(str(path))
    else:
        wb = load_workbook(str(path_xlsx))
        ws = wb.active
        next_row = ws.max_row + 1
        for col, val in enumerate(row_values, start=1):
            ws.cell(row=next_row, column=col, value=val)
        wb.save(str(path_xlsx))

# ---------------- Main PDF analyze flow ----------------
def analyze_pdf(path, ocr_fallback=True, ocr_force=False):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = ""
    if not ocr_force:
        text = extract_text_with_pdfplumber(str(path))
    if (not text or len(text.strip()) < 50) and ocr_fallback:
        text = extract_text_with_ocr(str(path))
    if not text:
        text = ""
    lines = [normalize_spaces(ln) for ln in text.splitlines() if normalize_spaces(ln)]
    vaccine_block = find_vaccine_block(lines)
    person_line = locate_person_line(lines, vaccine_block)
    return {
        "file": str(path),
        "raw_lines": lines,
        "vaccine_block": vaccine_block,
        "person_line": person_line,
    }

# ---------------- Helpers para batch desde ZIP ----------------
def extract_zip_and_find_pdfs(zip_path: Path, temp_root: Path):
    out_dir = temp_root / zip_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    pdfs = []
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(path=str(out_dir))
    except zipfile.BadZipFile:
        return []
    for p in out_dir.rglob("*.pdf"):
        pdfs.append(p)
    return pdfs

def make_row_from_result(res):
    """
    Construye la fila (lista) usando las mismas reglas que export_to_excel_action.
    """
    lines = res.get("raw_lines", []) or []
    vaccine_block = res.get("vaccine_block", []) or []
    person_line = res.get("person_line")

    if not person_line:
        for ln in lines:
            if DOC_RE.search(ln) and DATE_RE_GENERIC.search(ln):
                person_line = ln
                break

    nombres, apellidos, documento, fecha_nac, edad = split_personal_line(person_line or "")

    vb = [ln for ln in vaccine_block if ln and (ln != person_line)]
    vb_filtered = []
    for ln in vb:
        lcl = ln.lower()
        if ("programa de vacun" in lcl) or ("nombres" in lcl and "documento" in lcl) or ("edad vacuna" in lcl) or ("vacunador" in lcl):
            continue
        vb_filtered.append(ln)
    vaccine_lines = vb_filtered[:MAX_VACCINES]

    if not vaccine_lines:
        for ln in lines:
            for k in KNOWN_VACCINES:
                if re.search(r'\b' + re.escape(k) + r'\b', ln, re.IGNORECASE):
                    if ln != person_line and ln not in vaccine_lines:
                        vaccine_lines.append(ln)
                        break
            if len(vaccine_lines) >= MAX_VACCINES:
                break

    parsed_vaccines = []
    for vl in vaccine_lines[:MAX_VACCINES]:
        parsed_vaccines.append(parse_single_vaccine_line(vl))

    row = []
    row.extend([nombres, apellidos, documento, fecha_nac, edad])
    for i in range(MAX_VACCINES):
        if i < len(parsed_vaccines):
            pv = parsed_vaccines[i]
            for f in VACCINE_FIELDS:
                row.append(pv.get(f, ""))
        else:
            for _ in VACCINE_FIELDS:
                row.append("")
    return row

def process_zip_folder_and_append(zip_folder: Path, output_xlsx: Path, ocr_fallback=True, ocr_force=False, ui_callback=None):
    """
    Recorre la carpeta zip_folder, extrae PDFs dentro de cada .zip, procesa cada PDF
    y añade la fila al output_xlsx. ui_callback (si se pasa) se llama con mensajes para mostrar en la GUI.
    """
    zip_folder = Path(zip_folder)
    output_xlsx = Path(output_xlsx)
    if not zip_folder.exists():
        raise FileNotFoundError(zip_folder)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    processed = 0
    with tempfile.TemporaryDirectory() as td:
        temp_root = Path(td)
        for entry in sorted(zip_folder.iterdir()):
            if entry.is_file() and entry.suffix.lower() == ".zip":
                if ui_callback:
                    ui_callback(f"Procesando ZIP: {entry.name}")
                pdfs = extract_zip_and_find_pdfs(entry, temp_root)
                if not pdfs:
                    if ui_callback:
                        ui_callback(f"  - No se encontraron PDFs en {entry.name}")
                for pdf in pdfs:
                    try:
                        if ui_callback:
                            ui_callback(f"  - Analizando PDF: {pdf.relative_to(temp_root)}")
                        res = analyze_pdf(str(pdf), ocr_fallback=ocr_fallback, ocr_force=ocr_force)
                        row = make_row_from_result(res)
                        append_row_to_excel(str(output_xlsx), row)
                        processed += 1
                        if ui_callback:
                            ui_callback(f"    -> Añadida fila para {Path(res.get('file', str(pdf))).name}")
                    except Exception as e:
                        if ui_callback:
                            ui_callback(f"    ERROR al procesar {pdf.name}: {e}")
                        traceback.print_exc(file=sys.stderr)
    return processed

# ---------------- GUI ----------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Extractor -> Excel columnas separadas (PDF individuel / ZIP folder)")
        root.geometry("980x650")

        frm = tk.Frame(root)
        frm.pack(padx=10, pady=8, fill=tk.X)

        self.select_btn = tk.Button(frm, text="Seleccionar PDF", command=self.select_file)
        self.select_btn.pack(side=tk.LEFT)

        self.select_zip_btn = tk.Button(frm, text="Procesar carpeta (ZIP)", command=self.select_zip_folder)
        self.select_zip_btn.pack(side=tk.LEFT, padx=6)

        self.ocr_var = tk.BooleanVar(value=False)
        self.ocr_check = tk.Checkbutton(frm, text="Forzar OCR", variable=self.ocr_var)
        self.ocr_check.pack(side=tk.LEFT, padx=8)

        self.export_btn = tk.Button(frm, text="Exportar a Excel (columnas)", command=self.export_to_excel_action, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=8)

        # si quieres quitar JSON, mantener el botón deshabilitado o eliminarlo; lo dejo por compatibilidad
        self.save_btn = tk.Button(frm, text="Guardar JSON", command=self.save_json, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=8)

        self.status_label = tk.Label(root, text="Seleccione un PDF o una carpeta ZIP para empezar.")
        self.status_label.pack(fill=tk.X, padx=10, pady=(4,6))

        self.output = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=34)
        self.output.pack(padx=10, pady=6, fill=tk.BOTH, expand=True)

        self.current_result = None
        self.current_file = None

    def select_file(self):
        fn = filedialog.askopenfilename(title="Seleccionar archivo PDF", filetypes=[("PDF files","*.pdf"),("All files","*.*")])
        if not fn:
            return
        self.current_file = fn
        self.status_label.config(text=f"Analizando: {fn} ...")
        self.output.delete("1.0", tk.END)
        self.export_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        th = threading.Thread(target=self._analyze_file_thread, args=(fn, self.ocr_var.get()), daemon=True)
        th.start()

    def select_zip_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta que contiene archivos .zip")
        if not folder:
            return
        # pedir archivo Excel de salida (solo una vez)
        out_fn = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")], title="Guardar archivo Excel de salida")
        if not out_fn:
            return
        self.status_label.config(text=f"Procesando carpeta: {folder} ...")
        self.output.delete("1.0", tk.END)
        self.export_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        th = threading.Thread(target=self._process_zip_folder_thread, args=(folder, out_fn, self.ocr_var.get()), daemon=True)
        th.start()

    def _process_zip_folder_thread(self, folder, out_fn, ocr_force):
        try:
            def ui_cb(msg):
                # se llama en hilo de trabajo; programar en main thread
                self.root.after(0, lambda: self.output.insert(tk.END, msg + "\n"))
            processed = process_zip_folder_and_append(Path(folder), Path(out_fn), ocr_fallback=True, ocr_force=ocr_force, ui_callback=ui_cb)
            self.root.after(0, lambda: self.status_label.config(text=f"Procesado carpeta: {folder} -> {processed} PDFs añadidos a {out_fn}"))
            self.root.after(0, lambda: messagebox.showinfo("Procesado", f"Procesados: {processed} PDFs\nSalida: {out_fn}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error: {e}"))
            traceback.print_exc(file=sys.stderr)
        finally:
            self.root.after(0, lambda: self.export_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))

    def _analyze_file_thread(self, fn, ocr_force):
        try:
            res = analyze_pdf(fn, ocr_fallback=True, ocr_force=ocr_force)
            self.current_result = res
            self.root.after(0, lambda: self._display_result(res))
        except FileNotFoundError:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Archivo no encontrado: {fn}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error: {e}"))
            traceback.print_exc(file=sys.stderr)
        finally:
            self.root.after(0, lambda: self.status_label.config(text=f"Analizado: {fn}"))

    def _display_result(self, res):
        self.output.delete("1.0", tk.END)
        out = []
        out.append("LÍNEA DETECTADA DE PERSONA:")
        out.append(res.get("person_line") or "(no encontrada)")
        out.append("")
        out.append("BLOQUE DETECTADO DE VACUNAS (líneas):")
        for ln in res.get("vaccine_block", []):
            out.append(f" - {ln}")
        out.append("")
        out.append("SNIPPET (primeras líneas):")
        for i, ln in enumerate(res.get("raw_lines", [])[:20]):
            out.append(f"{i+1:02d}: {ln}")
        self.output.insert(tk.END, "\n".join(out))
        self.export_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)

    def save_json(self):
        # Función útil durante debugging; no requerida por petición, se mantiene por compatibilidad
        if not self.current_result:
            return
        fn = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")], title="Guardar resultado JSON")
        if not fn:
            return
        try:
            with open(fn, "w", encoding="utf-8") as fh:
                json.dump(self.current_result, fh, ensure_ascii=False, indent=2)
            messagebox.showinfo("Guardado", f"Resultado guardado en: {fn}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def export_to_excel_action(self):
        # exporta fila del documento actualmente mostrado en GUI (igual que antes)
        if not self.current_result:
            messagebox.showinfo("Aviso", "Primero selecciona un PDF y espera a que termine el análisis.")
            return

        lines = self.current_result.get("raw_lines", []) or []
        vaccine_block = self.current_result.get("vaccine_block", []) or []
        person_line = self.current_result.get("person_line")

        if not person_line:
            for ln in lines:
                if DOC_RE.search(ln) and DATE_RE_GENERIC.search(ln):
                    person_line = ln
                    break

        if not person_line:
            if not messagebox.askyesno("Confirmar", "No se pudo localizar la línea personal exacta. ¿Deseas exportar igualmente usando lo disponible?"):
                return

        nombres, apellidos, documento, fecha_nac, edad = split_personal_line(person_line or "")

        vaccine_lines = []
        vb = [ln for ln in vaccine_block if ln and (ln != person_line)]
        vb_filtered = []
        for ln in vb:
            lcl = ln.lower()
            if ("programa de vacun" in lcl) or ("nombres" in lcl and "documento" in lcl) or ("edad vacuna" in lcl) or ("vacunador" in lcl):
                continue
            vb_filtered.append(ln)
        vaccine_lines = vb_filtered[:MAX_VACCINES]

        if not vaccine_lines:
            for ln in lines:
                for k in KNOWN_VACCINES:
                    if re.search(r'\b' + re.escape(k) + r'\b', ln, re.IGNORECASE):
                        if ln != person_line and ln not in vaccine_lines:
                            vaccine_lines.append(ln)
                            break
                if len(vaccine_lines) >= MAX_VACCINES:
                    break

        parsed_vaccines = []
        for vl in vaccine_lines[:MAX_VACCINES]:
            parsed_vaccines.append(parse_single_vaccine_line(vl))

        row = []
        row.extend([nombres, apellidos, documento, fecha_nac, edad])
        for i in range(MAX_VACCINES):
            if i < len(parsed_vaccines):
                pv = parsed_vaccines[i]
                for f in VACCINE_FIELDS:
                    row.append(pv.get(f, ""))
            else:
                for _ in VACCINE_FIELDS:
                    row.append("")

        fn = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")], title="Guardar archivo Excel")
        if not fn:
            return
        try:
            append_row_to_excel(fn, row)
            messagebox.showinfo("Exportado", f"Datos exportados a: {fn}")
            self.output.insert(tk.END, "\n\nEXPORTADO A EXCEL (fila añadida):\n")
            self.output.insert(tk.END, f"Nombres: {nombres}\nApellidos: {apellidos}\nDocumento: {documento}\nFecha Nac: {fecha_nac}\nEdad: {edad}\n")
            for idx, pv in enumerate(parsed_vaccines, start=1):
                self.output.insert(tk.END, f"\nVacuna {idx} raw: {pv.get('VacunaRaw')}\n  Edad: {pv.get('Edad')}\n  Vacuna: {pv.get('Vacuna')}\n  Dosis: {pv.get('Dosis')}\n  Fecha: {pv.get('FechaAplicacion')}\n  Laboratorio: {pv.get('Laboratorio')}\n  Lote: {pv.get('NumeroDeLote')}\n  IPS: {pv.get('IPS')}\n  Vacunador: {pv.get('Vacunador')}\n")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()