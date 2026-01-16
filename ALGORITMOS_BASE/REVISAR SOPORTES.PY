import os
import tkinter as tk
from tkinter import filedialog, messagebox

def extraer_identificador(nombre_archivo):
    """
    Extrae el identificador que aparece después del último guion bajo ("_")
    y antes de la extensión del archivo.
    Ejemplo: CRC_123_ABC_99999.pdf -> 99999
    """
    try:
        nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
        partes = nombre_sin_ext.split("_")
        if len(partes) < 2:
            return None
        return partes[-1].strip()  # Lo que está después del último "_"
    except:
        return None

def seleccionar_carpeta_crc():
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta de archivos CRC")
    if carpeta:
        entrada_crc.set(carpeta)

def seleccionar_carpeta_opf():
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta de archivos OPF")
    if carpeta:
        entrada_opf.set(carpeta)

def comparar_archivos():
    carpeta_crc = entrada_crc.get()
    carpeta_opf = entrada_opf.get()

    if not os.path.isdir(carpeta_crc) or not os.path.isdir(carpeta_opf):
        messagebox.showerror("Error", "Debes seleccionar ambas carpetas.")
        return

    # Obtener archivos que comiencen con CRC_ y OPF_
    archivos_crc = [f for f in os.listdir(carpeta_crc) if f.startswith("CRC_")]
    archivos_opf = [f for f in os.listdir(carpeta_opf) if f.startswith("OPF_")]

    # Extraer los identificadores
    identificadores_crc = set(filter(None, [extraer_identificador(f) for f in archivos_crc]))
    identificadores_opf = set(filter(None, [extraer_identificador(f) for f in archivos_opf]))

    # Comparar los conjuntos
    sin_pareja_crc = identificadores_crc - identificadores_opf
    sin_pareja_opf = identificadores_opf - identificadores_crc

    resultado = ""

    if sin_pareja_crc:
        resultado += f"🔴 CRC sin pareja OPF ({len(sin_pareja_crc)}):\n"
        resultado += "\n".join(sorted(sin_pareja_crc)) + "\n\n"

    if sin_pareja_opf:
        resultado += f"🔴 OPF sin pareja CRC ({len(sin_pareja_opf)}):\n"
        resultado += "\n".join(sorted(sin_pareja_opf)) + "\n\n"

    if not resultado:
        resultado = "✅ Todos los archivos tienen su pareja."

    text_resultado.delete("1.0", tk.END)
    text_resultado.insert(tk.END, resultado)

# GUI
root = tk.Tk()
root.title("Verificador de Parejas CRC y OPF")
root.geometry("600x400")

entrada_crc = tk.StringVar()
entrada_opf = tk.StringVar()

tk.Label(root, text="Carpeta CRC:").pack(anchor="w", padx=10, pady=(10, 0))
tk.Entry(root, textvariable=entrada_crc, width=60).pack(padx=10)
tk.Button(root, text="Seleccionar Carpeta CRC", command=seleccionar_carpeta_crc).pack(pady=5)

tk.Label(root, text="Carpeta OPF:").pack(anchor="w", padx=10, pady=(10, 0))
tk.Entry(root, textvariable=entrada_opf, width=60).pack(padx=10)
tk.Button(root, text="Seleccionar Carpeta OPF", command=seleccionar_carpeta_opf).pack(pady=5)

tk.Button(root, text="Comparar Archivos", command=comparar_archivos, bg="#4CAF50", fg="white").pack(pady=10)

text_resultado = tk.Text(root, wrap=tk.WORD, height=12)
text_resultado.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)

root.mainloop()
