# import os
# import shutil
# import pandas as pd
# from tkinter import filedialog, Tk, messagebox
# from datetime import datetime

# MESES = {
#     1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
#     5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
#     9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
# }

# def buscar_pdf(nombre_pdf, carpeta_base):
#     for root, dirs, files in os.walk(carpeta_base):
#         if nombre_pdf in files:
#             return os.path.join(root, nombre_pdf)
#     return None

# def procesar():
#     root = Tk()
#     root.withdraw()

#     archivo_excel = filedialog.askopenfilename(
#         title="Selecciona el archivo Excel",
#         filetypes=[("Archivo Excel", "*.xlsx *.xls")]
#     )
#     if not archivo_excel:
#         return

#     carpeta_busqueda = filedialog.askdirectory(title="Selecciona la carpeta donde buscar PDFs")
#     if not carpeta_busqueda:
#         return

#     carpeta_destino = filedialog.askdirectory(title="Selecciona la carpeta destino")
#     if not carpeta_destino:
#         return

#     # -----------------------------------
#     # LEER Y NORMALIZAR COLUMNAS DEL EXCEL
#     # -----------------------------------
#     df = pd.read_excel(archivo_excel)

#     # Quitar espacios y pasar a minúscula
#     df.columns = [col.strip().lower() for col in df.columns]

#     # Renombrar nombres equivalentes
#     equivalencias = {
#         "fecha": "fecha",
#         "fechas": "fecha",
#         "archivo": "archivo",
#         "archivos": "archivo",
#         "nombrearchivo": "archivo",
#         "nombre_archivo": "archivo"
#     }

#     df.columns = [equivalencias.get(col, col) for col in df.columns]

#     # Validar columnas
#     if "fecha" not in df.columns or "archivo" not in df.columns:
#         messagebox.showerror(
#             "Error",
#             f"El Excel debe tener columnas:\n- Fecha\n- Archivo\n\nColumnas detectadas:\n{df.columns.tolist()}"
#         )
#         return

#     copiados = 0
#     no_encontrados = []

#     for _, fila in df.iterrows():
#         fecha = fila["fecha"]
#         archivo = str(fila["archivo"]).strip()

#         try:
#             fecha_dt = pd.to_datetime(fecha)
#         except:
#             no_encontrados.append(archivo)
#             continue

#         mes = MESES[fecha_dt.month]

#         carpeta_mes = os.path.join(carpeta_destino, mes)
#         os.makedirs(carpeta_mes, exist_ok=True)

#         ruta_pdf = buscar_pdf(archivo, carpeta_busqueda)

#         if ruta_pdf:
#             shutil.copy(ruta_pdf, carpeta_mes)
#             copiados += 1
#         else:
#             no_encontrados.append(archivo)

#     mensaje = f"Archivos copiados: {copiados}\n"
#     if no_encontrados:
#         mensaje += "\nNo encontrados:\n" + "\n".join(no_encontrados)

#     messagebox.showinfo("Proceso completado", mensaje)


# if __name__ == "__main__":
#     procesar()

import os
import shutil
import pandas as pd
from tkinter import Tk, Frame, Button, Label, Text, END
from tkinter import ttk, filedialog, messagebox

# Meses en español
MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# Rutas seleccionadas
excel_path = ""
carpeta_origen = ""
carpeta_destino = ""


def seleccionar_excel():
    global excel_path
    p = filedialog.askopenfilename(title="Seleccionar archivo Excel", filetypes=[("Excel", "*.xlsx *.xls")])
    if p:
        excel_path = p
        lbl_excel.config(text=os.path.basename(excel_path))
    else:
        excel_path = ""
        lbl_excel.config(text="No seleccionado")


def seleccionar_origen():
    global carpeta_origen
    p = filedialog.askdirectory(title="Seleccionar carpeta ORIGEN (donde buscar PDFs)")
    if p:
        carpeta_origen = p
        lbl_origen.config(text=carpeta_origen)
    else:
        carpeta_origen = ""
        lbl_origen.config(text="No seleccionada")


def seleccionar_destino():
    global carpeta_destino
    p = filedialog.askdirectory(title="Seleccionar carpeta DESTINO (aquí se crearán MES/DIA)")
    if p:
        carpeta_destino = p
        lbl_destino.config(text=carpeta_destino)
    else:
        carpeta_destino = ""
        lbl_destino.config(text="No seleccionada")


def buscar_pdf_recursivo(nombre_pdf, base):
    """Busca un archivo por nombre en base recursivamente (case-insensitive)."""
    objetivo = nombre_pdf.lower().strip()
    for root, _, files in os.walk(base):
        for f in files:
            if f.lower().strip() == objetivo:
                return os.path.join(root, f)
    return None


def asegurar_nombre_unico(destino):
    """Si destino existe, devuelve un destino con sufijo (1), (2), ..."""
    if not os.path.exists(destino):
        return destino
    base, ext = os.path.splitext(destino)
    contador = 1
    while True:
        nuevo = f"{base} ({contador}){ext}"
        if not os.path.exists(nuevo):
            return nuevo
        contador += 1


