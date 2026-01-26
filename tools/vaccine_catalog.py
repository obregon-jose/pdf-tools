"""
Catálogo de vacunas para el procesador de datos de vacunación.
Este archivo contiene la configuración de todas las vacunas soportadas.
"""

# Diccionario de vacunas con su información completa
VACCINE_CATALOG = {
    'INFLUVAC': {
        'keywords': ['INFLUVAC', 'INFLUENZA'],
        'display_name': 'INFLUVAC',
        'description': 'la influenza (INFLUVAC)',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#4CAF50',
        'lote_ejemplo': 'K17'
    },
    
    'VPH': {
        'keywords': ['VPH', 'GARDASIL', 'PAPILOMA'],
        'display_name': 'GARDASIL 9',
        'description': 'el Virus del Papiloma Humano (GARDASIL 9)',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#2196F3',
        'lote_ejemplo': 'Y000435'
    },
    
    'NEUMO': {
        'keywords': ['NEUMO', 'NEUMOCOCO', 'PNEUMO', 'NEUMONIA'],
        'display_name': 'NEUMOCOCO',
        'description': 'el neumococo (PREVENAR 15)',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#FF9800',
        'lote_ejemplo': 'NEUMO23'
    },
    
    'HEPATITIS_B': {
        'keywords': ['HEPATITIS B', 'HEPATITIS-B', 'HEP B', 'HB', 'HEPATITIS'],
        'display_name': 'HEPATITIS B',
        'description': 'la hepatitis B',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#9C27B0',
        'lote_ejemplo': 'HB2024'
    },
    
    'TETANOS': {
        'keywords': ['TETANOS', 'TÉTANOS', 'TD', 'TDAP', 'ANTITETANICA'],
        'display_name': 'TÉTANOS',
        'description': 'el tétanos',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#F44336',
        'lote_ejemplo': 'TD2024'
    },
    
    'COVID': {
        'keywords': ['COVID', 'COVID-19', 'COVID19', 'SARS-COV-2', 'CORONAVIRUS'],
        'display_name': 'COVID-19',
        'description': 'el COVID-19',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#00BCD4',
        'lote_ejemplo': 'COV2024'
    },
    
    'FIEBRE_AMARILLA': {
        'keywords': ['FIEBRE AMARILLA', 'YELLOW FEVER', 'FA', 'F.AMARILLA'],
        'display_name': 'FIEBRE AMARILLA',
        'description': 'la fiebre amarilla',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#FFEB3B',
        'lote_ejemplo': 'FA2024'
    },
    
    'SARAMPION': {
        'keywords': ['SARAMPION', 'SARAMPIÓN', 'MEASLES', 'SRP', 'TRIPLE VIRAL'],
        'display_name': 'SARAMPIÓN',
        'description': 'el sarampión',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#E91E63',
        'lote_ejemplo': 'SRP2024'
    },
    
    'VARICELA': {
        'keywords': ['VARICELA', 'CHICKENPOX'],
        'display_name': 'VARICELA',
        'description': 'la varicela',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#3F51B5',
        'lote_ejemplo': 'VAR2024'
    },
    
    'MENINGITIS': {
        'keywords': ['MENINGITIS', 'MENINGOCOCO', 'MENINGOCOCICA'],
        'display_name': 'MENINGITIS',
        'description': 'la meningitis',
        'default_arm': 'IZQUIERDO',
        'jeringa': 'JERINGA PRELLENADA',
        'color': '#795548',
        'lote_ejemplo': 'MEN2024'
    }
}