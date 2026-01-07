import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter
import os


class EliminarPaginasPDF:

    def __init__(self, root):
        self.root = root
        self.root.title("Eliminar páginas de PDF")
        self.root.geometry("420x500")
        self.root.resizable(False, False)

        self.pdf_path = None
        self.check_vars = []

        self.crear_interfaz()

    def crear_interfaz(self):
        tk.Button(
            self.root,
            text="Seleccionar PDF",
            command=self.seleccionar_pdf
        ).pack(pady=10)

        self.lbl_pdf = tk.Label(self.root, text="Ningún archivo seleccionado")
        self.lbl_pdf.pack()

        # Área scroll para los checkboxes
        self.frame_canvas = tk.Frame(self.root)
        self.frame_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.frame_canvas)
        self.scrollbar = ttk.Scrollbar(
            self.frame_canvas,
            orient="vertical",
            command=self.canvas.yview
        )

        self.frame_checks = tk.Frame(self.canvas)

        self.frame_checks.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.frame_checks, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        tk.Button(
            self.root,
            text="Eliminar páginas seleccionadas",
            command=self.eliminar_paginas,
            bg="#c0392b",
            fg="white"
        ).pack(pady=10)

    def seleccionar_pdf(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Archivos PDF", "*.pdf")]
        )

        if not ruta:
            return

        self.pdf_path = ruta
        self.lbl_pdf.config(text=os.path.basename(ruta))
        self.cargar_paginas()

    def cargar_paginas(self):
        # Limpiar checkboxes anteriores
        for widget in self.frame_checks.winfo_children():
            widget.destroy()

        self.check_vars.clear()

        reader = PdfReader(self.pdf_path)
        total = len(reader.pages)

        for i in range(total):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(
                self.frame_checks,
                text=f"Eliminar página {i + 1}",
                variable=var
            )
            chk.pack(anchor="w")
            self.check_vars.append(var)

    def eliminar_paginas(self):
        if not self.pdf_path:
            messagebox.showerror("Error", "Seleccione un PDF primero")
            return

        paginas_a_eliminar = [
            i for i, var in enumerate(self.check_vars) if var.get()
        ]

        if not paginas_a_eliminar:
            messagebox.showerror("Error", "No seleccionó ninguna página")
            return

        reader = PdfReader(self.pdf_path)

        if len(paginas_a_eliminar) == len(reader.pages):
            messagebox.showerror("Error", "No se pueden eliminar todas las páginas")
            return

        writer = PdfWriter()

        for i, pagina in enumerate(reader.pages):
            if i not in paginas_a_eliminar:
                writer.add_page(pagina)

        ruta_salida = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile="PDF_resultante.pdf"
        )

        if not ruta_salida:
            return

        with open(ruta_salida, "wb") as f:
            writer.write(f)

        messagebox.showinfo("Éxito", "PDF generado correctamente")


# --------- EJECUCIÓN ---------
if __name__ == "__main__":
    root = tk.Tk()
    app = EliminarPaginasPDF(root)
    root.mainloop()
