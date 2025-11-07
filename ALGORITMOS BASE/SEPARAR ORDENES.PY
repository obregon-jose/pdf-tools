import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PyPDF2 import PdfReader, PdfWriter
import re

# --- Funciones auxiliares ---

def limpiar_nombre_archivo(nombre):
    return re.sub(r'[\\/*?:"<>|]', "", nombre)

def crear_carpeta_si_no_existe(ruta):
    if not os.path.exists(ruta):
        os.makedirs(ruta)

def obtener_nombre_unico(ruta_base):
    if not os.path.exists(ruta_base):
        return ruta_base
    base, ext = os.path.splitext(ruta_base)
    contador = 2
    nueva_ruta = f"{base} ({contador}){ext}"
    while os.path.exists(nueva_ruta):
        contador += 1
        nueva_ruta = f"{base} ({contador}){ext}"
    return nueva_ruta

# --- Función principal de procesamiento ---

def procesar():
    pdf_path = entrada_pdf.get()
    carpeta_salida = entrada_salida.get()
    prefijo = entrada_prefijo.get()
    texto_nombres = texto_nombres_area.get("1.0", tk.END)

    if not all([pdf_path, carpeta_salida, texto_nombres.strip()]):
        messagebox.showerror("Error", "Todos los campos son obligatorios.")
        return

    try:
        reader = PdfReader(pdf_path)
        num_paginas = len(reader.pages)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
        return

    nombres = [line.strip() for line in texto_nombres.strip().splitlines() if line.strip()]

    if len(nombres) != num_paginas:
        messagebox.showerror("Error", f"La cantidad de nombres ({len(nombres)}) no coincide con el número de páginas del PDF ({num_paginas}).")
        return

    crear_carpeta_si_no_existe(carpeta_salida)

    for i, nombre_doc in enumerate(nombres):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        nombre_limpio = limpiar_nombre_archivo(nombre_doc)
        nombre_archivo = f"{prefijo}{nombre_limpio}.pdf"
        ruta_salida = os.path.join(carpeta_salida, nombre_archivo)
        ruta_final = obtener_nombre_unico(ruta_salida)

        try:
            with open(ruta_final, "wb") as f_out:
                writer.write(f_out)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la página {i+1}: {e}")
            return

    messagebox.showinfo("Éxito", "Todas las páginas fueron guardadas correctamente.")

# --- Funciones para botones de exploración ---

def seleccionar_pdf():
    ruta = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if ruta:
        entrada_pdf.delete(0, tk.END)
        entrada_pdf.insert(0, ruta)

def seleccionar_carpeta():
    ruta = filedialog.askdirectory()
    if ruta:
        entrada_salida.delete(0, tk.END)
        entrada_salida.insert(0, ruta)

# --- Crear GUI ---

root = tk.Tk()
root.title("Dividir PDF y Renombrar Páginas")
root.geometry("700x500")
root.resizable(False, False)

# --- Elementos de la interfaz ---

tk.Label(root, text="Archivo PDF:").grid(row=0, column=0, sticky="e", padx=10, pady=10)
entrada_pdf = tk.Entry(root, width=60)
entrada_pdf.grid(row=0, column=1, padx=5)
tk.Button(root, text="Seleccionar", command=seleccionar_pdf).grid(row=0, column=2, padx=5)

tk.Label(root, text="Carpeta de salida:").grid(row=1, column=0, sticky="e", padx=10, pady=10)
entrada_salida = tk.Entry(root, width=60)
entrada_salida.grid(row=1, column=1, padx=5)
tk.Button(root, text="Seleccionar", command=seleccionar_carpeta).grid(row=1, column=2, padx=5)

tk.Label(root, text="Prefijo para archivos:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
entrada_prefijo = tk.Entry(root, width=30)
entrada_prefijo.insert(0, "OPF_900895359_IPSP_")
entrada_prefijo.grid(row=2, column=1, sticky="w", padx=5)

tk.Label(root, text="Nombres de documentos (uno por línea):").grid(row=3, column=0, columnspan=3, sticky="w", padx=10)

texto_nombres_area = scrolledtext.ScrolledText(root, width=80, height=12)
texto_nombres_area.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

tk.Button(root, text="Procesar PDF", command=procesar, bg="#4CAF50", fg="white", width=20, height=2).grid(row=5, column=1, pady=20)

root.mainloop()
