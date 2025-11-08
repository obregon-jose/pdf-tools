#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# rename_pdf_tk.py
#
# Pequeña aplicación Tkinter para buscar y reemplazar patrones en los nombres
# de archivos PDF dentro de una carpeta (opción recursiva disponible).
#
# Características:
# - Seleccionar carpeta
# - Especificar patrón a buscar y texto de reemplazo
# - Modo: literal o expresión regular
# - Opciones: sensible a mayúsculas, recursivo, sobrescribir archivos destino
# - Previsualizar los cambios antes de renombrar
# - Renombrar todos o solo los seleccionados desde la lista
#
# Uso:
# python3 rename_pdf_tk.py
#
# Requiere Python 3.x (sin dependencias externas).

import os
import re
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

PDF_EXTS = {'.pdf', '.PDF'}


class RenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Renombrar PDFs - Buscar y Reemplazar")
        self.root.geometry("900x600")

        self.folder_path = tk.StringVar()
        self.pattern = tk.StringVar()
        self.replacement = tk.StringVar()
        self.use_regex = tk.BooleanVar(value=False)
        self.case_sensitive = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=False)
        self.overwrite = tk.BooleanVar(value=False)

        # Keep the last preview mapping and last performed operations for optional feedback
        self.preview_map = {}   # {full_old_path: full_new_path}
        self.last_renamed = []  # list of tuples (old, new, succeeded, error)

        self._build_ui()

    def _build_ui(self):
        frm_top = ttk.Frame(self.root, padding=8)
        frm_top.pack(fill=tk.X)

        # Folder selection row
        ttk.Label(frm_top, text="Carpeta:").grid(row=0, column=0, sticky=tk.W)
        ent_folder = ttk.Entry(frm_top, textvariable=self.folder_path, width=70)
        ent_folder.grid(row=0, column=1, padx=6, sticky=tk.W)
        ttk.Button(frm_top, text="Seleccionar...", command=self.select_folder).grid(row=0, column=2, padx=6)

        # Pattern / Replacement row
        ttk.Label(frm_top, text="Buscar (patrón):").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(frm_top, textvariable=self.pattern, width=40).grid(row=1, column=1, sticky=tk.W, pady=(8, 0))
        ttk.Label(frm_top, text="Reemplazar por:").grid(row=1, column=2, sticky=tk.W, pady=(8, 0))
        ttk.Entry(frm_top, textvariable=self.replacement, width=30).grid(row=1, column=3, sticky=tk.W, pady=(8, 0))

        # Options row
        opts = ttk.Frame(frm_top)
        opts.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(8, 0))
        ttk.Checkbutton(opts, text="Expresión regular", variable=self.use_regex).grid(row=0, column=0, padx=6)
        ttk.Checkbutton(opts, text="Sensible a mayúsculas", variable=self.case_sensitive).grid(row=0, column=1, padx=6)
        ttk.Checkbutton(opts, text="Recursivo", variable=self.recursive).grid(row=0, column=2, padx=6)
        ttk.Checkbutton(opts, text="Sobrescribir destino", variable=self.overwrite).grid(row=0, column=3, padx=6)

        # Action buttons
        actions = ttk.Frame(frm_top)
        actions.grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=(10, 0))
        ttk.Button(actions, text="Previsualizar", command=self.preview).grid(row=0, column=0, padx=6)
        ttk.Button(actions, text="Renombrar todo", command=lambda: self.rename(confirm=True, only_selected=False)).grid(row=0, column=1, padx=6)
        ttk.Button(actions, text="Renombrar seleccionados", command=lambda: self.rename(confirm=True, only_selected=True)).grid(row=0, column=2, padx=6)
        ttk.Button(actions, text="Refrescar lista", command=self.refresh_preview_from_folder).grid(row=0, column=3, padx=6)

        # Treeview for listing files and proposed names
        self.tree = ttk.Treeview(self.root, columns=('old', 'new', 'status'), show='headings', selectmode='extended')
        self.tree.heading('old', text='Archivo actual')
        self.tree.heading('new', text='Nuevo nombre')
        self.tree.heading('status', text='Estado')
        self.tree.column('old', width=360)
        self.tree.column('new', width=360)
        self.tree.column('status', width=120, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Vertical scrollbar
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')

        # Status bar
        self.status_var = tk.StringVar(value="Listo.")
        status = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status.pack(fill=tk.X, side=tk.BOTTOM)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.refresh_preview_from_folder()

    def _list_pdfs(self, folder):
        """Return list of full paths to PDFs in folder (respecting recursion option)."""
        pdfs = []
        if self.recursive.get():
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if os.path.splitext(f)[1] in PDF_EXTS:
                        pdfs.append(os.path.join(root, f))
        else:
            try:
                for f in os.listdir(folder):
                    full = os.path.join(folder, f)
                    if os.path.isfile(full) and os.path.splitext(f)[1] in PDF_EXTS:
                        pdfs.append(full)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo listar la carpeta:\n{e}")
        return sorted(pdfs, key=lambda p: p.lower())

    def _compute_new_name(self, filename):
        """
        Given a base filename (with extension), compute the new filename after replacement.
        Only operate on the basename without changing the extension.
        """
        base, ext = os.path.splitext(filename)
        pat = self.pattern.get()
        repl = self.replacement.get()
        if pat == "":
            return filename  # nothing to change

        flags = 0 if self.case_sensitive.get() else re.IGNORECASE
        if self.use_regex.get():
            try:
                newbase = re.sub(pat, repl, base, flags=flags)
            except re.error as e:
                # Invalid regex
                raise ValueError(f"Expresión regular inválida: {e}")
        else:
            if self.case_sensitive.get():
                newbase = base.replace(pat, repl)
            else:
                # case-insensitive replace for literal: we can use a regex escape
                try:
                    newbase = re.sub(re.escape(pat), repl, base, flags=re.IGNORECASE)
                except re.error as e:
                    raise ValueError(f"Error interno al reemplazar: {e}")

        return newbase + ext

    def preview(self):
        folder = self.folder_path.get().strip()
        if not folder:
            messagebox.showwarning("Carpeta no seleccionada", "Por favor, seleccione una carpeta primero.")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("Carpeta inválida", "La ruta seleccionada no es una carpeta válida.")
            return

        # Clear tree
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.preview_map.clear()

        try:
            pdfs = self._list_pdfs(folder)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la lista de PDFs:\n{e}")
            return

        # Compute mapping and detect conflicts
        proposed_targets = {}
        errors = []
        for full in pdfs:
            dirname, fname = os.path.split(full)
            try:
                new_fname = self._compute_new_name(fname)
            except ValueError as e:
                errors.append(str(e))
                new_fname = fname  # fallback
            new_full = os.path.join(dirname, new_fname)

            status = "Sin cambio"
            if new_fname != fname:
                if os.path.exists(new_full) and os.path.normpath(new_full) != os.path.normpath(full):
                    status = "Conflicto (exists)"
                elif new_full in proposed_targets.values():
                    # Another file in the same preview would map to the same target
                    status = "Conflicto (duplicado)"
                else:
                    status = "OK"
            self.preview_map[full] = new_full
            proposed_targets[full] = new_full

            # Insert in tree
            self.tree.insert('', tk.END, iid=full, values=(fname, os.path.relpath(new_full, start=folder), status))

        if errors:
            messagebox.showwarning("Advertencia", "Se encontraron errores al procesar el patrón:\n" + "\n".join(errors))

        self.status_var.set(f"Previsualización completada: {len(pdfs)} archivos listados.")

    def refresh_preview_from_folder(self):
        # Re-run preview (useful after toggling options)
        self.preview()

    def rename(self, confirm=True, only_selected=False):
        if not self.preview_map:
            messagebox.showinfo("Sin previsualización", "No hay previsualización. Haga clic en 'Previsualizar' primero.")
            return

        # Build list to rename
        if only_selected:
            selected = self.tree.selection()
            if not selected:
                messagebox.showinfo("Nada seleccionado", "Seleccione al menos un archivo en la lista.")
                return
            items = [s for s in selected]
        else:
            items = list(self.preview_map.keys())

        # Filter items that actually change and are OK
        to_rename = []
        conflicts = []
        for old in items:
            new = self.preview_map.get(old)
            if not new or os.path.normpath(old) == os.path.normpath(new):
                continue  # nothing to do
            # Check target exists
            if os.path.exists(new) and not self.overwrite.get():
                conflicts.append((old, new, "Destino existe"))
            else:
                # Also check that multiple sources don't map to same target (unless overwrite)
                to_rename.append((old, new))

        if not to_rename and not conflicts:
            messagebox.showinfo("Nada que renombrar", "No hay archivos válidos para renombrar.")
            return

        # Show confirmation with summary
        summary_lines = [f"{os.path.basename(o)}  ->  {os.path.relpath(n, start=self.folder_path.get())}" for o, n in to_rename]
        if conflicts:
            summary_lines.append("")
            summary_lines.append("Conflictos (no se renombrarán a menos que active 'Sobrescribir destino'):")
            for o, n, reason in conflicts:
                summary_lines.append(f"{os.path.basename(o)}  ->  {os.path.relpath(n, start=self.folder_path.get())}   [{reason}]")

        if confirm:
            if not messagebox.askokcancel("Confirmar renombrado", "Se renombrarán los siguientes archivos:\n\n" + "\n".join(summary_lines)):
                return

        # Perform renaming
        self.last_renamed.clear()
        errors = []
        # To reduce the chance of collisions mid-rename, do two-phase approach if possible:
        # But a simple sequential rename should be sufficient for most cases. We'll try sequentially.
        for old, new in to_rename:
            try:
                # Ensure target directory exists (it should) and create intermediate backup if needed
                if os.path.normpath(old) == os.path.normpath(new):
                    self.last_renamed.append((old, new, True, "Sin cambio"))
                    continue

                if os.path.exists(new):
                    if self.overwrite.get():
                        # remove target first
                        try:
                            os.remove(new)
                        except Exception as e:
                            raise RuntimeError(f"No se pudo eliminar destino existente: {e}")
                    else:
                        # skip because we already collected conflicts earlier
                        self.last_renamed.append((old, new, False, "Destino existe"))
                        continue

                os.rename(old, new)
                self.last_renamed.append((old, new, True, "OK"))
            except Exception as e:
                self.last_renamed.append((old, new, False, str(e)))
                errors.append(f"{os.path.basename(old)} -> {os.path.basename(new)} : {e}")

        # Refresh the preview (re-run) to update statuses
        self.preview()

        # Report results
        succeeded = sum(1 for t in self.last_renamed if t[2])
        failed = len(self.last_renamed) - succeeded
        msg = f"Renombrado completado. Éxitos: {succeeded}. Fallos: {failed}."
        if errors:
            msg += "\n\nErrores:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += f"\n... ({len(errors) - 10} errores más)"
            messagebox.showerror("Algunos errores ocurrieron", msg)
        else:
            messagebox.showinfo("Listo", msg)
        self.status_var.set(msg)


def main():
    root = tk.Tk()
    app = RenameApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()