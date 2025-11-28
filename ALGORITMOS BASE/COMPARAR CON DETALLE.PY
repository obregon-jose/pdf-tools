# import os
# import re
# import csv
# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox

# # ---------- utilidades ----------
# def normalize(s: str) -> str:
#     if not s:
#         return ""
#     s = s.strip()
#     if s.lower().endswith(".pdf"):
#         s = s[:-4]
#     s = s.replace("-", " ").replace("_", " ")
#     s = " ".join(s.split())
#     return s.lower()

# def compact(s: str) -> str:
#     """Versión compacta sin espacios/guiones/underscores (todo junto)."""
#     return re.sub(r'[\s\-_]+', '', normalize(s))

# def digits_only(s: str) -> str:
#     return "".join(re.findall(r"\d+", s))

# def build_index(folder: str):
#     """Devuelve lista de archivos pdf y varios índices para busqueda."""
#     archivos = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(".pdf")]
#     index = []
#     for f in archivos:
#         name_no_ext = os.path.splitext(f)[0]
#         rec = {
#             "file": f,
#             "norm": normalize(name_no_ext),
#             "compact": compact(name_no_ext),
#             "digits": digits_only(name_no_ext)
#         }
#         index.append(rec)
#     return index

# # ---------- lógica de búsqueda ----------
# def find_matches_for(term: str, index):
#     term_raw = term.strip()
#     if not term_raw:
#         return []

#     t_norm = normalize(term_raw)
#     t_compact = compact(term_raw)
#     t_digits = digits_only(term_raw)

#     matches = []
#     # Estrategia 1: coincidencia compacta exacta
#     for rec in index:
#         if t_compact and t_compact == rec["compact"]:
#             matches.append((rec["file"], "compact_exact"))
#     # Estrategia 2: subcadena normalizada (espacios respetados)
#     if not matches:
#         for rec in index:
#             if t_norm and t_norm in rec["norm"]:
#                 matches.append((rec["file"], "norm_substring"))
#     # Estrategia 3: buscar dígitos en el nombre (si term tiene dígitos)
#     if not matches and t_digits:
#         for rec in index:
#             # si los dígitos completos aparecen en el nombre del archivo:
#             if t_digits and t_digits in rec["digits"]:
#                 matches.append((rec["file"], "digits_substring"))
#     # Estrategia 4: compact match as substring
#     if not matches:
#         for rec in index:
#             if t_compact and t_compact in rec["compact"]:
#                 matches.append((rec["file"], "compact_substring"))
#     # Estrategia 5: buscar solo parte numérica larga (últimos N dígitos) - útil si hay prefijos
#     if not matches and t_digits and len(t_digits) >= 6:
#         # probar con últimas 6..10 cifras (descendente)
#         for L in range(min(10, len(t_digits)), 5, -1):
#             tail = t_digits[-L:]
#             for rec in index:
#                 if tail in rec["digits"]:
#                     matches.append((rec["file"], f"digits_tail_{L}"))
#             if matches:
#                 break

#     # eliminar duplicados (mantener estrategia primera encontrada)
#     seen = set()
#     unique = []
#     for f, why in matches:
#         if f not in seen:
#             unique.append((f, why))
#             seen.add(f)
#     return unique

# # ---------- GUI ----------
# def seleccionar_carpeta():
#     carpeta = filedialog.askdirectory(title="Selecciona la carpeta con los archivos PDF")
#     if carpeta:
#         entry_carpeta.delete(0, tk.END)
#         entry_carpeta.insert(0, carpeta)

# def verificar_archivos():
#     carpeta = entry_carpeta.get().strip()
#     if not carpeta or not os.path.isdir(carpeta):
#         messagebox.showwarning("Carpeta no válida", "Por favor selecciona una carpeta válida que contenga los PDF.")
#         return

#     listado = text_nombres.get("1.0", tk.END).strip().splitlines()
#     if not listado:
#         messagebox.showwarning("Listado vacío", "Por favor ingresa al menos un nombre de archivo.")
#         return

