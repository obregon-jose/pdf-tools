import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import pandas as pd
import dns.resolver
import unicodedata
import re
import os


class EmailValidatorApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # ---------- Ventana ----------
        self.title("Verificador de correos desde Excel")
        self.geometry("880x690")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ---------- Estado ----------
        self.ruta_archivo = None
        self.cache_dominios = set()

        # ---------- Regex compilado ----------
        self.regex_email = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        self._crear_interfaz()

    # ---------- Utilidades ----------
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        nfkd = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    def es_correo_valido(self, correo: str) -> bool:
        return bool(self.regex_email.fullmatch(correo))

    def dominio_es_valido(self, dominio: str) -> bool:
        if dominio in self.cache_dominios:
            return True
        try:
            dns.resolver.resolve(dominio, "MX", lifetime=4)
            self.cache_dominios.add(dominio)
            return True
        except Exception:
            return False

    @staticmethod
    def encontrar_columna_correo(columnas):
        posibles = {"correo", "email", "e-mail", "mail", "correo electrónico"}
        for col in columnas:
            if col.lower() in posibles:
                return col
        return None

    # ---------- Lógica principal ----------
    def procesar_excel(self, path: str):
        self.resultado_text.config(state="normal")
        self.resultado_text.delete(1.0, "end")
        self.estado_label.configure(text="⏳ Procesando...")
        self.progress_bar.set(0)

        try:
            df = pd.read_excel(path)
        except Exception as e:
            self._mostrar_error(f"Error al leer archivo: {e}")
            return

        columna = self.encontrar_columna_correo(df.columns)
        if not columna:
            self._mostrar_error("No se encontró columna de correos")
            return

        correos = df[columna].dropna()
        total = len(correos)
        errores = 0

        self._log(f"📄 Archivo: {os.path.basename(path)}")
        self._log("🔍 Validando correos...\n")

        for i, correo in enumerate(correos, start=1):
            fila_excel = i + 1
            correo_original = str(correo).strip()

            if "@" not in correo_original:
                self._log(f"Fila {fila_excel}: '{correo_original}' ❌ Falta '@'")
                errores += 1
                self._actualizar_progreso(i, total)
                continue

            usuario, dominio = correo_original.split("@", 1)

            if any(ord(c) > 127 for c in usuario):
                self._log(f"Fila {fila_excel}: '{correo_original}' ❌ Usuario con acentos")
                errores += 1
                self._actualizar_progreso(i, total)
                continue

            correo_limpio = self.normalizar_texto(correo_original)

            if not self.es_correo_valido(correo_limpio):
                self._log(f"Fila {fila_excel}: '{correo_original}' ❌ Formato inválido")
                errores += 1
                self._actualizar_progreso(i, total)
                continue

            if not self.dominio_es_valido(dominio):
                self._log(f"Fila {fila_excel}: '{correo_original}' ❌ Dominio inválido")
                errores += 1

            self._actualizar_progreso(i, total)

        if errores == 0:
            self._log("\n✅ Todos los correos son válidos")
            self.estado_label.configure(text="✅ Sin errores")
        else:
            self._log(f"\n⚠️ Total de errores: {errores}")
            self.estado_label.configure(text=f"⚠️ {errores} errores")

        self.resultado_text.config(state="disabled")

    # ---------- UI ----------
    def _crear_interfaz(self):
        ctk.CTkLabel(
            self,
            text="📄 Verificador de correos desde Excel",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=15)

        frame = ctk.CTkFrame(self)
        frame.pack(pady=10)

        ctk.CTkButton(
            frame,
            text="📂 Cargar Excel",
            width=180,
            command=self.cargar_excel,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            frame,
            text="🔁 Revisar Mismo Archivo",
            width=220,
            fg_color="#f1c40f",
            text_color="black",
            command=self.revisar_mismo_archivo,
        ).pack(side="left", padx=10)

        # 🔵 Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(self, width=520)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=12)

        self.resultado_text = ScrolledText(
            self, width=105, height=24, font=("Courier", 10)
        )
        self.resultado_text.pack(padx=15, pady=10)
        self.resultado_text.config(state="disabled")

        self.estado_label = ctk.CTkLabel(
            self, text="🕒 Esperando archivo...", text_color="gray"
        )
        self.estado_label.pack(pady=5)

    # ---------- Eventos ----------
    def cargar_excel(self):
        archivo = filedialog.askopenfilename(
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if archivo:
            self.ruta_archivo = archivo
            self.procesar_excel(archivo)

    def revisar_mismo_archivo(self):
        if not self.ruta_archivo or not os.path.exists(self.ruta_archivo):
            messagebox.showwarning("Aviso", "Primero carga un archivo válido")
            return
        self.procesar_excel(self.ruta_archivo)

    # ---------- Helpers ----------
    def _actualizar_progreso(self, actual, total):
        self.progress_bar.set(actual / total)
        self.update_idletasks()

    def _log(self, texto: str):
        self.resultado_text.insert("end", texto + "\n")

    def _mostrar_error(self, mensaje: str):
        self._log(f"❌ {mensaje}")
        self.resultado_text.config(state="disabled")
        self.estado_label.configure(text="⚠️ Error")


if __name__ == "__main__":
    app = EmailValidatorApp()
    app.mainloop()
