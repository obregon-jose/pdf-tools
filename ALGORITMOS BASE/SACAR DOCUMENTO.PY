import os
import re
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

def extraer_numero(nombre_archivo):
    """
    Extrae el número de documento del nombre del archivo.
    Se asume formato: NOMBRE_APELLIDO_NUMERODOCUMENTO.pdf
    """
    base = os.path.splitext(nombre_archivo)[0]
    partes = base.split("_")
    if len(partes) >= 3:
        return partes[-1]  # último elemento
    else:
        # Intentar detectar número con regex si el formato no es exacto
        match = re.search(r"(\d+)$", base)
        return match.group(1) if match else ""

def procesar_zip(archivo_zip):
    """
    Procesa un archivo .zip, extrayendo los archivos PDF y extrayendo el número de documento.
    """
    with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
        archivos_pdf = [f for f in zip_ref.namelist() if f.lower().endswith(".pdf")]
        
        datos = []
        for archivo in archivos_pdf:
            numero = extraer_numero(archivo)
            datos.append({"Archivo": archivo, "NumeroDocumento": numero})

        return pd.DataFrame(datos), len(archivos_pdf)

def procesar_carpeta_principal():
    carpeta_principal = filedialog.askdirectory(title="Selecciona la carpeta principal")
    if not carpeta_principal:
        return

    archivos_zip = [os.path.join(carpeta_principal, f) for f in os.listdir(carpeta_principal)
                    if f.lower().endswith(".zip")]

    if not archivos_zip:
        messagebox.showwarning("Sin archivos ZIP", "No se encontraron archivos ZIP en esta carpeta.")
        return

    # Crear archivo Excel en la carpeta principal
    nombre_archivo_excel = os.path.basename(carpeta_principal)
    ruta_excel = os.path.join(carpeta_principal, f"{nombre_archivo_excel}.xlsx")

    with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
        for archivo_zip in archivos_zip:
            nombre_hoja = os.path.basename(archivo_zip)[:31]  # Límite de Excel para nombre de hoja
            df, num_pdfs = procesar_zip(archivo_zip)
            if not df.empty:
                df.to_excel(writer, sheet_name=nombre_hoja, index=False)
                print(f"Procesado {archivo_zip}, con {num_pdfs} PDF(s).")

    messagebox.showinfo("Completado", f"Excel generado correctamente:\n{ruta_excel}")

# --- Interfaz Tkinter ---
root = tk.Tk()
root.title("Generar Excel desde archivos ZIP")

tk.Label(root, text="Generar Excel con información de PDFs en archivos ZIP").pack(pady=10)
tk.Button(root, text="Seleccionar carpeta principal", command=procesar_carpeta_principal).pack(pady=10)

root.mainloop()