def ejecutar():
    if not excel_path:
        messagebox.showerror("Error", "Selecciona el archivo Excel.")
        return
    if not carpeta_origen:
        messagebox.showerror("Error", "Selecciona la carpeta ORIGEN.")
        return
    if not carpeta_destino:
        messagebox.showerror("Error", "Selecciona la carpeta DESTINO.")
        return

    # Leer Excel
    try:
        df = pd.read_excel(excel_path, engine="openpyxl")
    except Exception as e:
        messagebox.showerror("Error", f"No pude leer el Excel:\n{e}")
        return

    # Normalizar encabezados
    df.columns = [str(c).strip().lower() for c in df.columns]
    # renombrar equivalentes si los hay
    rename_map = {"fechas": "fecha", "date": "fecha", "archivo": "archivo", "archivos": "archivo", "nombre_archivo": "archivo"}
    df.rename(columns=rename_map, inplace=True)

    if "fecha" not in df.columns or "archivo" not in df.columns:
        messagebox.showerror("Error", f"El Excel debe tener columnas 'Fecha' y 'Archivo'. Columnas detectadas: {df.columns.tolist()}")
        return

    # Convertir fecha y ordenar
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df["archivo"] = df["archivo"].astype(str).str.strip()
    df_valid = df[df["fecha"].notna() & (df["archivo"] != "")].copy()

    if df_valid.empty:
        messagebox.showwarning("Sin filas válidas", "No hay filas con fecha válida y nombre de archivo.")
        return

    df_valid.sort_values(by="fecha", inplace=True)

    total = len(df_valid)
    progreso["maximum"] = total
    progreso["value"] = 0
    txt_log.delete(1.0, END)

    copiados = 0
    no_encontrados = []

    for _, row in df_valid.iterrows():
        fecha = row["fecha"]
        archivo = str(row["archivo"]).strip()
        # Asegurar extensión
        if not archivo.lower().endswith(".pdf"):
            archivo = archivo + ".pdf"

        # Carpeta mes/dia
        mes_nombre = MESES.get(fecha.month, f"mes_{fecha.month}")
        dia = f"{fecha.day:02d}"
        carpeta_mes = os.path.join(carpeta_destino, mes_nombre)
        carpeta_dia = os.path.join(carpeta_mes, dia)
        os.makedirs(carpeta_dia, exist_ok=True)

        # Buscar PDF en origen recursivamente
        ruta_pdf = buscar_pdf_recursivo(archivo, carpeta_origen)
        if ruta_pdf:
            destino = os.path.join(carpeta_dia, archivo)
            destino_unico = asegurar_nombre_unico(destino)
            try:
                shutil.copy2(ruta_pdf, destino_unico)
                txt_log.insert(END, f"✔ Copiado: {archivo} → {mes_nombre}/{dia}\n")
                copiados += 1
            except Exception as e:
                txt_log.insert(END, f"❌ Error copiando {archivo}: {e}\n")
        else:
            txt_log.insert(END, f"⚠ No encontrado: {archivo}\n")
            no_encontrados.append(archivo)

        progreso["value"] += 1
        root.update_idletasks()

    resumen = f"Proceso terminado. Copiados: {copiados}. No encontrados: {len(no_encontrados)}"
    if no_encontrados:
        resumen += "\nNo encontrados:\n" + "\n".join(no_encontrados[:200])
    messagebox.showinfo("Finalizado", resumen)
    txt_log.insert(END, "\n" + resumen + "\n")


# ---------- Interfaz ----------
root = Tk()
root.title("Organizar PDFs por Fecha -> Estructura MES/DIA")
root.geometry("800x540")

frame = Frame(root)
frame.pack(pady=12, padx=12, anchor="w")

Button(frame, text="Seleccionar Excel", width=24, command=seleccionar_excel).grid(row=0, column=0, padx=6, pady=4)
lbl_excel = Label(frame, text="No seleccionado", width=80, anchor="w")
lbl_excel.grid(row=0, column=1, padx=6)

Button(frame, text="Seleccionar carpeta ORIGEN", width=24, command=seleccionar_origen).grid(row=1, column=0, padx=6, pady=4)
lbl_origen = Label(frame, text="No seleccionada", width=80, anchor="w")
lbl_origen.grid(row=1, column=1, padx=6)

Button(frame, text="Seleccionar carpeta DESTINO (se crearán MES/DIA)", width=48, command=seleccionar_destino).grid(row=2, column=0, padx=6, pady=4)
lbl_destino = Label(frame, text="No seleccionada", width=80, anchor="w")
lbl_destino.grid(row=2, column=1, padx=6)

Button(root, text="EJECUTAR", width=20, bg="#28a745", fg="white", command=ejecutar).pack(pady=10)

progreso = ttk.Progressbar(root, length=760, mode="determinate")
progreso.pack(pady=6)

txt_log = Text(root, height=20, width=100)
txt_log.pack(padx=8, pady=6)

root.mainloop()
