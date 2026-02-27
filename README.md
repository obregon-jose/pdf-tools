# 📄 RADICOR - Sistema de Radicación y Procesamiento de Documentos

**Versión 1.0.0** | *Sistema de automatización para radicación, procesamiento de PDFs y validación de datos*

**Desarrollador**: José Obregón | obregonjose812@gmail.com | +57 3168960724

---

## ¿Qué es RADICOR?

Sistema desktop para automatizar tareas de:
- Procesamiento masivo de PDFs (unir, dividir, eliminar páginas)
- Radicación de documentos con patrones automáticos
- Validación de datos (emails, carnets, etc.)
- Integración con APIs (Horus, Web PAI)

---

## 🚀 Herramientas Disponibles

**PDF**
- Unir PDFs - Combina múltiples archivos
- Dividir PDF - Separa en páginas individuales
- Eliminar Páginas - Remueve páginas específicas
- Multiplicar Soportes - Clona con diferentes nombres

**RADICACIÓN**
- Unir Grupos - Agrupa PDFs por patrón de nombre
- Multiplicar Soportes CRC - Copias masivas con nombres
- Separar Órdenes OPF - Divide órdenes individuales
- Verificar Soportes - Valida integridad
- Actualizar Facturas - Modifica números de factura

**DATOS**
- Validar Emails - Verifica direcciones de correo
- Carnet Virtual - Gestión de carnets
- Catálogo Vacunas - Base de vacunación
- Descargar Horus - Integración con Horus API
- Web PAI - Herramientas web

---

## 💻 Instalación

**Requisitos**: Windows 10+, Python 3.8+

```bash
# 1. Clonar repositorio
git clone <url>
cd radicor

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

**O usar el ejecutable**: `RADICOR.exe` (si está disponible)

---

## 📁 Estructura del Proyecto

```
radicor/
├── main.py              # Punto de entrada
├── app_store.py         # Gestión de tokens
├── core/                # Núcleo (app, config, storage, utils)
├── ui/                  # Interfaz gráfica
├── tools/               # Herramientas (pdf_merge, pdf_split, etc.)
├── data/                # Configuración (config.json)
└── assets/              # Recursos (iconos)
```

---

## ⚙️ Configuración

Archivo: `data/config.json`

```json
{
    "theme": "light",           // o "dark"
    "color_theme": "blue",      // o "green", "red"
    "last_tool": "Unir PDFs"
}
```

Se guarda automáticamente al cerrar la app.

---

## 🛠️ Crear Nueva Herramienta

1. Crear archivo en `tools/mi_herramienta.py`
2. Usar este template:

```python
import customtkinter as ctk
from tkinter import filedialog, messagebox

class MiHerramientaApp:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        # Construir interfaz
        btn = ctk.CTkButton(self.parent, text="Procesar", command=self.process)
        btn.pack(pady=10)
    
    def process(self):
        try:
            # Tu lógica aquí
            messagebox.showinfo("Éxito", "Completado")
        except Exception as e:
            messagebox.showerror("Error", str(e))
```

3. Registrar en `tools/tools_registry.py`:

```python
from tools.mi_herramienta import MiHerramientaApp

TOOLS_REGISTRY = [
    # ... existentes ...
    {
        "name": "Mi Herramienta",
        "description": "Descripción breve",
        "category": "PDF",  # o "RADICACIÓN" o "DATOS"
        "class": MiHerramientaApp,
    }
]
```

---

## 🐛 Solución de Problemas

**No inicia / ModuleNotFoundError**
```bash
pip install -r requirements.txt --force-reinstall
```

**Interfaz se congela**
- Usa PDFs más pequeños
- Cierra otras apps pesadas

**No guarda configuración**
- Verifica permisos en carpeta `data/`
- Elimina `data/config.json` y reinicia

---

## 📚 Dependencias Principales

```
PyMuPDF==1.23.0          # PDFs
customtkinter==5.2.0     # UI moderna
Pillow==10.0.0           # Imágenes
requests==2.31.0         # APIs HTTP
validators==0.20.0       # Validaciones
```

---

**RADICOR v1.0.0** | José Obregón | obregonjose812@gmail.com
