import customtkinter as ctk
from tkinter import filedialog, messagebox
import fitz
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class RotadorPDF(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Rotar PDF")
        self.geometry("420x260")
        self.resizable(False, False)

        self.archivo_pdf = ""

        # ---- Widgets ----
        self.label = ctk.CTkLabel(self, text="Rotar todas las páginas de un PDF", font=("Arial", 16))
        self.label.pack(pady=15)

        self.btn_seleccionar = ctk.CTkButton(
            self, text="Seleccionar PDF", command=self.seleccionar_pdf
        )
        self.btn_seleccionar.pack(pady=10)

        self.lbl_archivo = ctk.CTkLabel(self, text="Ningún archivo seleccionado")
        self.lbl_archivo.pack(pady=5)

        self.combo_grados = ctk.CTkComboBox(
            self, values=["90", "180", "270"]
        )
        self.combo_grados.set("90")
        self.combo_grados.pack(pady=10)

        self.btn_rotar = ctk.CTkButton(
            self, text="Rotar PDF", command=self.rotar_pdf
        )
        self.btn_rotar.pack(pady=15)

    # ---- Funciones ----
    def seleccionar_pdf(self):
        archivo = filedialog.askopenfilename(
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            self.archivo_pdf = archivo
            self.lbl_archivo.configure(text=os.path.basename(archivo))

    def rotar_pdf(self):
        if not self.archivo_pdf:
            messagebox.showerror("Error", "Seleccione un archivo PDF")
            return

        grados = int(self.combo_grados.get())

        try:
            doc = fitz.open(self.archivo_pdf)

            for page in doc:
                page.set_rotation(grados)

            salida = self.archivo_pdf.replace(".pdf", f"_rotado_{grados}.pdf")
            doc.save(salida)
            doc.close()

            messagebox.showinfo("Éxito", f"PDF rotado correctamente:\n{salida}")

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = RotadorPDF()
    app.mainloop()
import customtkinter as ctk
from tkinter import filedialog, messagebox
import fitz
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class RotadorPDF(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Rotar PDF")
        self.geometry("420x260")
        self.resizable(False, False)

        self.archivo_pdf = ""

        # ---- Widgets ----
        self.label = ctk.CTkLabel(self, text="Rotar todas las páginas de un PDF", font=("Arial", 16))
        self.label.pack(pady=15)

        self.btn_seleccionar = ctk.CTkButton(
            self, text="Seleccionar PDF", command=self.seleccionar_pdf
        )
        self.btn_seleccionar.pack(pady=10)

        self.lbl_archivo = ctk.CTkLabel(self, text="Ningún archivo seleccionado")
        self.lbl_archivo.pack(pady=5)

        self.combo_grados = ctk.CTkComboBox(
            self, values=["90", "180", "270"]
        )
        self.combo_grados.set("90")
        self.combo_grados.pack(pady=10)

        self.btn_rotar = ctk.CTkButton(
            self, text="Rotar PDF", command=self.rotar_pdf
        )
        self.btn_rotar.pack(pady=15)

    # ---- Funciones ----
    def seleccionar_pdf(self):
        archivo = filedialog.askopenfilename(
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            self.archivo_pdf = archivo
            self.lbl_archivo.configure(text=os.path.basename(archivo))

    def rotar_pdf(self):
        if not self.archivo_pdf:
            messagebox.showerror("Error", "Seleccione un archivo PDF")
            return

        grados = int(self.combo_grados.get())

        try:
            doc = fitz.open(self.archivo_pdf)

            for page in doc:
                page.set_rotation(grados)

            salida = self.archivo_pdf.replace(".pdf", f"_rotado_{grados}.pdf")
            doc.save(salida)
            doc.close()

            messagebox.showinfo("Éxito", f"PDF rotado correctamente:\n{salida}")

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = RotadorPDF()
    app.mainloop()
