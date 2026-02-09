"""Configuración y constantes del sistema"""
from pathlib import Path

# URLs de la API
API_SEARCH_URL = "https://paiwebservices.paiweb.gov.co:8081/api/v2/Paciente/GetList"
API_CARNET_URL = "https://paiwebservices.paiweb.gov.co:8081/api/Carnet"
API_VACCINES_URL = "https://paiwebservices.paiweb.gov.co:8081/api/resumen/paciente"

# Carpeta de descargas por defecto
DOWNLOADS_FOLDER = str(Path.home() / "Downloads") if (Path.home() / "Downloads").exists() else str(Path.home() / "Descargas")

# Opciones de formato de nombre de archivo
FILENAME_OPTIONS = [
    "Nombre Completo",
    "Nombre Completo + Documento",
    "Nombre Completo + Tipo + Documento",
    "Nombre Completo + Tipo_Documento"
]

# Diccionario de esquemas de vacunación PAI Colombia
ESQUEMAS_VACUNACION = {
    "Recién nacido": {
        "nombre": "Recién nacido",
        "opcional": True,
        "vacunas": [
            {"biologico": ["BCG"], "dosis": ["Única", "Unica"]},
            {"biologico": ["Hepatitis B Pediatrica", "Hepatitis B Pediátrica", "Hepatitis B"], "dosis": ["Única", "Unica", "Primera"]}
        ]
    },
    "2 meses": {
        "nombre": "2 meses",
        "opcional": False,
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente"], "dosis": ["Primera"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio"], "dosis": ["Primera"]},
            {"biologico": ["Rotavirus"], "dosis": ["Primera"]},
            {"biologico": ["Neumococo", "Neumococo Conjugado", "Neumococo 13valente", "Neumococo 13 valente", "Neumococo Conjugado 10valente"], "dosis": ["Primera"]}
        ]
    },
    "4 meses": {
        "nombre": "4 meses",
        "opcional": False,
        "incluye": ["2 meses", "Recién nacido"],
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente"], "dosis": ["Segunda", "Segunda "]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio"], "dosis": ["Segunda", "Segunda "]},
            {"biologico": ["Rotavirus"], "dosis": ["Segunda", "Segunda "]},
            {"biologico": ["Neumococo", "Neumococo Conjugado", "Neumococo 13valente", "Neumococo 13 valente", "Neumococo Conjugado 10valente"], "dosis": ["Segunda", "Segunda "]}
        ]
    },
    "6 meses": {
        "nombre": "6 meses",
        "opcional": False,
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente"], "dosis": ["Tercera"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio"], "dosis": ["Tercera"]},
            {"biologico": ["INFLUENZA", "INFLUENZA TRIVALENTE PEDIÁTRICA", "INFLUENZA TRIVALENTE PEDIATRICA", "Influenza"], "dosis": ["Primera"]}
        ]
    },
    "7 meses": {
        "nombre": "7 meses",
        "opcional": False,
        "vacunas": [
            {"biologico": ["INFLUENZA", "INFLUENZA TRIVALENTE PEDIÁTRICA", "INFLUENZA TRIVALENTE PEDIATRICA", "Influenza"], "dosis": ["Segunda", "Segunda "]}
        ]
    },
    "12 meses": {
        "nombre": "12 meses (1 año)",
        "opcional": False,
        "vacunas": [
            {"biologico": ["Triple Viral", "SRP", "Triple viral"], "dosis": ["Primera"]},
            {"biologico": ["Fiebre Amarilla", "FA"], "dosis": ["Única", "Unica"]},
            {"biologico": ["Hepatitis A", "Hepatitis A Pediátrica", "Hepatitis A Pediatrica"], "dosis": ["Única", "Unica"]},
            {"biologico": ["Neumococo", "Neumococo Conjugado", "Neumococo 13valente", "Neumococo 13 valente", "Neumococo Conjugado 10valente"], "dosis": ["Refuerzo"]},
            {"biologico": ["Varicela"], "dosis": ["Primera"]}
        ]
    },
    "18 meses": {
        "nombre": "18 meses (1 año y medio)",
        "opcional": False,
        "vacunas": [
            {"biologico": ["Pentavalente PAI", "Pentavalente", "DPT"], "dosis": ["Primer Refuerzo", "Refuerzo"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio Oral", "VOP", "Antipolio"], "dosis": ["Primer Refuerzo", "Refuerzo"]},
            {"biologico": ["Triple Viral", "SRP", "Triple viral"], "dosis": ["Refuerzo"]}
        ]
    },
    "5 años": {
        "nombre": "5 años",
        "opcional": False,
        "vacunas": [
            {"biologico": ["DPT"], "dosis": ["Segundo Refuerzo", "Refuerzo"]},
            {"biologico": ["Antipolio Inactivo", "Antipolio Inactivo (VIP)", "VIP", "Antipolio Oral", "VOP", "Antipolio"], "dosis": ["Segundo Refuerzo", "Refuerzo"]}
        ]
    },
    "9 años (VPH)": {
        "nombre": "9 años (VPH - niñas)",
        "opcional": False,
        "vacunas": [
            {"biologico": ["VPH", "Virus Papiloma Humano", "Virus del Papiloma Humano"], "dosis": ["Única", "Unica", "Primera"]}
        ]
    }
}

# Colores de la UI
COLORS = {
    "primary": "#14b97d",
    "secondary": "#476cb2",
    "success": "#27ae60",
    "warning": "#fbc531",
    "error": "#e74c3c",
    "info": "#1f6feb",
    "text": "#7f8c8d",
    "bg_dark": "#0a0a0a",
    "bg_medium": "#1a1a1a",
    "bg_light": "#2b2b2b"
}