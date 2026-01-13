
import os
import re
import shutil
import fitz  # PyMuPDF
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# ==================== UTILIDADES ====================

def natural_key(s: str):
    """Clave para ordenamiento natural."""
    parts = re.split(r'(\d+)', s)
    return [int(p) if p.isdigit() else p for p in parts]


def create_unique_name(path: Path) -> Path:
    """Si la ruta existe, añade sufijo _1, _2.. ."""
    if not path.exists():
        return path
    base = path.stem
    ext = path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{base}_{i}{ext}"
        if not candidate. exists():
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
    """Agrupa PDFs por prefijo.  Solo grupos con más de 1 PDF."""
    temp:  Dict[str, List[str]] = {}
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
    moved_paths:  List[Path] = []
    errors: List[str] = []
    group_dir.mkdir(parents=True, exist_ok=True)
    
    for name in files:
        src = folder / name
        if not src.exists():
            errors. append(f"No existe: {name}")
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
    paths_sorted = sorted(paths, key=lambda p: natural_key(p. name))
    
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
        errors.append(f"Error escribiendo '{output_path. name}': {e}")
    
    return errors


def merge_group_and_move(folder:  str, key: str, files: List[str]) -> Tuple[bool, List[str], Optional[Path]]:
    """
    Une un grupo y mueve originales. 
    Retorna (success, errors, output_path)
    """
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
    """
    Deshace la unión:  elimina el PDF unido y restaura los originales.
    """
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
                dst = folder_path / file_path. name
                if dst.exists():
                    dst = create_unique_name(dst)
                try:
                    shutil.move(str(file_path), str(dst))
                except Exception as e:
                    errors.append(f"Error restaurando '{file_path.name}': {e}")
    
    return len(errors) == 0, errors


# ==================== COMPONENTE ACORDEÓN COMPACTO ====================

