import os
import re
import shutil
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# ==================== UTILIDADES ====================

def natural_key(s: str):
    """Clave para ordenamiento natural."""
    parts = re.split(r'(\d+)', s)
    return [int(p) if p.isdigit() else p for p in parts]


def create_unique_name(path: Path) -> Path:
    """Si la ruta existe, añade sufijo _1, _2..."""
    if not path.exists():
        return path
    base = path.stem
    ext = path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{base}_{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1


def extract_prefix(filename: str) -> str:
    """Extrae el prefijo antes del primer espacio o punto."""
    name_no_ext = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
    match = re.search(r'[.\s]', name_no_ext)
    if match:
        return name_no_ext[:match.start()]
    return name_no_ext


def get_groups_case_sensitive(folder: str) -> Dict[str, List[str]]:
    """Agrupa PDFs por prefijo. Solo grupos con más de 1 PDF."""
    temp: Dict[str, List[str]] = {}
    try:
        names = sorted(os.listdir(folder), key=natural_key)
    except Exception:
        names = os.listdir(folder)
    
    for name in names:
        if not name.lower().endswith(".pdf"):
            continue
        key = extract_prefix(name)
        temp.setdefault(key, []).append(name)
    
    groups = {k: v for k, v in temp.items() if len(v) > 1}
    return dict(sorted(groups.items(), key=lambda kv: natural_key(kv[0])))


# ==================== OPERACIONES PDF ====================

def move_files_to_group_folder(folder: Path, files: List[str], group_dir: Path) -> Tuple[List[Path], List[str]]:
    """Mueve los archivos a la carpeta de grupo."""
    moved_paths: List[Path] = []
    errors: List[str] = []
    group_dir.mkdir(parents=True, exist_ok=True)
    
    for name in files:
        src = folder / name
        if not src.exists():
            errors.append(f"No existe: {name}")
            continue
        dst = group_dir / name
        if dst.exists():
            dst = create_unique_name(dst)
        try:
            shutil.move(str(src), str(dst))
            moved_paths.append(dst)
        except Exception as e:
            errors.append(f"Error moviendo '{name}': {e}")
    
    return moved_paths, errors


def merge_pdfs_from_paths(paths: List[Path], output_path: Path) -> List[str]:
    """Une los PDFs usando fitz."""
    errors: List[str] = []
    paths_sorted = sorted(paths, key=lambda p: natural_key(p.name))
    
    try:
        merged_doc = fitz.open()
        
        for p in paths_sorted:
            try:
                src_doc = fitz.open(str(p))
                merged_doc.insert_pdf(src_doc)
                src_doc.close()
            except Exception as e:
                errors.append(f"Error añadiendo '{p.name}': {e}")
        
        if merged_doc.page_count == 0:
            merged_doc.close()
            errors.append("No se añadieron PDFs válidos.")
            return errors
        
        merged_doc.save(str(output_path), garbage=4, deflate=True)
        merged_doc.close()
        
    except Exception as e:
        errors.append(f"Error escribiendo '{output_path.name}': {e}")
    
    return errors


def merge_group_and_move(folder: str, key: str, files: List[str]) -> Tuple[bool, List[str], Optional[Path]]:
    """Une un grupo y mueve originales."""
    errors: List[str] = []
    folder_path = Path(folder)
    group_dir = folder_path / "Grupos"
    
    moved_paths, move_errors = move_files_to_group_folder(folder_path, files, group_dir)
    errors.extend(move_errors)
    
    if not moved_paths:
        return False, errors, None
    
    output = folder_path / f"{key}.pdf"
    output_unique = create_unique_name(output) if output.exists() else output
    
    merge_errors = merge_pdfs_from_paths(moved_paths, output_unique)
    errors.extend(merge_errors)
    
    success = len(move_errors) == 0 and len(merge_errors) == 0
    return success, errors, output_unique if success else None


def undo_merge(folder: str, key: str, output_file: Path) -> Tuple[bool, List[str]]:
    """Deshace la unión: elimina el PDF unido y restaura los originales."""
    errors: List[str] = []
    folder_path = Path(folder)
    group_dir = folder_path / "Grupos"
    
    # Eliminar PDF unido
    if output_file and output_file.exists():
        try:
            os.remove(output_file)
        except Exception as e:
            errors.append(f"No se pudo eliminar '{output_file.name}': {e}")
            return False, errors
    
    # Restaurar archivos desde carpeta Grupos
    if group_dir.exists():
        for file_path in group_dir.iterdir():
            if file_path.name.startswith(key) or extract_prefix(file_path.name) == key:
                dst = folder_path / file_path.name
                if dst.exists():
                    dst = create_unique_name(dst)
                try:
                    shutil.move(str(file_path), str(dst))
                except Exception as e:
                    errors.append(f"Error restaurando '{file_path.name}': {e}")
    
    return len(errors) == 0, errors


# ==================== COMPONENTE ACORDEÓN ====================

class AccordionItem(ctk.CTkFrame):
    """Item de acordeón para un grupo de PDFs."""
    
    def __init__(self, master, group_key: str, files: List[str], on_merge_callback):
        super().__init__(master, fg_color="#f3f3f3", corner_radius=8, border_width=2, border_color="#7b7b7b")
        
        self.group_key = group_key
        self.files = files
        self.on_merge_callback = on_merge_callback
        self.is_expanded = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=6)
        
        # Botón expandir
        self.toggle_btn = ctk.CTkButton(
            header,
            text="▶",
            width=30,
            height=30,
            command=self._toggle,
            fg_color="#2b2b2b",
            hover_color="#404040",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=6
        )
        self.toggle_btn.pack(side="left", padx=(0,10))
        
        # Info del grupo
        info = f"{self.group_key}  •  {len(self.files)} archivos"
        ctk.CTkLabel(
            header,
            text=info,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
        
        # Badge
        ctk.CTkLabel(
            header,
            text="✔️",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#10b981",
            width=28
        ).pack(side="left", padx=6)
        
        # Botón unir
        ctk.CTkButton(
            header,
            text="Unir",
            width=75,
            height=30,
            command=self._on_merge_click,
            fg_color="#1f6feb",
            hover_color="#1557c0",
            font=ctk.CTkFont(size=12),
            corner_radius=6
        ).pack(side="right", padx=2)
        
        # Panel expandible
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=4)
        
        for filename in self.files:
            ctk.CTkLabel(
                self.content,
                text=f"📄 {filename}",
                font=ctk.CTkFont(size=11),
                anchor="w",
                text_color="#5f5f5f"
            ).pack(anchor="w", padx=12, pady=1)
    
    def _toggle(self):
        if self.is_expanded:
            self.content.pack_forget()
            self.toggle_btn.configure(text="▶")
        else:
            self.content.pack(fill="x", padx=8, pady=(0,8))
            self.toggle_btn.configure(text="▼")
        self.is_expanded = not self.is_expanded
    
    def _on_merge_click(self):
        self.on_merge_callback(self.group_key, self.files)


