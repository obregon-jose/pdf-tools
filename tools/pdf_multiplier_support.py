import os
import re
import shutil
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict

MAX_NOMBRES = 10


class CTkTextboxWithPlaceholder(ctk.CTkTextbox):
    """CTkTextbox con soporte para placeholder text."""
    
    def __init__(self, master, placeholder_text="", placeholder_color="gray50", **kwargs):
        super().__init__(master, **kwargs)
        
        self.placeholder_text = placeholder_text
        self.placeholder_color = placeholder_color
        self.default_color = self._text_color
        self.is_placeholder_active = False
        
        self._show_placeholder()
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Key>", self._on_key_press)
    
    def _show_placeholder(self):
        self.delete("1.0", "end")
        self.insert("1.0", self.placeholder_text)
        self.configure(text_color=self.placeholder_color)
        self.is_placeholder_active = True
    
    def _hide_placeholder(self):
        if self.is_placeholder_active:
            self.delete("1.0", "end")
            self.configure(text_color=self.default_color)
            self.is_placeholder_active = False
    
    def _on_click(self, event=None):
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def _on_focus_in(self, event=None):
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def _on_focus_out(self, event=None):
        content = self.get("1.0", "end").strip()
        if not content:
            self._show_placeholder()
    
    def _on_key_press(self, event=None):
        if self.is_placeholder_active:
            self._hide_placeholder()
    
    def get_content(self) -> str:
        if self.is_placeholder_active:
            return ""
        return self.get("1.0", "end").strip()
    
    def clear(self):
        self.is_placeholder_active = False
        self.delete("1.0", "end")
        self._show_placeholder()


def clean_filename(name: str) -> str:
    """Elimina caracteres no permitidos en nombres de archivo."""
    return re.sub(r'[\\/*?:"<>|]', "", name)


