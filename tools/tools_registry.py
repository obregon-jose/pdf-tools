from tools.base import BaseTool
from tools.pdf_splitter import PDFSplitterApp
# from tools.pdf_splitter2 import PDFSplitterApp2
from tools.pdf_page_deleter import PDFPageDeleterApp
from tools.horus import HorusApp
from tools.validate_emails import ValidateEmailApp
from tools.pdf_merge import PDFMergerApp
from tools.pdf_merge_group import PDFMergerGroupApp
from tools.pdf_multiplier_support import PDFMultiplierSupportApp
from tools.pdf_split_orders import PDFSplitOrdersApp

TOOLS_REGISTRY = [

    {
        "name": "Unir PDFs",
        "description": "Une múltiples archivos PDF seleccionados en uno solo.",
        "category": "PDF",
        "class": PDFMergerApp,
    },
    {
        "name": "Unir grupos de PDFs",
        "description": "Une grupos de archivos PDF de acuerdo al nombres similares.",
        "category": "PDF",
        "class": PDFMergerGroupApp,
    },
    {
        "name": "Dividir PDF",
        "description": "Divide un archivo PDF en múltiples archivos según el número de páginas.",
        "category": "PDF",
        "class": PDFSplitterApp,
    },
    {
        "name": "Eliminar paginas de pdf",
        "description": "Permite eliminar páginas específicas de un archivo PDF.",
        "category": "PDF",
        "class": PDFPageDeleterApp,
    },
    {
        "name": "Multiplicar Soportes CRC",
        "description": "Multiplica un archivo PDF con diferentes nombres de soporte.",
        "category": "FACTURA",
        "class": PDFMultiplierSupportApp,
    },
    {
        "name": "Separar Ordenes OPF",
        "description": "Divide un archivo PDF de órdenes OPF en múltiples archivos individuales por paciente.",
        "category": "FACTURA",
        "class": PDFSplitOrdersApp,
    },
    {
        "name": "Validar correos",
        "description": "Valida si una lista de correos electrónicos son válidos o no.",
        "category": "Revisión",
        "class": ValidateEmailApp,
    },
    {
        "name": "HORUS",
        "description": "Consulta de afiliados en HORUS a partir del detalle de carga.",
        "category": "Revisión",
        "class": HorusApp,
    },
        # {
    #     "name": "Contar Páginas",
    #     "description": "Cuenta el número de páginas totales eun una carpeta de archivos PDF.",
    #     "category": "Revisión",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "Actualizar # Factura",
    #     "description": "Permite insertar o actualizar el número de factura en un conjunto de archivos PDF.",
    #     "category": "PDF",
    #     "class": BaseTool,
    # },
    # {
    #     "name": "Separar Ordenes 2",
    #     "description": "Divide un archivo PDF en múltiples archivos individuales por paciente.",
    #     "category": "PDF",
    #     "class": PDFSplitterApp2,
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