class AccordionItem(ctk.CTkFrame):
    """Item de acordeón compacto para un grupo de PDFs."""
    
    def __init__(self, master, group_key: str, files:  List[str], on_merge_callback):
        super().__init__(master, fg_color="gray20", corner_radius=6, height=36)
        
        self.group_key = group_key
        self.files = files
        self.on_merge_callback = on_merge_callback
        self.is_expanded = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Header compacto (una sola línea)
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header_frame.pack(fill="x", padx=4, pady=3)
        header_frame.pack_propagate(False)
        
        # Botón expandir
        self.toggle_button = ctk.CTkButton(
            header_frame,
            text="+",
            width=24,
            height=24,
            command=self._toggle,
            fg_color="gray30",
            hover_color="gray40",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.toggle_button.pack(side="left", padx=(0, 6))
        
        # Info del grupo (en línea)
        info_text = f"{self.group_key}  •  {len(self.files)} archivos"
        info_label = ctk.CTkLabel(
            header_frame,
            text=info_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        info_label.pack(side="left", fill="x", expand=True)
        
        # Badge compacto
        badge_label = ctk.CTkLabel(
            header_frame,
            text="✓",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#10b981",
            width=20
        )
        badge_label.pack(side="left", padx=4)
        
        # Botón unir compacto
        merge_button = ctk.CTkButton(
            header_frame,
            text="Unir",
            width=60,
            height=24,
            command=self._on_merge_click,
            fg_color="#1f6feb",
            font=ctk.CTkFont(size=11)
        )
        merge_button.pack(side="right", padx=2)
        
        # Panel expandible (oculto)
        self.content_frame = ctk.CTkFrame(self, fg_color="gray25", corner_radius=4)
        
        for filename in self.files:
            file_label = ctk.CTkLabel(
                self.content_frame,
                text=f"📄 {filename}",
                font=ctk.CTkFont(size=10),
                anchor="w"
            )
            file_label.pack(anchor="w", padx=8, pady=1)
    
    def _toggle(self):
        if self.is_expanded:
            self.content_frame.pack_forget()
            self.toggle_button.configure(text="+")
        else:
            self. content_frame.pack(fill="x", padx=4, pady=(0, 3))
            self.toggle_button.configure(text="−")
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
        self.last_operation:  Optional[Dict] = None  # Para deshacer
        
        self._create_widgets()
    
    def _create_widgets(self):
        # ===== FRAME SUPERIOR =====
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=6, pady=6)
        
        # Fila 0: Carpeta
        lbl_folder = ctk.CTkLabel(top_frame, text="Carpeta:", width=60, anchor="w")
        lbl_folder.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.folder_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Selecciona una carpeta con PDFs",
            width=500
        )
        self.folder_entry. grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        self.folder_entry.bind("<Return>", lambda e: self._load_from_entry())
        
        btn_select = ctk.CTkButton(
            top_frame,
            text="Seleccionar Carpeta",
            width=140,
            command=self._on_select_folder
        )
        btn_select.grid(row=0, column=2, padx=(0, 6), pady=4)
        
        # Fila 1: Espaciador
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=1, column=0, columnspan=3)
        
        # Fila 2: Botones de acción
        btn_frame = ctk.CTkFrame(top_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 4))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        btn_frame.grid_columnconfigure(3, weight=1)
        
        self.merge_all_button = ctk.CTkButton(
            btn_frame,
            text="📑 Unir todos",
            command=self._on_merge_all,
            fg_color="#1f6feb"
        )
        self.merge_all_button.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self. undo_button = ctk.CTkButton(
            btn_frame,
            text="↶ Deshacer",
            command=self._on_undo,
            fg_color="#f0ad4e",
            text_color="black"
        )
        self.undo_button.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        self.undo_button.configure(state="disabled")
        
        self.refresh_button = ctk.CTkButton(
            btn_frame,
            text="🔄 Refrescar",
            command=self._refresh
        )
        self.refresh_button.grid(row=0, column=2, padx=6, pady=4, sticky="we")
        
        self.expand_all_button = ctk.CTkButton(
            btn_frame,
            text="↕ Expandir/Colapsar",
            command=self._toggle_all
        )
        self.expand_all_button.grid(row=0, column=3, padx=6, pady=4, sticky="we")
        
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== PANEL DE GRUPOS =====
        self.groups_frame = ctk.CTkFrame(self)
        self.groups_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Nota y contador en línea
        header_frame = ctk.CTkFrame(self.groups_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=4, pady=(2, 4))
        
        self.info_note = ctk.CTkLabel(
            header_frame,
            text="Nota: Solo grupos con más de 1 PDF.  Prefijo = texto antes del primer espacio o punto.",
            text_color="gray",
            font=("Arial", 11, "bold")
        )
        self.info_note.pack(side="left")
        
        self.counter_label = ctk.CTkLabel(
            header_frame,
            text="0 grupos",
            text_color="gray"
        )
        self.counter_label.pack(side="right")
        
        # ScrollableFrame
        self.scroll_frame = ctk.CTkScrollableFrame(self.groups_frame, height=400)
        self.scroll_frame.pack(fill="both", expand=True, padx=4, pady=2)
        
        self._show_empty_message()
    
    # ==================== MENSAJES ====================
    
    def _show_empty_message(self, message="📂 Selecciona una carpeta"):
        for widget in self.scroll_frame. winfo_children():
            widget.destroy()
        self.accordion_items. clear()
        
        msg_label = ctk.CTkLabel(
            self.scroll_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        msg_label.pack(pady=40)
    
    # ==================== EVENTOS ====================
    
    def _on_select_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self._load_folder(folder)
    
    def _load_from_entry(self):
        path = self.folder_entry.get().strip()
        if path:
            self._load_folder(path)
    
    def _load_folder(self, folder:  str):
        if not os.path.exists(folder) or not os.path.isdir(folder):
            messagebox.showerror("Error", "Carpeta no válida")
            return
        self.folder_path = folder
        self._refresh()
    
    def _refresh(self):
        if not self.folder_path:
            messagebox.showinfo("Sin carpeta", "Selecciona primero una carpeta.")
            return
        
        try:
            self.groups = get_groups_case_sensitive(self.folder_path)
            self._rebuild_accordion()
            
            count = len(self.groups)
            self.counter_label.configure(text=f"{count} grupo(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la carpeta:\n{e}")
    
    def _rebuild_accordion(self):
        for widget in self.scroll_frame.winfo_children():
            widget. destroy()
        self.accordion_items.clear()
        
        if not self.groups:
            self._show_empty_message("⚠️ No hay grupos con más de 1 PDF")
            return
        
        for key, files in self.groups.items():
            item = AccordionItem(
                self.scroll_frame,
                group_key=key,
                files=files,
                on_merge_callback=self._on_merge_group
            )
            item.pack(fill="x", padx=2, pady=2)
            self.accordion_items.append(item)
    
    def _toggle_all(self):
        if not self.accordion_items:
            return
        any_expanded = any(item.is_expanded for item in self.accordion_items)
        for item in self.accordion_items:
            if any_expanded and item.is_expanded:
                item._toggle()
            elif not any_expanded and not item.is_expanded:
                item._toggle()
    
    # ==================== OPERACIONES ====================
    
    def _on_merge_group(self, key: str, files: List[str]):
        response = messagebox.askyesno(
            "Confirmar",
            f"¿Unir {len(files)} PDFs del grupo '{key}'?"
        )
        if not response:
            return
        
        success, errors, output_path = merge_group_and_move(self.folder_path, key, files)
        
        if success: 
            self. last_operation = {
                'type': 'single',
                'key': key,
                'files': files. copy(),
                'output': output_path
            }
            self. undo_button.configure(state="normal")
            messagebox.showinfo("Éxito", f"Grupo '{key}' unido.\nArchivo:  {output_path. name}")
        else:
            error_msg = "\n".join(errors[: 3]) if errors else "Error desconocido"
            messagebox.showerror("Error", f"No se pudo unir '{key}':\n{error_msg}")
        
        self._refresh()
    
    def _on_merge_all(self):
        if not self.groups:
            messagebox.showinfo("Sin grupos", "No hay grupos para unir.")
            return
        
        response = messagebox.askyesno(
            "Confirmar",
            f"¿Unir los {len(self.groups)} grupos?"
        )
        if not response:
            return
        
        merged_count = 0
        merged_outputs = []
        all_errors = []
        
        for key, files in self.groups.items():
            success, errors, output_path = merge_group_and_move(self.folder_path, key, files)
            if success:
                merged_count += 1
                merged_outputs. append({'key': key, 'files':  files. copy(), 'output': output_path})
            all_errors.extend(errors)
        
        if merged_outputs:
            self.last_operation = {
                'type': 'all',
                'merged':  merged_outputs
            }
            self.undo_button.configure(state="normal")
        
        self._refresh()
        
        msg = f"Se unieron {merged_count} de {len(self.groups)} grupos."
        if all_errors: 
            msg += f"\n\nErrores:\n" + "\n".join(all_errors[: 3])
        messagebox.showinfo("Resultado", msg)
    
    def _on_undo(self):
        if not self.last_operation:
            messagebox.showinfo("Info", "No hay operación para deshacer.")
            return
        
        op_type = self.last_operation. get('type')
        
        if op_type == 'single':
            key = self. last_operation['key']
            output = self.last_operation['output']
            
            response = messagebox.askyesno(
                "Confirmar Deshacer",
                f"¿Deshacer la unión del grupo '{key}'?\n\n"
                f"Se eliminará '{output.name}' y se restaurarán los originales."
            )
            if not response:
                return
            
            success, errors = undo_merge(self.folder_path, key, output)
            
            if success: 
                messagebox.showinfo("Deshacer completado", f"Grupo '{key}' restaurado.")
            else:
                messagebox.showerror("Error", f"No se pudo deshacer:\n" + "\n".join(errors))
        
        elif op_type == 'all':
            merged = self.last_operation.get('merged', [])
            
            response = messagebox.askyesno(
                "Confirmar Deshacer",
                f"¿Deshacer la unión de {len(merged)} grupos?"
            )
            if not response:
                return
            
            restored = 0
            for item in merged:
                success, _ = undo_merge(self. folder_path, item['key'], item['output'])
                if success:
                    restored += 1
            
            messagebox.showinfo("Deshacer completado", f"Se restauraron {restored} de {len(merged)} grupos.")
        
        self. last_operation = None
        self. undo_button.configure(state="disabled")
        self._refresh()