#     # limpiar tabla
#     for row in tabla.get_children():
#         tabla.delete(row)

#     index = build_index(carpeta)

#     encontrados = 0
#     no_encontrados = 0

#     for nombre in listado:
#         raw = nombre.strip()
#         if not raw:
#             continue

#         matches = find_matches_for(raw, index)
#         if matches:
#             encontrados += 1
#             for file_name, why in matches:
#                 tabla.insert("", "end", values=(raw, "ENCONTRADO", file_name, why))
#         else:
#             no_encontrados += 1
#             tabla.insert("", "end", values=(raw, "NO ENCONTRADO", "", ""))

#     messagebox.showinfo("Verificación completa", f"Encontrados: {encontrados}  |  No encontrados: {no_encontrados}")

# def exportar_csv():
#     ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Guardar resultados como...")
#     if not ruta:
#         return
#     rows = []
#     for row_id in tabla.get_children():
#         rows.append(tabla.item(row_id)["values"])
#     try:
#         with open(ruta, "w", newline="", encoding="utf-8") as f:
#             import csv
#             writer = csv.writer(f)
#             writer.writerow(["Nombre buscado", "Estado", "Archivo encontrado", "Estrategia"])
#             writer.writerows(rows)
#         messagebox.showinfo("Exportado", f"Resultados guardados en:\n{ruta}")
#     except Exception as e:
#         messagebox.showerror("Error", f"No se pudo guardar CSV: {e}")

# # Interfaz
# root = tk.Tk()
# root.title("Verificador robusto de PDFs por nombre")
# root.geometry("950x600")
# root.resizable(True, True)

# frame_carpeta = tk.Frame(root)
# frame_carpeta.pack(padx=10, pady=8, fill="x")
# tk.Label(frame_carpeta, text="Carpeta con los PDFs:").pack(side="left")
# entry_carpeta = tk.Entry(frame_carpeta, width=80)
# entry_carpeta.pack(side="left", padx=5)
# tk.Button(frame_carpeta, text="Seleccionar...", command=seleccionar_carpeta, bg="#0078D4", fg="white").pack(side="left")

# tk.Label(root, text="Pega los nombres que quieres verificar (uno por línea). Ejemplos:\nASIRC1078118477\nRC1078118477").pack(anchor="w", padx=12)
# text_nombres = tk.Text(root, height=8, width=110)
# text_nombres.pack(padx=12, pady=6)

# frame_botones = tk.Frame(root)
# frame_botones.pack(pady=6)
# tk.Button(frame_botones, text="Verificar Archivos", command=verificar_archivos, bg="#0078D4", fg="white", width=20).pack(side="left", padx=6)
# tk.Button(frame_botones, text="Exportar resultados a CSV", command=exportar_csv, width=20).pack(side="left", padx=6)

# frame_tabla = tk.Frame(root)
# frame_tabla.pack(padx=12, pady=8, fill="both", expand=True)

# columns = ("nombre_busqueda", "estado", "archivo_encontrado", "estrategia")
# tabla = ttk.Treeview(frame_tabla, columns=columns, show="headings")
# tabla.heading("nombre_busqueda", text="Nombre Buscado")
# tabla.heading("estado", text="Estado")
# tabla.heading("archivo_encontrado", text="Archivo Encontrado")
# tabla.heading("estrategia", text="Estrategia")
# tabla.column("nombre_busqueda", width=300)
# tabla.column("estado", width=120)
# tabla.column("archivo_encontrado", width=380)
# tabla.column("estrategia", width=120)

# scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
# tabla.configure(yscroll=scroll_y.set)
# scroll_y.pack(side="right", fill="y")
# tabla.pack(fill="both", expand=True)

# tk.Label(root, text="Nota: la columna 'Estrategia' te indica cómo se encontró la coincidencia (útil para depurar).").pack(pady=6)

# root.mainloop()


