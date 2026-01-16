import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import fitz
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ContadorPDFTabla(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Contador de páginas PDF")
        self.geometry("780x560")
        self.resizable(False, False)

        # ---- Título ----
        ctk.CTkLabel(
            self,
            text="Contador de PDFs (total incluido)",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        # ---- Botón carpeta ----
        ctk.CTkButton(
            self,
            text="Seleccionar carpeta",
            command=self.seleccionar_carpeta
        ).pack(pady=10)

        # ---- Label carpeta ----
        self.lbl_carpeta = ctk.CTkLabel(self, text="Ninguna carpeta seleccionada")
        self.lbl_carpeta.pack(pady=5)

        # ---- Frame tabla ----
        frame_tabla = ctk.CTkFrame(self)
        frame_tabla.pack(pady=10, fill="both", expand=True)

        # ---- Tabla ----
        self.tabla = ttk.Treeview(
            frame_tabla,
            columns=("archivo", "paginas"),
            show="headings",
            height=13
        )

        self.tabla.heading("archivo", text="Archivo PDF")
        self.tabla.heading("paginas", text="Páginas")

        self.tabla.column("archivo", width=520, anchor="w")
        self.tabla.column("paginas", width=100, anchor="center")

        self.tabla.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # ---- Campo copiar ----
        ctk.CTkLabel(
            self,
            text="Nombre del archivo (doble clic para copiar):",
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 5))

        self.entry_copiar = ctk.CTkEntry(self, width=700)
        self.entry_copiar.pack(pady=5)

        # ---- Total (label) ----
        self.lbl_total = ctk.CTkLabel(
            self, text="Total de páginas: 0", font=("Arial", 14, "bold")
        )
        self.lbl_total.pack(pady=10)

        # ---- Eventos ----
        self.tabla.bind("<Double-1>", self.enviar_a_entry)

    # ---------------- FUNCIONES ----------------

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if not carpeta:
            return

        self.lbl_carpeta.configure(text=carpeta)
        self.cargar_tabla(carpeta)

    def cargar_tabla(self, carpeta):
        # Limpiar tabla
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        total = 0
        archivos = sorted(f for f in os.listdir(carpeta) if f.lower().endswith(".pdf"))

        if not archivos:
            messagebox.showinfo("Info", "No hay PDFs en la carpeta")
            self.lbl_total.configure(text="Total de páginas: 0")
            return

        # Archivos
        for archivo in archivos:
            ruta = os.path.join(carpeta, archivo)
            try:
                with fitz.open(ruta) as doc:
                    paginas = doc.page_count

                total += paginas
                self.tabla.insert("", "end", values=(archivo, paginas))

            except Exception:
                self.tabla.insert("", "end", values=(archivo, "ERROR"))

        # ---- Fila TOTAL ----
        self.tabla.insert(
            "", "end",
            values=("TOTAL", total),
            tags=("total",)
        )

        self.tabla.tag_configure(
            "total",
            font=("Arial", 11, "bold")
        )

        self.lbl_total.configure(text=f"Total de páginas: {total}")

    def enviar_a_entry(self, event):
        item = self.tabla.selection()
        if not item:
            return

        valores = self.tabla.item(item, "values")
        if valores[0] == "TOTAL":
            return

        self.entry_copiar.delete(0, "end")
        self.entry_copiar.insert(0, valores[0])
        self.entry_copiar.focus()
        self.entry_copiar.select_range(0, "end")


if __name__ == "__main__":
    app = ContadorPDFTabla()
    app.mainloop()
