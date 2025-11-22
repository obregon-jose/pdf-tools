import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfMerger

# Lista global para almacenar (variable, archivo)
checkbox_items = []

def seleccionar_carpeta():
    carpeta = filedialog.askdirectory(title="Selecciona una carpeta con PDFs")
    if carpeta:
        entry_carpeta.delete(0, tk.END)
        entry_carpeta.insert(0, carpeta)
        listar_archivos(carpeta)

def listar_archivos(carpeta):
    # Limpiar checkboxes previos
    for widget in frame_checks.winfo_children():
        widget.destroy()

    checkbox_items.clear()

    # Crear un checkbox por cada PDF
    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(frame_checks, text=archivo, variable=var)
            chk.pack(anchor="w", padx=5, pady=2)

            checkbox_items.append((var, archivo))

def seleccionar_todos():
    for var, _ in checkbox_items:
        var.set(True)

def deseleccionar_todos():
    for var, _ in checkbox_items:
        var.set(False)

def unir_seleccionados():
    carpeta = entry_carpeta.get().strip()

    if not carpeta:
        messagebox.showwarning("Advertencia", "Selecciona una carpeta primero.")
        return

    # Filtrar PDFs marcados
    seleccionados = [archivo for var, archivo in checkbox_items if var.get()]

    if not seleccionados:
        messagebox.showwarning("Advertencia", "Marca al menos un archivo PDF.")
        return

    salida = filedialog.asksaveasfilename(
        title="Guardar PDF unido como",
        defaultextension=".pdf",
        filetypes=[("Archivo PDF", "*.pdf")]
    )

    if not salida:
        return

    try:
        merger = PdfMerger()

        for archivo in seleccionados:
            merger.append(os.path.join(carpeta, archivo))

        merger.write(salida)
        merger.close()

        messagebox.showinfo("Éxito", f"PDF unido creado:\n{salida}")

    except Exception as e:
        messagebox.showerror("Error", f"Error durante la unión:\n{str(e)}")


# ----------------------------
# INTERFAZ GRÁFICA
# ----------------------------
root = tk.Tk()
root.title("Unir PDFs con Checkboxes")
root.geometry("600x500")

style = ttk.Style()
style.theme_use("clam")

# --- Selección de carpeta ---
frame_top = ttk.Frame(root, padding=10)
frame_top.pack(fill="x")

ttk.Label(frame_top, text="Carpeta seleccionada:").pack(anchor="w")

entry_carpeta = ttk.Entry(frame_top, width=70)
entry_carpeta.pack(side="left", padx=5)

ttk.Button(frame_top, text="Buscar carpeta", command=seleccionar_carpeta).pack(side="left")

# --- Scroll para checkboxes ---
frame_scroll = ttk.Frame(root)
frame_scroll.pack(fill="both", expand=True, padx=10, pady=10)

canvas = tk.Canvas(frame_scroll)
scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

canvas.pack(side="left", fill="both", expand=True)
canvas.configure(yscrollcommand=scrollbar.set)

frame_checks = ttk.Frame(canvas)
canvas.create_window((0, 0), window=frame_checks, anchor="nw")

def actualizar_scroll(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

frame_checks.bind("<Configure>", actualizar_scroll)

# --- Botones inferiores ---
frame_buttons = ttk.Frame(root, padding=10)
frame_buttons.pack(fill="x")

ttk.Button(frame_buttons, text="Seleccionar todos", command=seleccionar_todos).pack(side="left", padx=10)
ttk.Button(frame_buttons, text="Deseleccionar todos", command=deseleccionar_todos).pack(side="left", padx=10)
ttk.Button(frame_buttons, text="Unir PDFs marcados", command=unir_seleccionados).pack(side="right", padx=10)

root.mainloop()
