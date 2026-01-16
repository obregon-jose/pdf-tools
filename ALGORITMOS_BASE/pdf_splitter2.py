import os
import re
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import threading


# ==================== CONFIGURACIÓN ====================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ==================== UTILIDADES ====================

def parse_page_ranges(ranges: str, max_page: int) -> Optional[List[int]]:
    """
    Parsea un string de rangos como "1-3,5,7-9" a lista de índices 0-based.
    Retorna None si hay error o índices fuera de límites. 
    """
    if not ranges. strip():
        return list(range(max_page))
    
    page_nums = set()
    token_re = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$")
    
    for part in ranges.split(","):
        part = part.strip()
        if not part: 
            continue
        
        match = token_re.match(part)
        if not match: 
            return None
        
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        
        if start < 1 or end < start:
            return None
        
        for p in range(start - 1, end):
            if p < 0 or p >= max_page:
                return None
            page_nums.add(p)
    
    return sorted(page_nums)


def create_unique_path(path: Path) -> Path:
    """Crea una ruta única si el archivo ya existe."""
    if not path.exists():
        return path
    
    base = path.stem
    ext = path.suffix
    parent = path.parent
    counter = 1
    
    while True:
        new_path = parent / f"{base} ({counter}){ext}"
        if not new_path.exists():
            return new_path
        counter += 1


# ==================== LÓGICA DE DIVISIÓN ====================

def split_pdf_fitz(
    input_path:  Path,
    output_dir:  Path,
    ranges_text:  str,
    progress_callback=None,
    status_callback=None,
) -> Tuple[int, int, List[Path]]:
    """
    Divide el PDF usando fitz (PyMuPDF).
    Retorna:  (success_count, fail_count, created_files)
    """
    try:
        doc = fitz.open(str(input_path))
    except Exception as e:
        raise RuntimeError(f"No se pudo abrir el PDF: {e}")
    
    num_pages = doc.page_count
    page_indices = parse_page_ranges(ranges_text, num_pages)
    
    if page_indices is None: 
        doc.close()
        raise ValueError("Rangos inválidos o fuera de límites.")
    
    total = len(page_indices)
    success = 0
    fail = 0
    created_files:  List[Path] = []
    
    for i, page_idx in enumerate(page_indices, start=1):
        try:
            # Crear nuevo documento con una sola página
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
            
            # Generar nombre de salida
            out_name = f"{input_path.stem}_pagina_{page_idx + 1}.pdf"
            out_path = output_dir / out_name
            out_path = create_unique_path(out_path)
            
            # Guardar con compresión
            new_doc.save(str(out_path), garbage=4, deflate=True)
            new_doc.close()
            
            created_files.append(out_path)
            success += 1
            
        except Exception as e:
            print(f"[ERROR] Página {page_idx + 1}: {e}")
            fail += 1
        
        finally:
            if progress_callback: 
                progress_callback(i / total)
            if status_callback:
                status_callback(f"Procesadas {i}/{total}")
    
    doc.close()
    return success, fail, created_files


# ==================== APLICACIÓN PRINCIPAL ====================

