from tools.base import BaseTool
from tools.pdf_splitter import PDFSplitterApp
from tools.pdf_page_deleter import PDFPageDeleterApp
from tools.horus import Horus

TOOLS_REGISTRY = [
    # {
    #     "name": "Contar Páginas",
    #     "description": "Cuenta el número de páginas totales eun una carpeta de archivos PDF.",
    #     "category": "Revisión",
    #     "class": BaseTool,
    # },
    {
        "name": "HORUS",
        "description": "Consulta de afiliados en HORUS a partir del detalle de carga.",
        "category": "Revisión",
        "class": Horus,
    },
    # {
    #     "name": "Unir PDFs",
    #     "description": "Une múltiples archivos PDF en uno solo de acuerdo a su nombre.",
    #     "category": "PDF",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "Dividir PDFs",
    #     "description": "Divide un archivo PDF en múltiples archivos según el número de páginas.",
    #     "category": "PDF",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "Separar Registros",
    #     "description": "Multiplica una hoja de registros por cada paciente individual.",
    #     "category": "Registros",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "Validar correos",
    #     "description": "Valida si una lista de correos electrónicos son válidos o no.",
    #     "category": "Revisión",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "Actualizar # Factura",
    #     "description": "Permite insertar o actualizar el número de factura en un conjunto de archivos PDF.",
    #     "category": "PDF",
    #     "class": BaseTool,
    # },
    {
        "name": "Separar Ordenes",
        "description": "Divide un archivo PDF de órdenes en múltiples archivos individuales por paciente.",
        "category": "PDF",
        "class": PDFSplitterApp,
    },
    {
        "name": "Eliminar paginas de un archivo pdf",
        "description": "Permite eliminar páginas específicas de un archivo PDF.",
        "category": "PDF",
        "class": PDFPageDeleterApp,
    },
    # {
    #     "name": "",
    #     "description": "",
    #     "category": "",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "",
    #     "description": "",
    #     "category": "",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "",
    #     "description": "",
    #     "category": "",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "",
    #     "description": "",
    #     "category": "",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "",
    #     "description": "",
    #     "category": "",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "",
    #     "description": "",
    #     "category": "",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "",
    #     "description": "",
    #     "category": "",
    #     "class": BaseTool,
    # }
]
