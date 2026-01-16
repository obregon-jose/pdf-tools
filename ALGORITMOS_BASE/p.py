#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# rename_pdf_tk.py corregido: usando ttk.Treeview en lugar de CTkTreeview

import os
import re
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk


PDF_EXTS = {'.pdf', '.PDF'}


class RenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Renombrar PDFs - Buscar y Reemplazar")
        self.root.geometry("900x600")

        self.folder_path = ctk.StringVar()
        self.pattern = ctk.StringVar()
        self.replacement = ctk.StringVar()
        self.use_regex = ctk.BooleanVar(value=False)
        self.case_sensitive = ctk.BooleanVar(value=False)
        self.recursive = ctk.BooleanVar(value=False)
        self.overwrite = ctk.BooleanVar(value=False)

        self.preview_map = {}   # {full_old_path: full_new_path}
        self.last_renamed = []  # list of tuples (old, new, succeeded, error)

        self._build_ui()

    def _build_ui(self):
        frm_top = ctk.CTkFrame(self.root)
        frm_top.pack(padx=8, pady=8, fill=ctk.X)

        # Folder selection row
        ctk.CTkLabel(frm_top, text="Carpeta:").grid(row=0, column=0, sticky=ctk.W)
        ent_folder = ctk.CTkEntry(frm_top, textvariable=self.folder_path, width=350)
        ent_folder.grid(row=0, column=1, padx=6, sticky=ctk.W)
        ctk.CTkButton(frm_top, text="Seleccionar...", command=self.select_folder).grid(row=0, column=2, padx=6)

        # Pattern / Replacement row
        ctk.CTkLabel(frm_top, text="Buscar (patrón):").grid(row=1, column=0, sticky=ctk.W, pady=(8, 0))
        ctk.CTkEntry(frm_top, textvariable=self.pattern, width=200).grid(row=1, column=1, sticky=ctk.W, pady=(8, 0))
        ctk.CTkLabel(frm_top, text="Reemplazar por:").grid(row=1, column=2, sticky=ctk.W, pady=(8, 0))
        ctk.CTkEntry(frm_top, textvariable=self.replacement, width=150).grid(row=1, column=3, sticky=ctk.W, pady=(8, 0))

        # Options row
        opts = ctk.CTkFrame(frm_top)
        opts.grid(row=2, column=0, columnspan=4, sticky=ctk.W, pady=(8, 0))
        ctk.CTkCheckBox(opts, text="Expresión regular", variable=self.use_regex).grid(row=0, column=0, padx=6)
        ctk.CTkCheckBox(opts, text="Sensible a mayúsculas", variable=self.case_sensitive).grid(row=0, column=1, padx=6)
        ctk.CTkCheckBox(opts, text="Recursivo", variable=self.recursive).grid(row=0, column=2, padx=6)
        ctk.CTkCheckBox(opts, text="Sobrescribir destino", variable=self.overwrite).grid(row=0, column=3, padx=6)

        # Action buttons
        actions = ctk.CTkFrame(frm_top)
        actions.grid(row=3, column=0, columnspan=4, sticky=ctk.W, pady=(10, 0))
        ctk.CTkButton(actions, text="Previsualizar", command=self.preview).grid(row=0, column=0, padx=6)
        ctk.CTkButton(actions, text="Renombrar todo",
                      command=lambda: self.rename(confirm=True, only_selected=False)).grid(row=0, column=1, padx=6)
        ctk.CTkButton(actions, text="Renombrar seleccionados",
                      command=lambda: self.rename(confirm=True, only_selected=True)).grid(row=0, column=2, padx=6)
        ctk.CTkButton(actions, text="Refrescar lista", command=self.refresh_preview_from_folder).grid(row=0, column=3, padx=6)

        # -----------------------
        #  TREEVIEW (CORREGIDO)
        # -----------------------

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2b2b2b",
                        bordercolor="#444444",
                        borderwidth=0)
        style.map("Treeview",
                  background=[('selected', '#1f538d')])

        self.tree = ttk.Treeview(
            self.root,
            columns=('old', 'new', 'status'),
            show='headings',
            selectmode='extended'
        )

        self.tree.heading('old', text='Archivo actual')
        self.tree.heading('new', text='Nuevo nombre')
        self.tree.heading('status', text='Estado')

        self.tree.column('old', width=360)
        self.tree.column('new', width=360)
        self.tree.column('status', width=120, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=8, pady=8)

        # Scrollbar
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')

        # Status bar
        self.status_var = ctk.StringVar(value="Listo.")
        status = ctk.CTkLabel(self.root, textvariable=self.status_var)
        status.pack(fill=ctk.X, side=ctk.BOTTOM)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.refresh_preview_from_folder()

    def _list_pdfs(self, folder):
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
        base, ext = os.path.splitext(filename)
        pat = self.pattern.get()
        repl = self.replacement.get()

        if pat == "":
            return filename

        flags = 0 if self.case_sensitive.get() else re.IGNORECASE

        if self.use_regex.get():
            try:
                newbase = re.sub(pat, repl, base, flags=flags)
            except re.error as e:
                raise ValueError(f"Expresión regular inválida: {e}")
        else:
            if self.case_sensitive.get():
                newbase = base.replace(pat, repl)
            else:
                try:
                    newbase = re.sub(re.escape(pat), repl, base, flags=re.IGNORECASE)
                except re.error as e:
                    raise ValueError(f"Error interno al reemplazar: {e}")

        return newbase + ext

    def preview(self):
        folder = self.folder_path.get().strip()
        if not folder:
            messagebox.showwarning("Carpeta no seleccionada", "Seleccione una carpeta primero.")
            return

        if not os.path.isdir(folder):
            messagebox.showerror("Carpeta inválida", "La ruta seleccionada no es válida.")
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

        proposed_targets = {}
        errors = []

        for full in pdfs:
            dirname, fname = os.path.split(full)
            try:
                new_fname = self._compute_new_name(fname)
            except ValueError as e:
                errors.append(str(e))
                new_fname = fname

            new_full = os.path.join(dirname, new_fname)

            status = "Sin cambio"
            if new_fname != fname:
                if os.path.exists(new_full) and os.path.normpath(new_full) != os.path.normpath(full):
                    status = "Conflicto (exists)"
                elif new_full in proposed_targets.values():
                    status = "Conflicto (duplicado)"
                else:
                    status = "OK"

            self.preview_map[full] = new_full
            proposed_targets[full] = new_full

            self.tree.insert('', 'end',
                             iid=full,
                             values=(fname, os.path.relpath(new_full, start=folder), status))

        if errors:
            messagebox.showwarning("Advertencia", "Errores con el patrón:\n" + "\n".join(errors))

        self.status_var.set(f"Previsualización completada: {len(pdfs)} archivos.")

    def refresh_preview_from_folder(self):
        self.preview()

    def rename(self, confirm=True, only_selected=False):
        if not self.preview_map:
            messagebox.showinfo("Sin previsualización", "Genere una previsualización primero.")
            return

        if only_selected:
            selected = self.tree.selection()
            if not selected:
                messagebox.showinfo("Nada seleccionado", "Seleccione archivos en la lista.")
                return
            items = list(selected)
        else:
            items = list(self.preview_map.keys())

        to_rename = []
        conflicts = []

        for old in items:
            new = self.preview_map.get(old)
            if not new or os.path.normpath(old) == os.path.normpath(new):
                continue

            if os.path.exists(new) and not self.overwrite.get():
                conflicts.append((old, new, "Destino existe"))
            else:
                to_rename.append((old, new))

        if not to_rename and not conflicts:
            messagebox.showinfo("Nada que renombrar", "No hay archivos válidos.")
            return

        summary = [f"{os.path.basename(o)}  ->  {os.path.relpath(n, start=self.folder_path.get())}"
                   for o, n in to_rename]

        if conflicts:
            summary.append("")
            summary.append("Conflictos:")
            for o, n, r in conflicts:
                summary.append(f"{os.path.basename(o)} → {os.path.basename(n)} [{r}]")

        if confirm:
            if not messagebox.askokcancel("Confirmar", "Se renombrarán:\n\n" + "\n".join(summary)):
                return

        self.last_renamed.clear()
        errors = []

        for old, new in to_rename:
            try:
                if os.path.exists(new) and self.overwrite.get():
                    os.remove(new)

                os.rename(old, new)
                self.last_renamed.append((old, new, True, "OK"))

            except Exception as e:
                self.last_renamed.append((old, new, False, str(e)))
                errors.append(f"{old} -> {new} : {e}")

        self.preview()

        ok = sum(1 for x in self.last_renamed if x[2])
        bad = len(self.last_renamed) - ok
        msg = f"Completado. Éxitos: {ok}. Fallos: {bad}."

        if errors:
            msg += "\n\nErrores:\n" + "\n".join(errors[:10])
            messagebox.showerror("Errores", msg)
        else:
            messagebox.showinfo("Listo", msg)

        self.status_var.set(msg)


def main():
    root = ctk.CTk()
    app = RenameApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
