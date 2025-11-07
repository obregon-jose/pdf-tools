# import tkinter as tk
# from tkinter import ttk, messagebox
# import requests
# import time
# import random
# import threading

# # Diccionario de tipos de documento
# TIPOS_DOC = {
#     "CC": 1,  # Cédula de ciudadanía
#     "TI": 2,  # Tarjeta de identidad
#     "RC": 3   # Registro civil
# }

# BASE_URL = "https://backend.horus-health.com/api/afiliados/consultar-afiliado"

# def consultar_afiliado(token, documento):
#     """Consulta un afiliado individualmente."""
#     tipo = ''.join([c for c in documento if c.isalpha()]).upper()
#     numero = ''.join([c for c in documento if c.isdigit()])

#     tipo_id = TIPOS_DOC.get(tipo)

#     if not tipo_id or not numero:
#         return documento, "REVISAR (formato inválido)"

#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Accept": "application/json"
#     }

#     url = f"{BASE_URL}/{numero}/{tipo_id}"

#     try:
#         response = requests.get(url, headers=headers, timeout=10)

#         if response.status_code == 200:
#             data = response.json()
#             if "primer_nombre" in data:
#                 nombre = f"{data.get('primer_nombre', '')} {data.get('segundo_nombre', '')} {data.get('primer_apellido', '')} {data.get('segundo_apellido', '')}".strip()
#                 return documento, nombre
#             else:
#                 return documento, "REVISAR (sin nombre)"
#         else:
#             return documento, f"REVISAR (status {response.status_code})"

#     except Exception as e:
#         return documento, f"REVISAR (error: {e})"


# def ejecutar_consulta():
#     """Ejecuta la consulta en un hilo separado para no congelar la GUI."""
#     token = entry_token.get().strip()
#     listado = text_lista.get("1.0", tk.END).strip().splitlines()

#     if not token or not listado:
#         messagebox.showwarning("Campos requeridos", "Debes ingresar el token y al menos un documento.")
#         return

#     # Limpiar tabla
#     for row in tabla.get_children():
#         tabla.delete(row)

#     # Deshabilitar botón mientras corre
#     btn_consultar.config(state="disabled")
#     messagebox.showinfo("Consultando", "La consulta ha comenzado. Esto puede tardar varios segundos...")

#     def tarea():
#         for doc in listado:
#             doc = doc.strip()
#             if not doc:
#                 continue

#             documento, resultado = consultar_afiliado(token, doc)
#             tabla.insert("", "end", values=(documento, resultado))
#             time.sleep(random.uniform(2, 3))  # pausa entre peticiones

#         btn_consultar.config(state="normal")
#         messagebox.showinfo("Completado", "Consultas finalizadas.")

#     threading.Thread(target=tarea, daemon=True).start()


# # --- Interfaz gráfica ---
# root = tk.Tk()
# root.title("Consulta de Afiliados Horus Health")
# root.geometry("700x600")
# root.resizable(False, False)

# # Token
# frame_top = tk.Frame(root)
# frame_top.pack(pady=10)
# tk.Label(frame_top, text="Token de Autenticación:").pack(side="left")
# entry_token = tk.Entry(frame_top, width=60, show="*")
# entry_token.pack(side="left", padx=5)

# # Listado
# tk.Label(root, text="Listado de Documentos (uno por línea):").pack(anchor="w", padx=10)
# text_lista = tk.Text(root, height=10, width=80)
# text_lista.pack(padx=10, pady=5)

# # Botón
# btn_consultar = tk.Button(root, text="Consultar Afiliados", command=ejecutar_consulta, bg="#0078D4", fg="white", height=2)
# btn_consultar.pack(pady=10)

# # Resultados
# frame_tabla = tk.Frame(root)
# frame_tabla.pack(padx=10, pady=10, fill="both", expand=True)

# columns = ("documento", "resultado")
# tabla = ttk.Treeview(frame_tabla, columns=columns, show="headings", height=15)
# tabla.heading("documento", text="Documento")
# tabla.heading("resultado", text="Resultado / Nombre")

# # Scrollbar
# scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
# tabla.configure(yscroll=scroll_y.set)
# scroll_y.pack(side="right", fill="y")
# tabla.pack(fill="both", expand=True)

# # Iniciar interfaz
# root.mainloop()


