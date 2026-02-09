"""Funciones utilitarias"""
import os
import re
from datetime import datetime


def nombre_completo(datos):
    """Genera el nombre completo del paciente"""
    partes = [
        datos.get("primerNombre", "").strip(),
        datos.get("segundoNombre", "").strip(),
        datos.get("primerApellido", "").strip(),
        datos.get("segundoApellido", "").strip()
    ]
    return " ".join([p for p in partes if p]).upper().strip()


def limpiar_nombre_archivo(nombre):
    """Limpia caracteres no permitidos en nombres de archivo"""
    base, ext = os.path.splitext(nombre)
    permitido = re.compile(r"[^\wÁÉÍÓÚáéíóúÑñ\s]+", re.UNICODE)
    base_limpio = permitido.sub("", base).strip()[:80]
    return base_limpio + ext


def generar_nombre_archivo(nombre_full, tdoc, ndoc, formato_idx):
    """Genera el nombre del archivo según el formato seleccionado"""
    if formato_idx == 0:
        nombre = f"{nombre_full}.pdf"
    elif formato_idx == 1:
        nombre = f"{nombre_full} {ndoc}.pdf"
    elif formato_idx == 2:
        nombre = f"{nombre_full} {tdoc}{ndoc}.pdf"
    else:
        nombre = f"{nombre_full} {tdoc}_{ndoc}.pdf"
    return limpiar_nombre_archivo(nombre)


def resolver_ruta(user_input, default_folder):
    """Resuelve la ruta de destino para guardar archivos"""
    user_input = user_input.strip()
    if not user_input:
        return default_folder
    if user_input.startswith('/') or user_input.startswith('\\') or not os.path.isabs(user_input):
        carpeta = os.path.join(default_folder, user_input.lstrip('/\\'))
    else:
        carpeta = user_input
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def format_date(date_str):
    """Convierte fecha ISO a formato dd/mm/yyyy"""
    if not date_str:
        return "N/A"
    try:
        date_part = date_str[:10]
        date_obj = datetime.strptime(date_part, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else "N/A"


def normalizar_biologico(biologico):
    """Normaliza el nombre del biológico"""
    if not biologico:
        return ""
    normalizado = biologico.lower().strip()
    normalizado = re.sub(r'[áäâà]', 'a', normalizado)
    normalizado = re.sub(r'[éëêè]', 'e', normalizado)
    normalizado = re.sub(r'[íïîì]', 'i', normalizado)
    normalizado = re.sub(r'[óöôò]', 'o', normalizado)
    normalizado = re.sub(r'[úüûù]', 'u', normalizado)
    normalizado = re.sub(r'[\(\)]', '', normalizado)
    return normalizado