import os
import re
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ---------- utilidades ----------
def normalize(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    if s.lower().endswith(".pdf"):
        s = s[:-4]
    s = s.replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    return s.lower()

def compact(s: str) -> str:
    """Versión compacta sin espacios/guiones/underscores (todo junto)."""
    return re.sub(r'[\s\-_]+', '', normalize(s))

def digits_only(s: str) -> str:
    return "".join(re.findall(r"\d+", s))

def build_index(folder: str):
    """Devuelve lista de archivos pdf y varios índices para busqueda."""
    archivos = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(".pdf")]
    index = []
    for f in archivos:
        name_no_ext = os.path.splitext(f)[0]
        rec = {
            "file": f,
            "norm": normalize(name_no_ext),
            "compact": compact(name_no_ext),
            "digits": digits_only(name_no_ext),
            # Guardamos también el nombre sin extensión tal cual para búsquedas con límites
            "orig_name_no_ext": name_no_ext
        }
        index.append(rec)
    return index

# ---------- lógica de búsqueda ----------
def find_matches_for(term: str, index):
    term_raw = term.strip()
    if not term_raw:
        return []

    t_norm = normalize(term_raw)
    t_compact = compact(term_raw)
    t_digits = digits_only(term_raw)
    term_digits_only = term_raw.isdigit()  # True si el término ingresado es únicamente dígitos

    matches = []
    # Estrategia 1: coincidencia compacta exacta
    for rec in index:
        if t_compact and t_compact == rec["compact"]:
            matches.append((rec["file"], "compact_exact"))
    # Estrategia 2: subcadena normalizada (espacios respetados)
    if not matches:
        for rec in index:
            if t_norm and t_norm in rec["norm"]:
                matches.append((rec["file"], "norm_substring"))
    # Estrategia 3: buscar dígitos en el nombre (si term tiene dígitos)
    # Mejora: si el término es SOLO dígitos, requerimos que esos dígitos estén delimitados (no formar parte de una secuencia mayor).
    if not matches and t_digits:
        if term_digits_only:
            pattern = re.compile(r'(?<!\d)'+re.escape(t_digits)+r'(?!\d)')
            for rec in index:
                if pattern.search(rec["orig_name_no_ext"]):
                    matches.append((rec["file"], "digits_token_exact"))
        else:
            for rec in index:
                if t_digits and t_digits in rec["digits"]:
                    matches.append((rec["file"], "digits_substring"))
    # Estrategia 4: compact match as substring
    if not matches:
        for rec in index:
            if t_compact and t_compact in rec["compact"]:
                matches.append((rec["file"], "compact_substring"))
    # Estrategia 5: buscar solo parte numérica larga (últimos N dígitos)
    if not matches and t_digits and len(t_digits) >= 6:
        for L in range(min(10, len(t_digits)), 5, -1):
            tail = t_digits[-L:]
            for rec in index:
                if tail in rec["digits"]:
                    matches.append((rec["file"], f"digits_tail_{L}"))
            if matches:
                break

    # eliminar duplicados (mantener estrategia primera encontrada)
    seen = set()
    unique = []
    for f, why in matches:
        if f not in seen:
            unique.append((f, why))
            seen.add(f)
    return unique

# ---------- GUI ----------
def seleccionar_carpeta():
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta con los archivos PDF")
    if carpeta:
        entry_carpeta.delete(0, tk.END)
        entry_carpeta.insert(0, carpeta)

