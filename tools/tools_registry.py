from tools.base import BaseTool
from tools.pdf_splitter import PDFSplitterApp

TOOLS_REGISTRY = [
    {
        "name": "Contar Páginas",
        "description": "Cuenta el número de páginas totales eun una carpeta de archivos PDF.",
        "category": "Revisión",
        "class": BaseTool,
    },
    {
        "name": "HORUS",
        "description": "Consulta de afiliados en HORUS a partir del detalle de carga.",
        "category": "Revisión",
        "class": BaseTool,
    },
    {
        "name": "Unir PDFs",
        "description": "Une múltiples archivos PDF en uno solo de acuerdo a su nombre.",
        "category": "PDF",
        "class": BaseTool,
    },
    {
        "name": "Dividir PDFs",
        "description": "Divide un archivo PDF en múltiples archivos según el número de páginas.",
        "category": "PDF",
        "class": PDFSplitterApp,
    },
    {
        "name": "Separar Registros",
        "description": "Multiplica una hoja de registros por cada paciente individual.",
        "category": "Registros",
        "class": BaseTool,
    },
    {
        "name": "Validar correos",
        "description": "Valida si una lista de correos electrónicos son válidos o no.",
        "category": "Revisión",
        "class": BaseTool,
    },
    {
        "name": "Actualizar # Factura",
        "description": "Permite insertar o actualizar el número de factura en un conjunto de archivos PDF.",
        "category": "PDF",
        "class": BaseTool,
    },
    {
        "name": "Separar Ordenes",
        "description": "Divide un archivo PDF de órdenes en múltiples archivos individuales por paciente.",
        "category": "PDF",
        "class": BaseTool,
    },
    {
        "name": "Revisar RIPS",
        "description": "Permite revisar los RIPS generados por la plataforma.",
        "category": "Revisión",
        "class": BaseTool,
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
