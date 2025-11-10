import os
import re
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

def procesar_carpeta():
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta con los PDF")
    if not carpeta:
        return

    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(".pdf")]
    if not archivos:
        messagebox.showwarning("Sin PDFs", "No se encontraron archivos PDF en esta carpeta.")
        return

    datos = []
    for archivo in archivos:
        numero = extraer_numero(archivo)
        datos.append({"Archivo": archivo, "NumeroDocumento": numero})

    df = pd.DataFrame(datos)

    # Nombre del archivo Excel = nombre de la carpeta
    nombre_carpeta = os.path.basename(carpeta)
    archivo_salida = os.path.join(carpeta, f"{nombre_carpeta}.xlsx")

    # Guardar en Excel
    with pd.ExcelWriter(archivo_salida, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=nombre_carpeta[:31], index=False)  # Excel limita a 31 caracteres el nombre de hoja

    messagebox.showinfo("Proceso completado", f"Archivo Excel generado:\n{archivo_salida}")

# --- Interfaz sencilla ---
root = tk.Tk()
root.title("Extraer Números de Documento de PDFs")

tk.Label(root, text="Extraer números de documento desde nombres de PDF").pack(pady=10)
tk.Button(root, text="Seleccionar carpeta y generar Excel", command=procesar_carpeta).pack(pady=10)

root.mainloop()


##################3
import os
import re
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

def procesar_subcarpeta(ruta_subcarpeta):
    """
    Procesa una subcarpeta, devolviendo un DataFrame con los archivos PDF y sus números.
    """
    archivos = [f for f in os.listdir(ruta_subcarpeta) if f.lower().endswith(".pdf")]
    datos = []

    for archivo in archivos:
        numero = extraer_numero(archivo)
        datos.append({"Archivo": archivo, "NumeroDocumento": numero})

    return pd.DataFrame(datos)

def procesar_carpeta_principal():
    carpeta_principal = filedialog.askdirectory(title="Selecciona la carpeta principal")
    if not carpeta_principal:
        return

    subcarpetas = [os.path.join(carpeta_principal, d) for d in os.listdir(carpeta_principal)
                   if os.path.isdir(os.path.join(carpeta_principal, d))]

    if not subcarpetas:
        messagebox.showwarning("Sin subcarpetas", "No se encontraron subcarpetas en esta carpeta.")
        return

    # Crear archivo Excel en la carpeta principal
    nombre_archivo_excel = os.path.basename(carpeta_principal)
    ruta_excel = os.path.join(carpeta_principal, f"{nombre_archivo_excel}.xlsx")

    with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
        for subcarpeta in subcarpetas:
            nombre_hoja = os.path.basename(subcarpeta)[:31]  # Límite de Excel
            df = procesar_subcarpeta(subcarpeta)
            if not df.empty:
                df.to_excel(writer, sheet_name=nombre_hoja, index=False)

    messagebox.showinfo("Completado", f"Excel generado correctamente:\n{ruta_excel}")

# --- Interfaz Tkinter ---
root = tk.Tk()
root.title("Extraer números de documento desde PDFs")

tk.Label(root, text="Generar Excel con una hoja por subcarpeta").pack(pady=10)
tk.Button(root, text="Seleccionar carpeta principal", command=procesar_carpeta_principal).pack(pady=10)

root.mainloop()
