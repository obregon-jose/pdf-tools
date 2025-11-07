import os
import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF

class PDFSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dividir PDF en Páginas")
        self.root.geometry("400x300")

        self.label = tk.Label(self.root, text="Selecciona un archivo PDF", font=("Arial", 14))
        self.label.pack(pady=10)

        self.select_button = tk.Button(self.root, text="Seleccionar PDF", command=self.select_pdf, font=("Arial", 12))
        self.select_button.pack(pady=10)

        self.output_label = tk.Label(self.root, text="Carpeta de salida:", font=("Arial", 12))
        self.output_label.pack(pady=5)

        self.output_entry = tk.Entry(self.root, width=35, font=("Arial", 12))
        self.output_entry.pack(pady=5)

        self.browse_button = tk.Button(self.root, text="Seleccionar Carpeta", command=self.select_output_folder, font=("Arial", 12))
        self.browse_button.pack(pady=10)

        self.split_button = tk.Button(self.root, text="Dividir PDF", command=self.split_pdf, font=("Arial", 12), state=tk.DISABLED)
        self.split_button.pack(pady=20)

        self.quit_button = tk.Button(self.root, text="Salir", command=self.root.quit, font=("Arial", 12))
        self.quit_button.pack(pady=10)

        self.pdf_path = None

    def select_pdf(self):
        # Abre el diálogo para seleccionar el archivo PDF
        self.pdf_path = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        
        if not self.pdf_path:
            return  # Si no seleccionó archivo, no hace nada

        # Activar el botón de dividir PDF
        self.split_button.config(state=tk.NORMAL)

    def select_output_folder(self):
        # Abre el diálogo para seleccionar la carpeta de salida
        folder = filedialog.askdirectory(title="Selecciona la carpeta de salida")

        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)  # Pone la ruta seleccionada en el campo de texto

    def split_pdf(self):
        if not self.pdf_path:
            messagebox.showerror("Error", "No se ha seleccionado un archivo PDF.")
            return

        output_dir = self.output_entry.get().strip()

        if not output_dir:
            messagebox.showerror("Error", "Por favor, selecciona o escribe una carpeta de salida.")
            return

        # Si la carpeta no existe, la creamos
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(f"Carpeta creada en: {output_dir}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la carpeta: {e}")
                return

        try:
            doc = fitz.open(self.pdf_path)
            num_pages = doc.page_count
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]

            # Guardar cada página como un archivo PDF individual
            created_files = []
            for i in range(num_pages):
                page = doc.load_page(i)  # Cargar la página i
                new_pdf = fitz.open()  # Crear un nuevo documento PDF vacío
                new_pdf.insert_pdf(doc, from_page=i, to_page=i)

                out_filename = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
                new_pdf.save(out_filename)
                created_files.append(out_filename)
                print(f"Página {i+1}/{num_pages} escrita en: {out_filename}")

            # Intentar eliminar el archivo original solo después de que todas las páginas hayan sido creadas
            os.remove(self.pdf_path)
            print(f"Archivo original eliminado: {self.pdf_path}")

            messagebox.showinfo("Éxito", f"Se han creado {num_pages} archivos PDF y el original ha sido eliminado.")
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error: {e}")
            print(f"Error: {e}")

# Inicializa la interfaz gráfica
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSplitterApp(root)
    root.mainloop()
