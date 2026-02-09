"""Analizador de esquemas de vacunación"""
from config import ESQUEMAS_VACUNACION
from utils import normalizar_biologico


def vacuna_coincide(vacuna_paciente, vacuna_esquema):
    """Verifica si una vacuna del paciente coincide con una del esquema"""
    biologico_paciente = normalizar_biologico(vacuna_paciente.get("biologico", ""))
    dosis_paciente = vacuna_paciente.get("dosis", "").strip()
    
    biologico_match = False
    for bio_esquema in vacuna_esquema["biologico"]:
        bio_esquema_norm = normalizar_biologico(bio_esquema)
        if bio_esquema_norm in biologico_paciente or biologico_paciente in bio_esquema_norm:
            biologico_match = True
            break
    
    if not biologico_match:
        return False
    
    return dosis_paciente in vacuna_esquema["dosis"]


def analizar_esquema_vacunacion(vacunas_paciente):
    """Analiza las vacunas del paciente y determina qué esquemas ha completado"""
    resultado = {}
    
    for esquema_key, esquema_data in ESQUEMAS_VACUNACION.items():
        vacunas_requeridas = esquema_data["vacunas"]
        vacunas_encontradas = []
        vacunas_faltantes = []
        
        for vacuna_req in vacunas_requeridas:
            encontrada = False
            for vacuna_pac in vacunas_paciente:
                if vacuna_coincide(vacuna_pac, vacuna_req):
                    encontrada = True
                    vacunas_encontradas.append({
                        "biologico": vacuna_pac.get("biologico"),
                        "dosis": vacuna_pac.get("dosis"),
                        "fecha": vacuna_pac.get("fechaAplicacion")
                    })
                    break
            
            if not encontrada:
                vacunas_faltantes.append({
                    "biologico": vacuna_req["biologico"][0],
                    "dosis": vacuna_req["dosis"][0]
                })
        
        total_requeridas = len(vacunas_requeridas)
        total_encontradas = len(vacunas_encontradas)
        porcentaje = int((total_encontradas / total_requeridas) * 100) if total_requeridas > 0 else 0
        
        # Verificar esquemas incluidos
        incluye_completos = True
        if "incluye" in esquema_data:
            for esquema_incluido in esquema_data["incluye"]:
                if esquema_incluido in resultado:
                    es_opcional = ESQUEMAS_VACUNACION[esquema_incluido].get("opcional", False)
                    if not es_opcional and not resultado[esquema_incluido]["completo"]:
                        incluye_completos = False
                        break
        
        completo = porcentaje == 100 and incluye_completos
        
        resultado[esquema_key] = {
            "nombre": esquema_data["nombre"],
            "total_requeridas": total_requeridas,
            "total_encontradas": total_encontradas,
            "porcentaje": porcentaje,
            "completo": completo,
            "opcional": esquema_data.get("opcional", False),
            "vacunas_encontradas": vacunas_encontradas,
            "vacunas_faltantes": vacunas_faltantes
        }
    
    return resultado