import os
import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import time  # Para agregar un retraso antes de eliminar el archivo


class PDFMultiplierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multiplicar Soportes PDF")
        self.root.geometry("700x600")  # Ajusté la altura de la ventana para un diseño más cómodo

        # Etiqueta y botón para seleccionar el archivo PDF
        self.label = tk.Label(self.root, text="Selecciona un archivo PDF", font=("Arial", 14))
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        self.select_button = tk.Button(self.root, text="Seleccionar PDF", command=self.select_pdf, font=("Arial", 12))
        self.select_button.grid(row=1, column=0, columnspan=2, pady=5)

        # Ruta del archivo seleccionado (campo editable)
        self.pdf_path_label = tk.Label(self.root, text="Ruta del PDF seleccionado: ", font=("Arial", 12))
        self.pdf_path_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        
        self.pdf_path_entry = tk.Entry(self.root, width=50, font=("Arial", 12))
        self.pdf_path_entry.grid(row=3, column=0, columnspan=2, padx=10, pady=5)
        self.pdf_path_entry.config(state='readonly')  # Solo lectura, pero editable si es necesario

        # Prefijo
        self.prefix_label = tk.Label(self.root, text="Prefijo (Ej: CRC_900895359_IPSP)", font=("Arial", 12))
        self.prefix_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        self.prefix_entry = tk.Entry(self.root, width=40, font=("Arial", 12))
        self.prefix_entry.insert(0, "CRC_900895359_IPSP")  # Prefijo por defecto
        self.prefix_entry.grid(row=4, column=1, padx=10, pady=5)

        # Número de Factura
        self.invoice_label = tk.Label(self.root, text="Número de Factura (Ej: 48886)", font=("Arial", 12))
        self.invoice_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")

        self.invoice_entry = tk.Entry(self.root, width=40, font=("Arial", 12))
        self.invoice_entry.grid(row=5, column=1, padx=10, pady=5)

        # Listado de Documentos
        self.document_label = tk.Label(self.root, text="Listado de Documentos (max. 10, separados por salto de línea)", font=("Arial", 12))
        self.document_label.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

        self.document_text = tk.Text(self.root, height=10, width=40, font=("Arial", 12))  # Ampliamos el espacio para los documentos
        self.document_text.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

        # Carpeta de salida
        self.output_label = tk.Label(self.root, text="Carpeta de salida:", font=("Arial", 12))
        self.output_label.grid(row=8, column=0, padx=10, pady=5, sticky="w")

        self.output_entry = tk.Entry(self.root, width=40, font=("Arial", 12))
        self.output_entry.grid(row=8, column=1, padx=10, pady=5)

        self.browse_button = tk.Button(self.root, text="Seleccionar Carpeta", command=self.select_output_folder, font=("Arial", 12))
        self.browse_button.grid(row=9, column=0, columnspan=2, pady=5)

        # Botón para generar los PDFs
        self.split_button = tk.Button(self.root, text="Generar Multiplicados", command=self.multiply_pdfs, font=("Arial", 12), state=tk.DISABLED)
        self.split_button.grid(row=10, column=0, columnspan=2, pady=20)

        # Botón de salida
        self.quit_button = tk.Button(self.root, text="Salir", command=self.root.quit, font=("Arial", 12))
        self.quit_button.grid(row=11, column=0, columnspan=2, pady=10)

        # Variable para el archivo PDF seleccionado
        self.pdf_path = None

    def select_pdf(self):
        # Abre el diálogo para seleccionar el archivo PDF
        self.pdf_path = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])

        if not self.pdf_path:
            return  # Si no seleccionó archivo, no hace nada

        # Mostrar la ruta del archivo seleccionado en el campo editable
        self.pdf_path_entry.config(state='normal')  # Permitir edición temporalmente para mostrar la ruta
        self.pdf_path_entry.delete(0, tk.END)  # Limpiar el campo antes de insertar
        self.pdf_path_entry.insert(0, self.pdf_path)
        self.pdf_path_entry.config(state='readonly')  # Volver a modo solo lectura

        # Activar el botón de generar
        self.split_button.config(state=tk.NORMAL)

    def select_output_folder(self):
        # Abre el diálogo para seleccionar la carpeta de salida
        folder = filedialog.askdirectory(title="Selecciona la carpeta de salida")

        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)  # Pone la ruta seleccionada en el campo de texto

    def multiply_pdfs(self):
        if not self.pdf_path:
            messagebox.showerror("Error", "No se ha seleccionado un archivo PDF.")
            return

        prefix = self.prefix_entry.get().strip()
        invoice_number = self.invoice_entry.get().strip()
        document_list = self.document_text.get("1.0", tk.END).strip().split('\n')  # Obtiene el texto separado por saltos de línea
        output_dir = self.output_entry.get().strip()

        # Validar que la entrada no esté vacía
        if not prefix or not document_list or not output_dir:
            messagebox.showerror("Error", "Por favor, completa todos los campos.")
            return

        # Verificar si la lista de documentos está vacía
        if not any(document_list):
            messagebox.showerror("Error", "No se ha ingresado ningún documento.")
            return

        # Limitar a 10 documentos
        if len(document_list) > 10:
            messagebox.showerror("Error", "El número máximo de documentos es 10.")
            return

        # Crear la carpeta de salida si no existe
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

            created_files = []
            for document in document_list:
                document = document.strip()

                # Generar el nombre del archivo de salida
                if invoice_number:
                    file_name = f"{prefix}{invoice_number}_{document}.pdf"  # Sin guion bajo entre prefijo y factura
                else:
                    file_name = f"{prefix}_{document}.pdf"  # Solo el prefijo y el documento
                
                file_path = os.path.join(output_dir, file_name)

                # Comprobar si el archivo ya existe y crear una versión numerada
                counter = 1
                while os.path.exists(file_path):
                    if invoice_number:
                        file_name = f"{prefix}{invoice_number}_{document} ({counter}).pdf"  # Sin guion bajo entre prefijo y factura
                    else:
                        file_name = f"{prefix}_{document} ({counter}).pdf"
                    file_path = os.path.join(output_dir, file_name)
                    counter += 1

                # Guardar el PDF multiplicado
                new_pdf = fitz.open()
                new_pdf.insert_pdf(doc)

                new_pdf.save(file_path)
                created_files.append(file_path)
                print(f"Archivo guardado en: {file_path}")

            # Cerrar el archivo PDF antes de eliminarlo
            doc.close()

            # Dar un pequeño retraso para asegurar que el archivo se haya liberado
            time.sleep(1)

            # Eliminar el archivo original
            os.remove(self.pdf_path)
            print(f"Archivo original eliminado: {self.pdf_path}")

            messagebox.showinfo("Éxito", f"Se han creado {len(created_files)} archivos PDF y el archivo original ha sido eliminado.")

        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error: {e}")
            print(f"Error: {e}")


# Inicializa la interfaz gráfica
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFMultiplierApp(root)
    root.mainloop()