class PDFSplitterApp2(ctk.CTkFrame):
    """
    Aplicación para dividir PDFs en páginas individuales. 
    Diseño basado en el modelo PDFSplitterApp.
    """
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # ===== ESTADO =====
        self.pdf_path:  Optional[str] = None
        self.last_operation: Optional[Dict] = None
        self.is_processing = False
        
        # ===== CONSTRUIR UI =====
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # ===== FRAME SUPERIOR =====
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: PDF de entrada
        lbl_pdf = ctk.CTkLabel(top_frame, text="PDF:", width=60, anchor="w")
        lbl_pdf.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.pdf_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Selecciona el archivo PDF a dividir",
            width=500
        )
        self.pdf_entry.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        self.pdf_entry.bind("<Return>", lambda e: self._load_pdf_info())
        
        btn_select_pdf = ctk.CTkButton(
            top_frame,
            text="Seleccionar PDF",
            width=140,
            command=self._on_select_pdf
        )
        btn_select_pdf.grid(row=0, column=2, padx=(0, 6), pady=4)
        
        # Fila 1: Info del PDF
        lbl_info_title = ctk.CTkLabel(top_frame, text="Info:", width=60, anchor="w")
        lbl_info_title.grid(row=1, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.info_label = ctk.CTkLabel(
            top_frame,
            text="Ningún archivo seleccionado",
            anchor="w",
            text_color="gray"
        )
        self.info_label. grid(row=1, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="w")
        
        # Fila 2: Carpeta de salida
        lbl_output = ctk.CTkLabel(top_frame, text="Salida:", width=60, anchor="w")
        lbl_output. grid(row=2, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self. output_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Carpeta de salida (opcional, usa la del PDF)",
            width=500
        )
        self.output_entry.grid(row=2, column=1, padx=(0, 6), pady=4, sticky="we")
        
        btn_select_output = ctk. CTkButton(
            top_frame,
            text="Seleccionar Carpeta",
            width=140,
            command=self._on_select_output
        )
        btn_select_output.grid(row=2, column=2, padx=(0, 6), pady=4)
        
        # Fila 3: Rangos de páginas
        lbl_ranges = ctk.CTkLabel(top_frame, text="Rangos:", width=60, anchor="w")
        lbl_ranges.grid(row=3, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.ranges_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Ej:  1-3,5,7-9 (vacío = todas las páginas)",
            width=500
        )
        self.ranges_entry.grid(row=3, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="we")
        
        # Fila 4: Espaciador
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=4, column=0, columnspan=3)
        
        # Fila 5: Botones de acción
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        
        self.split_button = ctk.CTkButton(
            btn_frame,
            text="✂️ Dividir PDF",
            command=self._on_split,
            fg_color="#1f6feb"
        )
        self.split_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self. undo_button = ctk.CTkButton(
            btn_frame,
            text="↶ Deshacer",
            command=self._on_undo,
            fg_color="#f0ad4e",
            text_color="black"
        )
        self.undo_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        self.undo_button.configure(state="disabled")
        
        self.clear_button = ctk.CTkButton(
            btn_frame,
            text="🧹 Limpiar",
            command=self._on_clear
        )
        self.clear_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE PROGRESO =====
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Nota informativa
        self.info_note = ctk.CTkLabel(
            self.progress_frame,
            text="Nota: Si dejas los rangos vacíos, se extraerán todas las páginas.  Usa formato 1-3,5,7-9 para rangos específicos.",
            text_color="gray",
            font=("Arial", 12, "bold")
        )
        self.info_note.pack(anchor="w", padx=4, pady=(2, 4))
        
        # Barra de progreso
        self. progressbar = ctk.CTkProgressBar(self.progress_frame, height=20)
        self.progressbar.pack(fill="x", padx=4, pady=(10, 4))
        self.progressbar.set(0)
        
        # Estado del proceso
        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="⏳ Esperando archivo...",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(anchor="w", padx=4, pady=(4, 10))
        
        # Área de resultados
        self.results_frame = ctk.CTkFrame(self. progress_frame, fg_color="gray20")
        self.results_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.results_label = ctk.CTkLabel(
            self.results_frame,
            text="Los archivos creados aparecerán aquí",
            text_color="gray",
            font=ctk. CTkFont(size=11)
        )
        self.results_label.pack(pady=20)
    
    # ==================== EVENTOS ====================
    
    def _on_select_pdf(self):
        """Selecciona el archivo PDF."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if file_path:
            self.pdf_path = file_path
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, file_path)
            
            # Auto-llenar carpeta de salida
            if not self.output_entry.get().strip():
                output_dir = os.path.dirname(file_path)
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, output_dir)
            
            self._load_pdf_info()
    
    def _load_pdf_info(self):
        """Carga información del PDF."""
        pdf_path = self.pdf_entry.get().strip()
        
        if not pdf_path or not os.path.exists(pdf_path):
            return
        
        try:
            doc = fitz.open(pdf_path)
            num_pages = doc.page_count
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)
            doc.close()
            
            self.info_label.configure(
                text=f"✓ {num_pages} páginas • {file_size:.2f} MB",
                text_color="#10b981"
            )
        except Exception as e:
            self.info_label.configure(
                text=f"❌ Error:  {e}",
                text_color="red"
            )
    
    def _on_select_output(self):
        """Selecciona la carpeta de salida."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_entry. delete(0, tk.END)
            self.output_entry. insert(0, folder)
    
    def _on_clear(self):
        """Limpia los campos."""
        self.ranges_entry.delete(0, tk.END)
        self.progressbar.set(0)
        self.status_label.configure(text="⏳ Esperando archivo.. .", text_color="gray")
        self.results_label.configure(text="Los archivos creados aparecerán aquí")
        messagebox.showinfo("Limpiar", "Se han limpiado los campos.")
    
    # ==================== OPERACIONES ====================
    
    def _on_split(self):
        """Inicia la división del PDF."""
        if self.is_processing:
            messagebox. showwarning("Procesando", "Ya hay una operación en curso.")
            return
        
        # Obtener rutas
        pdf_path = self.pdf_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        ranges_text = self.ranges_entry.get().strip()
        
        # Validaciones
        if not pdf_path: 
            messagebox.showerror("Error", "Selecciona un archivo PDF.")
            return
        
        if not os.path.exists(pdf_path):
            messagebox.showerror("Error", f"El archivo no existe:\n{pdf_path}")
            return
        
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox. showerror("Error", f"No se pudo crear la carpeta:\n{e}")
                return
        
        # Confirmar
        response = messagebox.askyesno(
            "Confirmar",
            f"¿Dividir el PDF?\n\n"
            f"Rangos: {ranges_text if ranges_text else 'Todas las páginas'}\n"
            f"Salida: {output_dir}"
        )
        
        if not response:
            return
        
        # Iniciar proceso en hilo separado
        self. is_processing = True
        self.split_button.configure(state="disabled")
        self.undo_button.configure(state="disabled")
        self.progressbar.set(0)
        self.status_label.configure(text="⏳ Iniciando.. .", text_color="orange")
        
        thread = threading.Thread(
            target=self._run_split,
            args=(Path(pdf_path), Path(output_dir), ranges_text),
            daemon=True
        )
        thread.start()
    
    def _run_split(self, input_path: Path, output_dir: Path, ranges_text: str):
        """Ejecuta la división en un hilo separado."""
        try:
            success, fail, created_files = split_pdf_fitz(
                input_path,
                output_dir,
                ranges_text,
                progress_callback=lambda v: self.after(0, lambda: self.progressbar.set(v)),
                status_callback=lambda t: self.after(0, lambda: self.status_label.configure(text=t))
            )
            
            # Guardar estado para deshacer
            self.last_operation = {
                'original_path': str(input_path),
                'created_files': [str(f) for f in created_files]
            }
            
            # Actualizar UI
            def update_ui():
                self.progressbar.set(1.0)
                self.status_label.configure(
                    text=f"✅ Completado.  Éxitos: {success}, Fallos:  {fail}",
                    text_color="green"
                )
                
                # Mostrar archivos creados
                if created_files:
                    files_text = "\n".join([f"📄 {f. name}" for f in created_files[: 10]])
                    if len(created_files) > 10:
                        files_text += f"\n... y {len(created_files) - 10} más"
                    self.results_label.configure(text=files_text)
                
                self. undo_button.configure(state="normal")
                messagebox.showinfo("Completado", f"Operación completada.\nÉxitos: {success}\nFallos: {fail}")
            
            self.after(0, update_ui)
            
        except Exception as e:
            def show_error():
                self.status_label.configure(text=f"❌ Error:  {e}", text_color="red")
                messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
            
            self. after(0, show_error)
        
        finally:
            self.is_processing = False
            self. after(0, lambda: self.split_button.configure(state="normal"))
    
    def _on_undo(self):
        """Deshace la última operación."""
        if not self.last_operation:
            messagebox.showinfo("Info", "No hay operación para deshacer.")
            return
        
        created_files = self.last_operation. get('created_files', [])
        
        if not created_files: 
            messagebox.showinfo("Info", "No hay archivos para eliminar.")
            self.last_operation = None
            self.undo_button.configure(state="disabled")
            return
        
        response = messagebox.askyesno(
            "Confirmar Deshacer",
            f"¿Eliminar {len(created_files)} archivos creados?"
        )
        
        if not response:
            return
        
        try:
            deleted_count = 0
            for file_path in created_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        print(f"[WARN] No se pudo eliminar {file_path}: {e}")
            
            messagebox.showinfo(
                "Deshacer completado",
                f"Se eliminaron {deleted_count} archivos."
            )
            
            self.last_operation = None
            self.undo_button.configure(state="disabled")
            self.results_label.configure(text="Los archivos creados aparecerán aquí")
            self.progressbar.set(0)
            self.status_label.configure(text="⏳ Esperando archivo...", text_color="gray")
            
        except Exception as e:
            messagebox. showerror("Error", f"No se pudo deshacer:\n{e}")
