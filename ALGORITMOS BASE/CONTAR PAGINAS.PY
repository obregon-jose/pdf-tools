
import os

import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# Try to import pypdf (preferred) or PyPDF2 as fallback
try:
    from pypdf import PdfMerger  # pypdf moderno
    _MERGER_FACTORY = lambda: PdfMerger()
except Exception:
    try:
        from PyPDF2 import PdfFileMerger  # fallback
        class _PyPDF2Adapter:
            def __init__(self):
                self._m = PdfFileMerger()
            def append(self, path):
                self._m.append(path)
            def write(self, out_path):
                with open(out_path, "wb") as f:
                    self._m.write(f)
            def close(self):
                try:
                    self._m.close()
                except Exception:
                    pass
        _MERGER_FACTORY = lambda: _PyPDF2Adapter()
    except Exception:
        PdfMerger = None
        _MERGER_FACTORY = None

USE_MERGER = _MERGER_FACTORY is not None

PDF_EXTS = {'.pdf', '.PDF'}


class GroupWidget:
    """Represents a single accordion group UI inside the scrollable area."""
    def __init__(self, parent, key, files, base_folder):
        self.parent = parent
        self.key = key
        self.files = files[:]  # list of full paths
        self.base_folder = base_folder

        self.var_selected = tk.BooleanVar(value=True)
        self.expanded = False

        # Main frame for this group
        self.frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1, padding=(4,4))
        # Header row
        self.header = ttk.Frame(self.frame)
        self.header.pack(fill=tk.X)
        self.chk = ttk.Checkbutton(self.header, variable=self.var_selected)
        self.chk.pack(side=tk.LEFT)
        self.btn_toggle = ttk.Button(self.header, width=2, text='+', command=self.toggle)
        self.btn_toggle.pack(side=tk.LEFT, padx=(4,4))
        display_name = self.key.strip()
        self.lbl_title = ttk.Label(self.header, text=f"{display_name}   ({len(self.files)})", font=('TkDefaultFont', 10, 'bold'))
        self.lbl_title.pack(side=tk.LEFT)
        # small spacer and show preview button
        self.btn_show = ttk.Button(self.header, text="Abrir lista", command=self.open_folder)
        self.btn_show.pack(side=tk.RIGHT)

        # Content area (hidden initially)
        self.content = ttk.Frame(self.frame)
        # Add file labels in content
        for f in self.files:
            bn = os.path.basename(f)
            lbl = ttk.Label(self.content, text=bn)
            lbl.pack(anchor=tk.W, padx=(24,8))

    def toggle(self):
        if self.expanded:
            self.content.forget()
            self.btn_toggle.config(text='+')
            self.expanded = False
        else:
            self.content.pack(fill=tk.X, pady=(4,4))
            self.btn_toggle.config(text='-')
            self.expanded = True

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def destroy(self):
        self.frame.destroy()

    def open_folder(self):
        # open folder containing first file, or base folder
        target_dir = os.path.dirname(self.files[0]) if self.files else self.base_folder
        try:
            if os.name == 'nt':
                os.startfile(target_dir)
            elif os.uname().sysname == 'Darwin':
                os.system(f'open "{target_dir}"')
            else:
                os.system(f'xdg-open "{target_dir}"')
        except Exception:
            messagebox.showinfo("Carpeta", f"Carpeta: {target_dir}")


class MergeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unir PDFs por grupo (acordeón) - mover originales a 'grupos' y unidos a 'unidos'")
        self.root.geometry("880x620")

        self.folder = tk.StringVar()
        self.recursive = tk.BooleanVar(value=False)
        self.overwrite = tk.BooleanVar(value=False)
        self.include_singletons = tk.BooleanVar(value=False)

        self.groups = {}  # key -> list of file paths
        self.group_widgets = {}  # key -> GroupWidget

        self._build_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding=8)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Carpeta:").pack(side=tk.LEFT)
        ent = ttk.Entry(top_frame, textvariable=self.folder, width=70)
        ent.pack(side=tk.LEFT, padx=6)
        ttk.Button(top_frame, text="Seleccionar...", command=self.select_folder).pack(side=tk.LEFT)
        ttk.Checkbutton(top_frame, text="Recursivo", variable=self.recursive).pack(side=tk.LEFT, padx=6)

        opts = ttk.Frame(self.root, padding=(8,0))
        opts.pack(fill=tk.X)
        ttk.Checkbutton(opts, text="Incluir grupos de 1 archivo", variable=self.include_singletons).pack(side=tk.LEFT)
        ttk.Checkbutton(opts, text="Sobrescribir archivos destino", variable=self.overwrite).pack(side=tk.LEFT, padx=12)

        actions = ttk.Frame(self.root, padding=(8,4))
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Previsualizar grupos", command=self.preview).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Seleccionar todos", command=self.select_all).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Deseleccionar todos", command=self.deselect_all).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Unir grupos seleccionados", command=self.merge_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Unir todos", command=self.merge_all).pack(side=tk.LEFT, padx=6)

        # Scrollable accordion area
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(container)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.inner, anchor='nw')

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_windows)

        # Status bar
        self.status = tk.StringVar(value="Listo.")
        ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, side=tk.BOTTOM)

    def _on_mousewheel_windows(self, event):
        # Cross-platform small handler, on Linux sometimes event.num is used
        try:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)
            self.preview()

    def _list_pdfs(self, folder):
        files = []
        if self.recursive.get():
            for root, dirs, filenames in os.walk(folder):
                for f in filenames:
                    if os.path.splitext(f)[1] in PDF_EXTS:
                        files.append(os.path.join(root, f))
        else:
            try:
                for f in os.listdir(folder):
                    full = os.path.join(folder, f)
                    if os.path.isfile(full) and os.path.splitext(f)[1] in PDF_EXTS:
                        files.append(full)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo listar la carpeta: {e}")
        return sorted(files, key=lambda p: os.path.basename(p).lower())

    def _group_key(self, filename):
        base = os.path.splitext(filename)[0]
        parts = base.strip().split(' ', 1)
        # Key is the part up to first space, without extra spaces
        return parts[0].strip() if parts and parts[0] != '' else base.strip()

    def preview(self):
        folder = self.folder.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Carpeta inválida", "Seleccione una carpeta válida primero.")
            return

        pdfs = self._list_pdfs(folder)
        groups = {}
        for full in pdfs:
            name = os.path.basename(full)
            key = self._group_key(name)
            groups.setdefault(key, []).append(full)

        if not self.include_singletons.get():
            groups = {k: v for k, v in groups.items() if len(v) > 1}

        for k in groups:
            groups[k].sort(key=lambda p: os.path.basename(p).lower())

        # Clear previous widgets
        for gw in self.group_widgets.values():
            gw.destroy()
        self.group_widgets.clear()
        self.groups = groups

        # Create accordion entries
        for k, files in sorted(groups.items(), key=lambda kv: kv[0].lower()):
            gw = GroupWidget(self.inner, k, files, folder)
            gw.pack(fill=tk.X, pady=(4,4), padx=4)
            self.group_widgets[k] = gw

        self.status.set(f"Previsualización: {len(self.groups)} grupos (carpeta: {folder})")

    def select_all(self):
        for gw in self.group_widgets.values():
            gw.var_selected.set(True)

    def deselect_all(self):
        for gw in self.group_widgets.values():
            gw.var_selected.set(False)

    def _ensure_dirs(self):
        base = self.folder.get().strip()
        grupos_dir = os.path.join(base, "grupos")
        unidos_dir = os.path.join(base, "unidos")
        os.makedirs(grupos_dir, exist_ok=True)
        os.makedirs(unidos_dir, exist_ok=True)
        return grupos_dir, unidos_dir

    def _unique_target(self, target_path):
        """If target exists, generate a unique filename by appending _1, _2, ..."""
        if not os.path.exists(target_path):
            return target_path
        base, ext = os.path.splitext(target_path)
        i = 1
        while True:
            candidate = f"{base}_{i}{ext}"
            if not os.path.exists(candidate):
                return candidate
            i += 1

    def _move_to_grupos(self, src_path, grupos_dir):
        """Move a file to grupos_dir, preserving filename, disambiguating if necessary."""
        bn = os.path.basename(src_path)
        target = os.path.join(grupos_dir, bn)
        if os.path.exists(target):
            if self.overwrite.get():
                try:
                    os.remove(target)
                except Exception:
                    pass
            else:
                target = self._unique_target(target)
        try:
            shutil.move(src_path, target)
            return target, None
        except Exception as e:
            return None, str(e)

    def _merge_group(self, key, files, grupos_dir, unidos_dir, results):
        # Prepare clean group name for output: key trimmed, no spaces
        out_basename = key.strip().replace(' ', '')
        if out_basename == '':
            out_basename = key.strip()  # fallback
        out_name = f"{out_basename}.pdf"
        out_path = os.path.join(unidos_dir, out_name)

        # If already exists and not overwrite: skip
        if os.path.exists(out_path) and not self.overwrite.get():
            results.append((key, out_path, "skipped_exists"))
            return

        # Move originals into grupos_dir first (as required)
        moved_files = []
        for f in files:
            newf, err = self._move_to_grupos(f, grupos_dir)
            if err:
                results.append((key, "", f"error_move:{err}"))
                # if move fails for any file, attempt to continue with what moved, or abort group
                # We'll abort merging this group to avoid incomplete results.
                # Move back already moved? Not attempted here.
                return
            moved_files.append(newf)

        # Instantiate merger
        if not USE_MERGER:
            results.append((key, out_path, "no_merger"))
            return

        try:
            merger = _MERGER_FACTORY()
        except Exception as e:
            results.append((key, out_path, f"error_init:{e}"))
            return

        try:
            for mf in moved_files:
                merger.append(mf)
            # Write output
            merger.write(out_path)
            try:
                merger.close()
            except Exception:
                pass
            results.append((key, out_path, "ok"))
        except Exception as e:
            results.append((key, out_path, f"error_write:{e}"))
            try:
                merger.close()
            except Exception:
                pass

    def _run_merge(self, keys_to_merge):
        if not USE_MERGER:
            messagebox.showerror("Dependencia faltante", "No se encontró pypdf ni PyPDF2. Instale pypdf con:\n\npip install pypdf")
            return

        if not keys_to_merge:
            messagebox.showinfo("Nada para unir", "No se seleccionaron grupos para unir.")
            return

        grupos_dir, unidos_dir = self._ensure_dirs()
        self.status.set("Iniciando unión...")

        def worker():
            results = []
            for key in keys_to_merge:
                files = self.groups.get(key) or []
                if not files:
                    results.append((key, "", "no_files"))
                    continue
                self.status.set(f"Procesando {key} ...")
                self._merge_group(key, files, grupos_dir, unidos_dir, results)
            ok = [r for r in results if r[2] == "ok"]
            skipped = [r for r in results if r[2] == "skipped_exists"]
            errors = [r for r in results if r[2].startswith("error") or r[2] == "no_files" or r[2] == "no_merger"]
            summary = f"Unión terminada. OK: {len(ok)}. Saltados: {len(skipped)}. Errores: {len(errors)}."
            lines = [f"{r[0]} -> {os.path.basename(r[1]) if r[1] else ''} [{r[2]}]" for r in results]
            msg = summary + "\n\nDetalles:\n" + "\n".join(lines[:200])
            def on_done():
                if errors:
                    messagebox.showwarning("Resultado", msg)
                else:
                    messagebox.showinfo("Resultado", msg)
                self.status.set(summary + f" (grupos: {grupos_dir} | unidos: {unidos_dir})")
                # Refresh preview to reflect that originals moved into grupos and won't appear in folder
                self.preview()
            self.root.after(10, on_done)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def merge_selected(self):
        keys = [k for k, gw in self.group_widgets.items() if gw.var_selected.get()]
        if not keys:
            messagebox.showinfo("Seleccione", "Seleccione uno o más grupos en la UI.")
            return
        if not messagebox.askokcancel("Confirmar", f"Se van a unir {len(keys)} grupos. Se moverán los originales a la carpeta 'grupos' y los unidos a 'unidos'. ¿Continuar?"):
            return
        self._run_merge(keys)

    def merge_all(self):
        keys = list(self.groups.keys())
        if not keys:
            messagebox.showinfo("Nada", "No hay grupos para unir. Haga una previsualización primero.")
            return
        if not messagebox.askokcancel("Confirmar", f"Se van a unir todos los grupos ({len(keys)}). ¿Continuar?"):
            return
        self._run_merge(keys)


def main():
    root = tk.Tk()
    app = MergeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()