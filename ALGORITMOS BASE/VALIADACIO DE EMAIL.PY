import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import dns.resolver
import pandas as pd
import re
import unicodedata
import os

# ---------- Validadores -------------------

def normalizar_texto(texto):
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

def es_correo_valido(correo):
    correo = correo.strip()
    correo = normalizar_texto(correo)
    if not correo or any(ord(c) > 127 for c in correo):
        return False
    patron = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return patron.fullmatch(correo) is not None

def dominio_es_valido(dominio):
    try:
        dns.resolver.resolve(dominio, 'MX', lifetime=5)
        return True
    except Exception:
        return False

def encontrar_columna_correo(columnas):
    posibles_nombres = ['correo', 'email', 'e-mail', 'mail', 'correo electrónico']
    columnas_lower = [col.lower() for col in columnas]
    for nombre in posibles_nombres:
        if nombre in columnas_lower:
            return columnas[columnas_lower.index(nombre)]
    return None

# ---------- Lógica de Validación ----------

ruta_archivo = None  # Global para recordar el último archivo cargado

def procesar_archivo_excel(path):
    resultado_text.config(state="normal")
    resultado_text.delete(1.0, tk.END)
    estado_label.config(text="⏳ Procesando...")

    ventana.update_idletasks()

    try:
        df = pd.read_excel(path)
    except Exception as e:
        resultado_text.insert(tk.END, f"❌ Error al leer el archivo: {str(e)}\n")
        resultado_text.config(state="disabled")
        estado_label.config(text="⚠️ Error al leer el archivo")
        return

    columna_correo = encontrar_columna_correo(df.columns)
    if not columna_correo:
        resultado_text.insert(tk.END, "❌ No se encontró una columna de correos.\n")
        resultado_text.config(state="disabled")
        estado_label.config(text="⚠️ Columna de correos no encontrada")
        return

    errores = 0
    resultado_text.insert(tk.END, f"📄 Archivo: {os.path.basename(path)}\n")
    resultado_text.insert(tk.END, "🔍 Validando correos...\n\n")

    for idx, correo in enumerate(df[columna_correo], start=2):
        if pd.isna(correo):
            continue

        correo = str(correo).strip()

        if '@' not in correo:
            resultado_text.insert(tk.END, f"Fila {idx}: '{correo}' ❌ Falta el carácter '@'\n")
            errores += 1
            continue

        usuario = correo.split('@')[0]

        # Validar caracteres especiales en el usuario (antes de normalizar)
        if any(ord(c) > 127 for c in usuario):
            resultado_text.insert(tk.END, f"Fila {idx}: '{correo}' ❌❌ Usuario contiene acentos o caracteres no permitidos\n")
            errores += 1
            continue

        correo_limpio = normalizar_texto(correo)

        if not es_correo_valido(correo_limpio):
            resultado_text.insert(tk.END, f"Fila {idx}: '{correo}' ❌- Formato inválido\n")
            errores += 1
            continue

        dominio = correo_limpio.split('@')[1]
        if not dominio_es_valido(dominio):
            resultado_text.insert(tk.END, f"Fila {idx}: '{correo}' ❌ Dominio inválido ({dominio})\n")
            errores += 1

    if errores == 0:
        resultado_text.insert(tk.END, "\n✅ Todos los correos tienen formato y dominio válido.\n")
        estado_label.config(text="✅ Validación completada sin errores")
    else:
        resultado_text.insert(tk.END, f"\n⚠️ Total de errores encontrados: {errores}\n")
        estado_label.config(text=f"⚠️ {errores} errores encontrados")

    resultado_text.config(state="disabled")

# --------- Funciones de Botones -----------

def cargar_excel():
    global ruta_archivo
    archivo = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx *.xls")])
    if archivo:
        ruta_archivo = archivo
        procesar_archivo_excel(ruta_archivo)

def revisar_mismo_archivo():
    if ruta_archivo:
        if not os.path.exists(ruta_archivo):
            messagebox.showerror("Archivo no encontrado", "El archivo original ya no existe.")
            return
        procesar_archivo_excel(ruta_archivo)
    else:
        messagebox.showinfo("Sin archivo", "Primero debes cargar un archivo Excel.")



# --------- Interfaz Gráfica --------------

ventana = tk.Tk()
ventana.title("Verificador de correos desde Excel")
ventana.geometry("800x640")
ventana.configure(bg="#f4f4f4")

tk.Label(ventana, text="📄 Selecciona o revisa un archivo Excel con columna de correos", font=("Arial", 13, "bold"), bg="#f4f4f4").pack(pady=15)

frame_botones = tk.Frame(ventana, bg="#f4f4f4")
frame_botones.pack()

tk.Button(frame_botones, text="📂 Cargar Excel", command=cargar_excel, font=("Arial", 12), bg="#2196F3", fg="white", width=18).pack(side=tk.LEFT, padx=10)
tk.Button(frame_botones, text="🔁 Revisar Mismo Archivo", command=revisar_mismo_archivo, font=("Arial", 12), bg="#FFC107", fg="black", width=20).pack(side=tk.LEFT, padx=10)

resultado_text = scrolledtext.ScrolledText(ventana, width=95, height=24, font=("Courier", 10))
resultado_text.pack(padx=20, pady=10)
resultado_text.config(state="disabled")

estado_label = tk.Label(ventana, text="🕒 Esperando archivo...", font=("Arial", 11), bg="#f4f4f4", fg="gray")
estado_label.pack(pady=5)

ventana.mainloop()

