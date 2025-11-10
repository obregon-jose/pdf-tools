import os
import json

APP_NAME = "Su Factura"
VERSION = "1.0.0"


# AUTOR = "José Obregón"
# EMAIL_SOPORTE = "obregonjose812@gmail.com"
# WHATSAPP_SOPORTE = "+57 3168960724"

# ## CONFIGURACION DE LA APP
# COLOR_FONDO = "#FFFFFF"
# COLOR_TEXTO = "#000000"
# COLOR_BARRA_SUPERIOR = "#1f2329"
# COLOR_MENU_LATERAL = "#2a3138"
# COLOR_CUERPO_PRINCIPAL = "#f1faff"
# COLOR_MENU_CURSOR_ENCIMA = "#2f88c5"

# HABILITAR_BACKUP = True
# RUTA_BACKUP = "./backups/"


# TAMAÑO_WINDOW = "985x540"
# TAMANO_MINIMO_WINDOW = (985, 540)
DEFAULT_CONFIG = {
    "theme": "light",
    "color_theme": "blue",
    "last_tool": "Calculadora"
}

ICONO_APP = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")



def load_config():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Si el archivo está vacío o roto, lo repara
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