def verificar_archivos():
    carpeta = entry_carpeta.get().strip()
    if not carpeta or not os.path.isdir(carpeta):
        messagebox.showwarning("Carpeta no válida", "Por favor selecciona una carpeta válida que contenga los PDF.")
        return

    listado = text_nombres.get("1.0", tk.END).strip().splitlines()
    if not listado:
        messagebox.showwarning("Listado vacío", "Por favor ingresa al menos un nombre de archivo.")
        return

    # limpiar tabla
    for row in tabla.get_children():
        tabla.delete(row)

    index = build_index(carpeta)
    all_files = {rec["file"] for rec in index}
    found_files = set()

    encontrados = 0
    no_encontrados = 0

    for nombre in listado:
        raw = nombre.strip()
        if not raw:
            continue

        matches = find_matches_for(raw, index)
        if matches:
            encontrados += 1
            for file_name, why in matches:
                tabla.insert("", "end", values=(raw, "ENCONTRADO", file_name, why))
                found_files.add(file_name)
        else:
            no_encontrados += 1
            tabla.insert("", "end", values=(raw, "NO ENCONTRADO", "", ""))

    # Archivos presentes en la carpeta que NO fueron referenciados por ningún nombre del listado
    no_en_lista = sorted(list(all_files - found_files))
    for f in no_en_lista:
        # dejamos la columna "Nombre Buscado" vacía para indicar que es un archivo que no está en el listado
        tabla.insert("", "end", values=("", "NO EN LISTADO", f, ""))

    messagebox.showinfo(
        "Verificación completa",
        f"Entradas en el listado: {len([l for l in listado if l.strip()])}\n"
        f"Encontrados (inputs con al menos una coincidencia): {encontrados}\n"
        f"No encontrados (inputs sin coincidencia): {no_encontrados}\n"
        f"Archivos en la carpeta no referenciados por el listado: {len(no_en_lista)}"
    )

def exportar_csv():
    ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Guardar resultados como...")
    if not ruta:
        return
    rows = []
    for row_id in tabla.get_children():
        rows.append(tabla.item(row_id)["values"])
    try:
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Nombre buscado", "Estado", "Archivo encontrado", "Estrategia"])
            writer.writerows(rows)
        messagebox.showinfo("Exportado", f"Resultados guardados en:\n{ruta}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar CSV: {e}")

# Interfaz
root = tk.Tk()
root.title("Verificador robusto de PDFs por nombre")
root.geometry("950x600")
root.resizable(True, True)

frame_carpeta = tk.Frame(root)
frame_carpeta.pack(padx=10, pady=8, fill="x")
tk.Label(frame_carpeta, text="Carpeta con los PDFs:").pack(side="left")
entry_carpeta = tk.Entry(frame_carpeta, width=80)
entry_carpeta.pack(side="left", padx=5)
tk.Button(frame_carpeta, text="Seleccionar...", command=seleccionar_carpeta, bg="#0078D4", fg="white").pack(side="left")

tk.Label(root, text="Pega los nombres que quieres verificar (uno por línea). Ejemplos:\nASIRC1078118477\nRC1078118477").pack(anchor="w", padx=12)
text_nombres = tk.Text(root, height=8, width=110)
text_nombres.pack(padx=12, pady=6)

frame_botones = tk.Frame(root)
frame_botones.pack(pady=6)
tk.Button(frame_botones, text="Verificar Archivos", command=verificar_archivos, bg="#0078D4", fg="white", width=20).pack(side="left", padx=6)
tk.Button(frame_botones, text="Exportar resultados a CSV", command=exportar_csv, width=20).pack(side="left", padx=6)

frame_tabla = tk.Frame(root)
frame_tabla.pack(padx=12, pady=8, fill="both", expand=True)

columns = ("nombre_busqueda", "estado", "archivo_encontrado", "estrategia")
tabla = ttk.Treeview(frame_tabla, columns=columns, show="headings")
tabla.heading("nombre_busqueda", text="Nombre Buscado")
tabla.heading("estado", text="Estado")
tabla.heading("archivo_encontrado", text="Archivo Encontrado")
tabla.heading("estrategia", text="Estrategia")
tabla.column("nombre_busqueda", width=300)
tabla.column("estado", width=140)
tabla.column("archivo_encontrado", width=340)
tabla.column("estrategia", width=120)

scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
tabla.configure(yscroll=scroll_y.set)
scroll_y.pack(side="right", fill="y")
tabla.pack(fill="both", expand=True)

tk.Label(root, text="Nota: la columna 'Estrategia' te indica cómo se encontró la coincidencia. Las filas con 'NO EN LISTADO' son archivos presentes en la carpeta que no aparecen en tu listado de búsqueda.").pack(pady=6)

root.mainloop()