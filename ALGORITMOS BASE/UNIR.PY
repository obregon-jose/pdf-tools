#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unir PDFs por prefijo (texto EXACTO case-sensitive antes del primer espacio o punto).
- Muestra SOLO grupos que tengan más de 1 PDF.
- Interfaz tipo acordeón: cada item despliega la lista de PDFs justo debajo del encabezado.
- Al unir: mueve los archivos originales a carpeta "Grupos" y crea el PDF unido en la carpeta original
  con el nombre del grupo (si ya existe, no sobrescribe; añade sufijo _1, _2...).
- No se eliminan los originales; quedan en la carpeta "Grupos".
"""
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from PyPDF2 import PdfMerger
except Exception as e:
    raise RuntimeError("PyPDF2 no está instalado. Instale con: pip install PyPDF2") from e

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception:
    raise RuntimeError("Tkinter no está disponible en este entorno. Ejecuta en un entorno con GUI.")

# -----------------------
# Utilidades
# -----------------------
def natural_key(s: str):
    parts = re.split(r'(\d+)', s)
    key = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p)
    return key

def crear_nombre_unico(ruta: Path) -> Path:
    """Si ruta existe, añade sufijo _1, _2... antes de la extensión."""
    if not ruta.exists():
        return ruta
    base = ruta.stem
    ext = ruta.suffix
    parent = ruta.parent
    i = 1
    while True:
        candidato = parent / f"{base}_{i}{ext}"
        if not candidato.exists():
            return candidato
        i += 1

def prefix_case_sensitive(nombre: str) -> str:
    """
    Extrae el texto EXACTO (respetando mayúsculas/minúsculas) antes del primer espacio o punto,
    sin la extensión .pdf.
    """
    nombre_sin_ext = re.sub(r'\.pdf$', '', nombre, flags=re.IGNORECASE)
    m = re.search(r'[.\s]', nombre_sin_ext)
    if m:
        return nombre_sin_ext[:m.start()]
    return nombre_sin_ext

def obtener_grupos_case_sensitive(carpeta: str) -> Dict[str, List[str]]:
    """
    Recorre la carpeta y agrupa PDFs por el prefijo EXACTO antes del primer espacio o punto.
    Devuelve solo los grupos con más de 1 PDF (tal y como solicitaste).
    """
    temp: Dict[str, List[str]] = {}
    try:
        nombres = sorted(os.listdir(carpeta), key=natural_key)
    except Exception:
        nombres = os.listdir(carpeta)
    for nombre in nombres:
        if not nombre.lower().endswith(".pdf"):
            continue
        clave = prefix_case_sensitive(nombre)
        temp.setdefault(clave, []).append(nombre)
    # Filtrar solo grupos con más de 1 archivo
    grupos = {k: v for k, v in temp.items() if len(v) > 1}
    # Ordenar por clave con orden natural
    return dict(sorted(grupos.items(), key=lambda kv: natural_key(kv[0])))

# -----------------------
# Operaciones de unión y movimiento
# -----------------------
def mover_originales_a_grupo(folder: Path, archivos: List[str], grupo_dir: Path) -> Tuple[List[Path], List[str]]:
    """
    Mueve los 'archivos' (nombres relativos en folder) a grupo_dir.
    Devuelve (lista_de_paths_destino, lista_de_errores)
    Se usa crear_nombre_unico para evitar colisiones.
    """
    moved_paths: List[Path] = []
    errores: List[str] = []
    grupo_dir.mkdir(parents=True, exist_ok=True)
    for nombre in archivos:
        src = folder / nombre
        if not src.exists():
            errores.append(f"No existe: {nombre}")
            continue
        dst = grupo_dir / nombre
        if dst.exists():
            dst = crear_nombre_unico(dst)
        try:
            shutil.move(str(src), str(dst))
            moved_paths.append(dst)
        except Exception as e:
            errores.append(f"Error moviendo '{nombre}' a '{grupo_dir}': {e}")
    return moved_paths, errores

def unir_desde_paths_y_guardar(rutas: List[Path], salida_path: Path) -> List[str]:
    """
    Une los PDFs listados en rutas (Paths) y escribe en salida_path (Path).
    No sobrescribe salida_path (se espera llamar a crear_nombre_unico antes si se quiere).
    Devuelve lista de errores (vacía si exitosa).
    """
    errores: List[str] = []
    merger = PdfMerger()
    anexados = 0
    # ordenar naturalmente por nombre de archivo
    rutas_sorted = sorted(rutas, key=lambda p: natural_key(p.name))
    for p in rutas_sorted:
        try:
            merger.append(str(p))
            anexados += 1
        except Exception as e:
            errores.append(f"Error añadiendo '{p.name}': {e}")
    if anexados == 0:
        merger.close()
        errores.append("No se añadieron PDFs válidos para unir.")
        return errores
    try:
        with open(salida_path, "wb") as f_out:
            merger.write(f_out)
    except Exception as e:
        errores.append(f"Error escribiendo '{salida_path.name}': {e}")
    finally:
        merger.close()
    return errores

def unir_grupo_mover_y_crear(carpeta: str, clave: str, archivos: List[str]) -> Tuple[bool, List[str]]:
    """
    Procedimiento completo:
    - Crea carpeta 'Grupos' dentro de carpeta
    - Mueve los archivos originales del grupo allí (evitando colisiones)
    - Une los PDFs desde la carpeta 'Grupos' y guarda el archivo unido en la carpeta principal
      con el nombre EXACTO de la clave (preservando mayúsc/minúsc). Si ya existe en la carpeta
      principal, se evita sobrescribir con crear_nombre_unico.
    - Devuelve (success, errores)
    """
    errores: List[str] = []
    folder = Path(carpeta)
    grupo_dir = folder / "Grupos"
    # 1) mover originales a carpeta Grupos
    moved_paths, errs_move = mover_originales_a_grupo(folder, archivos, grupo_dir)
    if errs_move:
        errores.extend(errs_move)
        # si ningún archivo se movió, abortar
        if not moved_paths:
            return False, errores
    # 2) preparar salida en carpeta principal con nombre clave.pdf (preservando case)
    salida = folder / f"{clave}.pdf"
    salida_unica = crear_nombre_unico(salida) if salida.exists() else salida
    # 3) unir desde las rutas movidas
    errs_unir = unir_desde_paths_y_guardar(moved_paths, salida_unica)
    if errs_unir:
        errores.extend(errs_unir)
    success = len(errs_move) == 0 and len(errs_unir) == 0
    # Si hubo errores pero la unión produjo archivo, lo consideramos éxito parcial: devolver True y errores
    return True if not errs_unir else False, errores

# -----------------------
# UI - Acordeón (lista sólo grupos >1)
# -----------------------
class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.container = ttk.Frame(canvas)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0,0), window=self.container, anchor="nw")

        self.container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.container.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1*(ev.delta/120)), "units")))
        self.container.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Previsualizar y unir PDFs por grupo (case-sensitive)")
        self.geometry("920x640")
        self.carpeta = ""
        self.grupos: Dict[str, List[str]] = {}
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)

        self.lbl_carpeta = ttk.Label(top, text="Carpeta: (ninguna seleccionada)")
        self.lbl_carpeta.pack(side="left", fill="x", expand=True)

        btn_select = ttk.Button(top, text="Seleccionar carpeta", command=self.seleccionar_carpeta)
        btn_select.pack(side="right", padx=4)
        btn_refresh = ttk.Button(top, text="Refrescar", command=self.refrescar)
        btn_refresh.pack(side="right", padx=4)
        btn_unir_todos = ttk.Button(top, text="Unir todos (solo grupos >1)", command=self.unir_todos)
        btn_unir_todos.pack(side="right", padx=8)

        self.lbl_count = ttk.Label(self, text="Hay 0 grupos (se muestran solo grupos con >1 PDF)")
        self.lbl_count.pack(anchor="w", padx=12, pady=(6,0))

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=12, pady=8)

        lbl_log = ttk.Label(self, text="Log:")
        lbl_log.pack(anchor="w", padx=12)
        self.txt_log = tk.Text(self, height=6, wrap="word")
        self.txt_log.pack(fill="x", padx=12, pady=(0,8))

        self.status = ttk.Label(self, text="Listo", relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom")

    def log(self, *parts):
        texto = " ".join(str(p) for p in parts)
        self.txt_log.insert("end", texto + "\n")
        self.txt_log.see("end")

    def set_status(self, txt: str):
        self.status.config(text=txt)
        self.update_idletasks()

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if carpeta:
            self.carpeta = carpeta
            self.lbl_carpeta.config(text=f"Carpeta: {self.carpeta}")
            self.refrescar()

    def refrescar(self):
        if not self.carpeta:
            messagebox.showinfo("Sin carpeta", "Selecciona primero una carpeta.")
            return
        try:
            self.grupos = obtener_grupos_case_sensitive(self.carpeta)  # sólo >1
            n = len(self.grupos)
            self.lbl_count.config(text=f"Hay {n} grupo(s) (se muestran solo grupos con >1 PDF)")
            self._rebuild_accordion()
            self.log(f"Se encontraron {n} grupo(s).")
            self.set_status(f"Carpeta cargada: {self.carpeta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la carpeta: {e}")
            self.set_status("Error al leer carpeta")

    def _rebuild_accordion(self):
        # limpiar
        for w in self.scroll.container.winfo_children():
            w.destroy()

        # crear acordeón; cada header seguido inmediatamente por su panel ocultable
        for clave, archivos in self.grupos.items():
            header = ttk.Frame(self.scroll.container)
            header.pack(fill="x", pady=2, padx=2)

            lbl_text = f"{clave}   ({len(archivos)})"
            lbl = ttk.Label(header, text=lbl_text, font=("TkDefaultFont", 10, "bold"))
            lbl.pack(side="left", padx=6)

            tag = ttk.Label(header, text="SE PUEDE UNIR", foreground="green")
            tag.pack(side="left", padx=6)

            btn_unir = ttk.Button(header, text="Unir este grupo")
            btn_unir.pack(side="right", padx=4)
            btn_toggle = ttk.Button(header, text="+", width=3)
            btn_toggle.pack(side="right", padx=4)

            # panel inmediatamente debajo del header (en el mismo contenedor)
            panel = ttk.Frame(self.scroll.container)
            panel.pack(fill="x", padx=20, pady=(0,6))
            panel.pack_forget()  # oculto inicialmente

            lb = tk.Listbox(panel, height=min(8, max(3, len(archivos))), exportselection=False)
            lb.pack(fill="both", expand=True)
            for a in archivos:
                lb.insert("end", a)

            # toggle
            def make_toggle(p=panel, b=btn_toggle):
                def toggle():
                    if p.winfo_ismapped():
                        p.pack_forget()
                        b.config(text="+")
                    else:
                        p.pack(fill="x", padx=20, pady=(0,6))
                        b.config(text="-")
                return toggle

            # action unir
            def make_unir(c=clave, archivos_local=list(archivos)):
                def unir_click():
                    if not messagebox.askyesno("Confirmar unión", f"Unir {len(archivos_local)} PDFs del grupo '{c}'?\nSe moverán los originales a '{Path(self.carpeta)/'Grupos'}' y se creará '{c}.pdf' en la carpeta principal."):
                        return
                    self.set_status(f"Uniendo '{c}'...")
                    self.update_idletasks()
                    success, errs = unir_grupo_mover_y_crear(self.carpeta, c, archivos_local)
                    if success:
                        self.log(f"[OK] Grupo '{c}' unido. Salida: '{c}.pdf' (si ya existía se usó sufijo).")
                    else:
                        self.log(f"[FAIL] Grupo '{c}' no unido.")
                    for e in errs:
                        self.log(f"[{c}] {e}")
                    self.refrescar()
                    self.set_status("Operación completada")
                return unir_click

            btn_toggle.config(command=make_toggle())
            btn_unir.config(command=make_unir())

    def unir_todos(self):
        grupos_a_unir = list(self.grupos.keys())
        if not grupos_a_unir:
            messagebox.showinfo("Nada para unir", "No hay grupos con más de 1 PDF para unir.")
            return
        if not messagebox.askyesno("Confirmar unión", f"Se unirán {len(grupos_a_unir)} grupos. ¿Continuar?"):
            return
        resumen = {"unidos": 0, "errores": []}
        for clave in grupos_a_unir:
            archivos = list(self.grupos.get(clave, []))
            self.set_status(f"Unindo '{clave}' ({len(archivos)})...")
            self.update_idletasks()
            success, errs = unir_grupo_mover_y_crear(self.carpeta, clave, archivos)
            if success:
                resumen["unidos"] += 1
                self.log(f"[OK] {clave} -> '{clave}.pdf' (sufijo si existía).")
            else:
                self.log(f"[FAIL] {clave}")
            for e in errs:
                resumen["errores"].append(f"[{clave}] {e}")
                self.log(f"[{clave}] {e}")
        self.refrescar()
        mensaje = f"Se unieron {resumen['unidos']} grupo(s)."
        if resumen["errores"]:
            mensaje += "\n\nErrores:\n" + "\n".join(resumen["errores"])
        messagebox.showinfo("Resultado", mensaje)
        self.set_status("Operación completada")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()