# ==================== APLICACIÓN PRINCIPAL ====================

class PDFMergerGroupApp(ctk.CTkFrame):
    """Aplicación para unir PDFs agrupados por prefijo."""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        self.folder_path = ""
        self.groups: Dict[str, List[str]] = {}
        self.accordion_items: List[AccordionItem] = []
        self.last_operation: Optional[Dict] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_top_panel()
        self._build_groups_panel()
        self._build_log_panel()
    
    def _build_top_panel(self):
        """Panel superior con controles."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        panel.grid_columnconfigure(1, weight=1)
        
        # Carpeta
        ctk.CTkLabel(panel, text="Carpeta:", width=70, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(6,4), pady=4, sticky="w")
        self.folder_entry = ctk.CTkEntry(panel, placeholder_text="Selecciona carpeta con PDFs")
        self.folder_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.folder_entry.bind("<Return>", lambda e: self._load_from_entry())
        ctk.CTkButton(panel, text="Seleccionar", width=120, command=self._on_select_folder).grid(row=0, column=2, padx=(4,6), pady=4)
        
        # Botones de acción
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(4,6))
        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.merge_all_btn = ctk.CTkButton(btn_frame, text="📑 Unir Todos", command=self._on_merge_all, fg_color="#1f6feb")
        self.merge_all_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        
        self.undo_btn = ctk.CTkButton(btn_frame, text="↶ Deshacer", command=self._on_undo, fg_color="#f0ad4e", text_color="black", state="disabled")
        self.undo_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        self.refresh_btn = ctk.CTkButton(btn_frame, text="🔄 Refrescar", command=self._refresh, fg_color="#6c757d")
        self.refresh_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    
    def _build_groups_panel(self):
        """Panel de grupos."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6,4))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header,
            text="ℹ️ Grupos con prefijo común (texto antes de espacio/punto)",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=0, sticky="w")
        
        self.counter_lbl = ctk.CTkLabel(header, text="0 grupos", text_color="gray", anchor="e")
        self.counter_lbl.grid(row=0, column=1, sticky="e")
        
        # ScrollableFrame
        self.scroll_frame = ctk.CTkScrollableFrame(panel)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))
        
        self._show_empty_message()
    
    def _build_log_panel(self):
        """Panel de log."""
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0,6))
        panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(panel, text="📋 Registro", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=6, pady=(6,2))
        
        self.log_text = ctk.CTkTextbox(panel, height=90, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        self.log_text.configure(state="disabled")
        
        self._log("INFO", "Listo para comenzar.")
    
    def _log(self, level: str, message: str):
        """Agrega mensaje al log."""
        colors = {
            "INFO": "#7f8c8d",
            "SUCCESS": "#27ae60",
            "WARNING": "#f39c12",
            "ERROR": "#e74c3c"
        }
        
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{level}] {message}\n")
        
        last_line = self.log_text.index("end-2l")
        self.log_text.tag_add(level, last_line, "end-1c")
        self.log_text.tag_config(level, foreground=colors.get(level, "white"))
        
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update()
    
    def _show_empty_message(self, message="📂 Selecciona una carpeta para comenzar"):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.accordion_items.clear()
        
        ctk.CTkLabel(
            self.scroll_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(pady=40)
    
    def _on_select_folder(self):
        """Selecciona carpeta."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self._load_folder(folder)
    
    def _load_from_entry(self):
        """Carga carpeta desde entry."""
        path = self.folder_entry.get().strip()
        if path:
            self._load_folder(path)
    
    def _load_folder(self, folder: str):
        """Carga grupos de la carpeta."""
        if not os.path.exists(folder) or not os.path.isdir(folder):
            self._log("ERROR", "Carpeta no válida.")
            return
        
        self.folder_path = folder
        self._log("INFO", f"Carpeta seleccionada: {folder}")
        self._refresh()
    
    def _refresh(self):
        """Refresca la lista de grupos."""
        if not self.folder_path:
            self._log("WARNING", "Selecciona primero una carpeta.")
            return
        
        try:
            self.groups = get_groups_case_sensitive(self.folder_path)
            self._rebuild_accordion()
            
            count = len(self.groups)
            total_files = sum(len(files) for files in self.groups.values())
            self.counter_lbl.configure(text=f"{count} grupo(s), {total_files} archivos")
            self._log("INFO", f"Detectados {count} grupos con {total_files} archivos.")
            
        except Exception as e:
            self._log("ERROR", f"Error leyendo carpeta: {e}")
    
    def _rebuild_accordion(self):
        """Reconstruye el acordeón."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.accordion_items.clear()
        
        if not self.groups:
            self._show_empty_message("⚠️ No hay grupos con más de 1 PDF")
            return
        
        for key, files in self.groups.items():
            item = AccordionItem(self.scroll_frame, key, files, self._on_merge_group)
            item.pack(fill="x", padx=4, pady=4)
            self.accordion_items.append(item)
    
    def _on_merge_group(self, key: str, files: List[str]):
        """Une un grupo individual."""
        self._log("INFO", f"Iniciando unión del grupo '{key}' ({len(files)} archivos)...")
        
        success, errors, output_path = merge_group_and_move(self.folder_path, key, files)
        
        if success:
            self.last_operation = {'type': 'single', 'key': key, 'files': files.copy(), 'output': output_path}
            self.undo_btn.configure(state="normal")
            self._log("SUCCESS", f"✅ Grupo '{key}' unido → {output_path.name}")
        else:
            for error in errors[:3]:
                self._log("ERROR", error)
        
        self._refresh()
    
    def _on_merge_all(self):
        """Une todos los grupos."""
        if not self.groups:
            self._log("WARNING", "No hay grupos para unir.")
            return
        
        self._log("INFO", f"Uniendo {len(self.groups)} grupos...")
        
        merged_count = 0
        merged_outputs = []
        
        for key, files in self.groups.items():
            success, errors, output_path = merge_group_and_move(self.folder_path, key, files)
            if success:
                merged_count += 1
                merged_outputs.append({'key': key, 'files': files.copy(), 'output': output_path})
                self._log("SUCCESS", f"✅ Grupo '{key}' unido → {output_path.name}")
            else:
                for error in errors[:2]:
                    self._log("ERROR", f"Grupo '{key}': {error}")
        
        if merged_outputs:
            self.last_operation = {'type': 'all', 'merged': merged_outputs}
            self.undo_btn.configure(state="normal")
        
        self._refresh()
        self._log("SUCCESS", f"✅ Proceso completado: {merged_count}/{len(self.groups)} grupos unidos.")
    
    def _on_undo(self):
        """Deshace la última operación."""
        if not self.last_operation:
            self._log("WARNING", "No hay operación para deshacer.")
            return
        
        op_type = self.last_operation.get('type')
        
        if op_type == 'single':
            key = self.last_operation['key']
            output = self.last_operation['output']
            
            self._log("INFO", f"Deshaciendo unión del grupo '{key}'...")
            success, errors = undo_merge(self.folder_path, key, output)
            
            if success:
                self._log("SUCCESS", f"✅ Grupo '{key}' restaurado.")
            else:
                for error in errors:
                    self._log("ERROR", error)
        
        elif op_type == 'all':
            merged = self.last_operation.get('merged', [])
            self._log("INFO", f"Deshaciendo unión de {len(merged)} grupos...")
            
            restored = 0
            for item in merged:
                success, _ = undo_merge(self.folder_path, item['key'], item['output'])
                if success:
                    restored += 1
            
            self._log("SUCCESS", f"✅ Restaurados {restored}/{len(merged)} grupos.")
        
        self.last_operation = None
        self.undo_btn.configure(state="disabled")
        self._refresh()


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("PDF Merger - Unir por Grupos")
    root.geometry("850x750")
    root.minsize(750, 650)
    app = PDFMergerGroupApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()