import tkinter as tk
from tkinter import ttk, messagebox
import requests
import time
import random
import threading

# Diccionario de tipos de documento
TIPOS_DOC = {
    "CC": 1,  # Cédula de ciudadanía
    "TI": 2,  # Tarjeta de identidad
    "RC": 3   # Registro civil
}

BASE_URL = "https://backend.horus-health.com/api/afiliados/consultar-afiliado"


def consultar_afiliado(token, documento):
    """Consulta un afiliado individualmente y devuelve datos clave."""
    tipo = ''.join([c for c in documento if c.isalpha()]).upper()
    numero = ''.join([c for c in documento if c.isdigit()])

    tipo_id = TIPOS_DOC.get(tipo)

    if not tipo_id or not numero:
        return documento, "REVISAR (formato inválido)", "", ""

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = f"{BASE_URL}/{numero}/{tipo_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # --- Nombres (sin mostrar None) ---
            nombre = " ".join(
                filter(None, [
                    data.get("primer_nombre"),
                    data.get("segundo_nombre"),
                    data.get("primer_apellido"),
                    data.get("segundo_apellido")
                ])
            ).strip()

            # --- Estado del afiliado ---
            estado = data.get("estado_afiliado", {}).get("nombre", "REVISAR")

            # --- IPS ---
            ips = data.get("ips", {}).get("nombre", "REVISAR")

            if not nombre:
                nombre = "REVISAR (sin nombre)"

            return documento, nombre, estado, ips

        else:
            return documento, f"REVISAR (status {response.status_code})", "", ""

    except Exception as e:
        return documento, f"REVISAR (error: {e})", "", ""


def ejecutar_consulta():
    """Ejecuta la consulta en un hilo separado para no congelar la GUI."""
    token = entry_token.get().strip()
    listado = text_lista.get("1.0", tk.END).strip().splitlines()

    if not token or not listado:
        messagebox.showwarning("Campos requeridos", "Debes ingresar el token y al menos un documento.")
        return

    # Limpiar tabla
    for row in tabla.get_children():
        tabla.delete(row)

    # Deshabilitar botón mientras corre
    btn_consultar.config(state="disabled")
    messagebox.showinfo("Consultando", "La consulta ha comenzado. Esto puede tardar varios segundos...")

    def tarea():
        for doc in listado:
            doc = doc.strip()
            if not doc:
                continue

            documento, nombre, estado, ips = consultar_afiliado(token, doc)
            tabla.insert("", "end", values=(documento, nombre, estado, ips))
            time.sleep(random.uniform(2, 3))  # pausa entre peticiones

        btn_consultar.config(state="normal")
        messagebox.showinfo("Completado", "Consultas finalizadas.")

    threading.Thread(target=tarea, daemon=True).start()


# --- Interfaz gráfica ---
root = tk.Tk()
root.title("Consulta de Afiliados Horus Health")
root.geometry("900x600")
root.resizable(False, False)

# Token
frame_top = tk.Frame(root)
frame_top.pack(pady=10)
tk.Label(frame_top, text="Token de Autenticación:").pack(side="left")
entry_token = tk.Entry(frame_top, width=80, show="*")
entry_token.pack(side="left", padx=5)

# Listado
tk.Label(root, text="Listado de Documentos (uno por línea):").pack(anchor="w", padx=10)
text_lista = tk.Text(root, height=10, width=100)
text_lista.pack(padx=10, pady=5)

# Botón
btn_consultar = tk.Button(root, text="Consultar Afiliados", command=ejecutar_consulta, bg="#0078D4", fg="white", height=2)
btn_consultar.pack(pady=10)

# Resultados
frame_tabla = tk.Frame(root)
frame_tabla.pack(padx=10, pady=10, fill="both", expand=True)

columns = ("documento", "nombre", "estado", "ips")
tabla = ttk.Treeview(frame_tabla, columns=columns, show="headings", height=15)
tabla.heading("documento", text="Documento")
tabla.heading("nombre", text="Nombre completo")
tabla.heading("estado", text="Estado afiliado")
tabla.heading("ips", text="IPS")

# Scrollbar
scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
tabla.configure(yscroll=scroll_y.set)
scroll_y.pack(side="right", fill="y")
tabla.pack(fill="both", expand=True)

# Iniciar interfaz
root.mainloop()
