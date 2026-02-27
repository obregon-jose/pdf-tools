from tools.pdf_splitter import PDFSplitterApp
from ALGORITMOS_BASE.pdf_splitter2 import PDFSplitterApp2
from tools.pdf_page_deleter import PDFPageDeleterApp
from tools.horus import HorusApp
from tools.validate_emails import ValidateEmailApp
from tools.pdf_merge import PDFMergerApp
from tools.pdf_merge_group import PDFMergerGroupApp
from tools.pdf_multiplier_support import PDFMultiplierSupportApp
from tools.pdf_split_orders import PDFSplitOrdersApp
from tools.carnet_virtual import CarnetVirtualApp
from tools.pdf_verifier_supports import PDFVerifierSupportsApp
from tools.pdf_factura_updater import InvoiceNumberUpdaterApp

TOOLS_REGISTRY = [

    {
        "name": "Unir PDFs",
        "description": "Une múltiples PDFs en uno solo archivo segun seleccion.",
        "category": "PDF",
        "class": PDFMergerApp,
    },
    {
        "name": "Unir grupos de PDFs",
        "description": "Une grupos de archivos PDF de acuerdo a nombres similares.",
        "category": "RADICACIÓN",
        "class": PDFMergerGroupApp,
    },
    {
        "name": "Dividir PDF",
        "description": "Divide un archivo PDF en paginas separadas.",
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
        "description": "Multiplica un archivo PDF con diferentes nombres.",
        "category": "RADICACIÓN",
        "class": PDFMultiplierSupportApp,
    },
    {
        "name": "Separar Ordenes OPF",
        "description": "Divide un archivo PDF de órdenes OPF en archivos individuales.",
        "category": "RADICACIÓN",
        "class": PDFSplitOrdersApp,
    },
    {
        "name": "Validar correos",
        "description": "Valida si una lista de correos electrónicos tienen un formato válido.",
        "category": "Revisión",
        "class": ValidateEmailApp,
    },
    {
        "name": "HORUS",
        "description": "Consulta pacientes en HORUS a partir del detalle de carga.",
        "category": "Revisión",
        "class": HorusApp,
    },
        # {
    #     "name": "Contar Páginas",
    #     "description": "Cuenta el número de páginas totales eun una carpeta de archivos PDF.",
    #     "category": "Revisión",
    #     "class": BaseTool,
    # },
    {
        "name": "Actualizar # Factura",
        "description": "Actualiza masivamente el numero de factura en los archivos de soporte OPF y CRC.",
        "category": "RADICACIÓN",
        "class": InvoiceNumberUpdaterApp,
    },
    {
        "name": "Comparar Soportes",
        "description": "Revisa que los archivos de soporte CRC y OPF coincidan con los documentos del detalle de cargue",
        "category": "RADICACIÓN",
        "class": PDFVerifierSupportsApp,
    },
    {
        "name": "Extraer paginas de PDF",
        "description": "",
        "category": "PDF",
        "class": PDFSplitterApp2,
    },
    {
        "name": "Base Carnet Virtual",
        "description": "Genera el archivo masivo con las vacunas aplicadas listo para cargar al sistema",
        "category": "VAXTHERA",
        "class": CarnetVirtualApp,
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
    # }
]