class PDFMultiplierSupportApp(ctk.CTkFrame):
    """Aplicación para multiplicar un PDF con diferentes nombres."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        self.pdf_path: Optional[str] = None
        self.last_operation: Optional[Dict] = None
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_top_panel()
        self._build_main_panel()
        self._build_log_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # PDF de entrada
        ctk.CTkLabel(panel, text="PDF:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.pdf_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona el archivo PDF")
        self.pdf_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar PDF", width=130, command=self._on_select_pdf).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Carpeta de salida
        ctk.CTkLabel(panel, text="Salida:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=(6,4), pady=4, sticky="w")
        self.output_entry = ctk.CTkEntry(panel, placeholder_text="Carpeta de salida (opcional)")
        self.output_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(panel, text="Seleccionar", width=130, command=self._on_select_output).grid(row=1, column=2, padx=(4,6), pady=4)
        
        # Prefijo
        ctk.CTkLabel(panel, text="Prefijo:", width=60, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=(6,4), pady=4, sticky="w")
        self.prefix_entry = ctk.CTkEntry(panel)
        self.prefix_entry.grid(row=2, column=1, columnspan=2, padx=4, pady=4, sticky="ew")
        self.prefix_entry.insert(0, "CRC_900895359_IPSP_")
        
        # Botones de acción
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.process_btn = ctk.CTkButton(btn_frame, text="📄 Multiplicar PDF", command=self._on_process, fg_color="#1f6feb")
        self.process_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.undo_btn = ctk.CTkButton(btn_frame, text="↶ Deshacer", command=self._on_undo, fg_color="#f0ad4e", text_color="black", state="disabled")
        self.undo_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Limpiar", command=self._on_clear, fg_color="#e74c3c")
        self.clear_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    
    def _build_main_panel(self):
        """Panel principal con nombres."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Header con nombre de archivo y contador
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6,4))
        header.grid_columnconfigure(0, weight=1)
        
        self.file_name_lbl = ctk.CTkLabel(header, text="📄 Ningún archivo seleccionado", text_color="gray", anchor="w", font=ctk.CTkFont(size=12))
        self.file_name_lbl.grid(row=0, column=0, sticky="w")
        
        self.counter_lbl = ctk.CTkLabel(header, text=f"0 / {MAX_NOMBRES} nombres", text_color="gray", anchor="e")
        self.counter_lbl.grid(row=0, column=1, sticky="e", padx=(10,0))
        
        # Textbox de nombres
        placeholder = (
            f"Ingresa los nombres para duplicar el PDF (máximo {MAX_NOMBRES}):\n\n"
            "Ejemplo:\n"
            "CC1234567890\n"
            "TI0987654321\n"
            "RC1122334455"
        )
        
        self.names_textbox = CTkTextboxWithPlaceholder(
            panel,
            placeholder_text=placeholder,
            placeholder_color="gray50",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.names_textbox.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        self.names_textbox.bind("<KeyRelease>", self._update_counter)
    
    def _build_log_panel(self):
        """Panel de log/informe."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(panel, text="📋 Registro de operaciones", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=6, pady=(6,2))
        
        self.log_text = ctk.CTkTextbox(panel, height=100, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Listo para comenzar.")
    
    def _log(self, level: str, message: str):
        """Agrega un mensaje al log."""
        colors = {
            "INFO": "#7f8c8d",
            "OK": "#27ae60",
            "WARNING": "#f39c12",
            "ERROR": "#e74c3c"
        }
        
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{level}] {message}\n")
        
        # Aplicar color
        last_line = self.log_text.index("end-2l")
        self.log_text.tag_add(level, last_line, "end-1c")
        self.log_text.tag_config(level, foreground=colors.get(level, "white"))
        
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update()
    
    def _on_select_pdf(self):
        """Selecciona archivo PDF."""
        path = filedialog.askopenfilename(title="Seleccionar PDF", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        
        self.pdf_path = path
        self.pdf_entry.delete(0, "end")
        self.pdf_entry.insert(0, path)
        
        # Actualizar nombre de archivo en el header
        file_name = os.path.basename(path)
        self.file_name_lbl.configure(text=f"📄 {file_name}", text_color="white")
        
        if not self.output_entry.get().strip():
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, os.path.dirname(path))
        
        self._log("INFO", f"PDF seleccionado: {file_name}")
    
    def _on_select_output(self):
        """Selecciona carpeta de salida."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)
            self._log("INFO", f"Carpeta de salida: {folder}")
    
    def _on_clear(self):
        """Limpia el campo de nombres."""
        self.names_textbox.clear()
        self._update_counter()
        self._log("INFO", "Lista de nombres limpiada.")
    
    def _update_counter(self, event=None):
        """Actualiza el contador de nombres."""
        names = self._get_names_list()
        count = len(names)
        
        if count == 0:
            color, icon = "gray", ""
        elif count <= MAX_NOMBRES:
            color, icon = "green", "✓ "
        else:
            color, icon = "red", "❌ "
        
        self.counter_lbl.configure(text=f"{icon}{count} / {MAX_NOMBRES} nombres", text_color=color)
    
    def _get_names_list(self) -> List[str]:
        """Obtiene la lista de nombres."""
        text = self.names_textbox.get_content()
        if not text:
            return []
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def _on_process(self):
        """Procesa el PDF multiplicándolo."""
        pdf_path = self.pdf_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        prefix = self.prefix_entry.get().strip()
        names = self._get_names_list()
        
        # Validaciones
        if not pdf_path:
            messagebox.showerror("Error", "No se ha seleccionado un PDF.")
            self._log("ERROR", "No se ha seleccionado un PDF.")
            return
        
        if not os.path.exists(pdf_path):
            messagebox.showerror("Error", "El archivo PDF no existe.")
            self._log("ERROR", f"El archivo no existe: {pdf_path}")
            return
        
        if not names:
            messagebox.showerror("Error", "Debes ingresar al menos un nombre.")
            self._log("ERROR", "Debes ingresar al menos un nombre.")
            return
        
        if len(names) > MAX_NOMBRES:
            messagebox.showerror("Error", f"Máximo {MAX_NOMBRES} nombres permitidos. Tienes {len(names)}.")
            self._log("ERROR", f"Máximo {MAX_NOMBRES} nombres permitidos. Tienes {len(names)}.")
            return
        
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self._log("INFO", f"Carpeta creada: {output_dir}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la carpeta de salida: {e}")
                self._log("ERROR", f"No se pudo crear la carpeta: {e}")
                return
        
        # Procesar
        self._log("INFO", f"Iniciando multiplicación: {len(names)} copias con prefijo '{prefix}'")
        
        try:
            created_files = []
            
            for idx, name in enumerate(names, 1):
                clean_name = clean_filename(name)
                file_name = f"{prefix}{clean_name}.pdf"
                file_path = os.path.join(output_dir, file_name)
                
                # Evitar sobrescribir
                counter = 1
                while os.path.exists(file_path):
                    file_name = f"{prefix}{clean_name} ({counter}).pdf"
                    file_path = os.path.join(output_dir, file_name)
                    counter += 1
                
                # Copiar archivo
                shutil.copy(pdf_path, file_path)
                created_files.append(file_path)
                self._log("OK", f"[{idx}/{len(names)}] Creado: {file_name}")
            
            # Guardar estado para deshacer
            self.last_operation = {
                'original_path': pdf_path,
                'output_dir': output_dir,
                'created_files': created_files.copy()
            }
            
            # Eliminar el PDF original
            os.remove(pdf_path)
            self._log("WARNING", f"PDF original eliminado: {os.path.basename(pdf_path)}")
            
            self.undo_btn.configure(state="normal")
            self._log("OK", f"✅ Proceso completado: {len(created_files)} archivos creados.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el proceso: {e}")
            self._log("ERROR", f"Error durante el proceso: {e}")
    
    def _on_undo(self):
        """Deshace la última operación."""
        if not self.last_operation:
            self._log("WARNING", "No hay operación para deshacer.")
            return
        
        created_files = self.last_operation.get('created_files', [])
        original_path = self.last_operation.get('original_path')
        output_dir = self.last_operation.get('output_dir')
        
        if not created_files:
            self._log("WARNING", "No hay archivos para eliminar.")
            self.last_operation = None
            self.undo_btn.configure(state="disabled")
            return
        
        self._log("INFO", "Iniciando operación de deshacer...")
        
        try:
            # Restaurar el PDF original
            if created_files and os.path.exists(created_files[0]):
                first_copy = created_files[0]
                
                if os.path.dirname(original_path) != output_dir:
                    shutil.copy2(first_copy, original_path)
                else:
                    os.rename(first_copy, original_path)
                
                self._log("OK", f"PDF original restaurado: {os.path.basename(original_path)}")
                
                # Eliminar todas las copias
                deleted = 0
                for file_path in created_files:
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted += 1
                        except:
                            pass
                
                self._log("OK", f"Eliminadas {deleted} copias.")
                self._log("OK", "✅ Operación de deshacer completada.")
            
            self.last_operation = None
            self.undo_btn.configure(state="disabled")
            
            # Actualizar el campo del PDF
            self.pdf_entry.delete(0, "end")
            self.pdf_entry.insert(0, original_path)
            self.file_name_lbl.configure(text=f"📄 {os.path.basename(original_path)}", text_color="white")
            
        except Exception as e:
            self._log("ERROR", f"Error al deshacer: {e}")


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("PDF Multiplier")
    root.geometry("800x700")
    root.minsize(700, 600)
    app = PDFMultiplierSupportApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()