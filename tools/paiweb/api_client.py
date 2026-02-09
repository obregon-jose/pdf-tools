"""Cliente para interactuar con la API de PAIWeb"""
import requests
import urllib3
from config import API_SEARCH_URL, API_CARNET_URL, API_VACCINES_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PAIWebAPIClient:
    """Cliente para la API de PAIWeb"""
    
    def __init__(self, token):
        self.session = requests.Session()
        self.session.cookies.set("access_token", token)
        self.headers = {"Content-Type": "application/json"}
    
    def validar_token(self):
        """Valida si el token es válido"""
        try:
            res = requests.get(
                "https://paiwebservices.paiweb.gov.co:8081/api/Login/ValidateToken",
                cookies={"access_token": self.session.cookies.get("access_token")},
                timeout=10, verify=False
            )
            return res.status_code == 200 and res.json() is True
        except Exception:
            return False
    
    def buscar_paciente(self, numero_documento):
        """Busca un paciente por número de documento"""
        payload = {
            "size": 10,
            "totalElements": 0,
            "totalPages": 0,
            "pageNumber": 0,
            "data": {
                "numeroIdentificacion": numero_documento,
                "tipoDocumento": {},
                "numeroIdentificacionCuidador": "",
                "type": "basic"
            }
        }
        
        try:
            res = self.session.post(API_SEARCH_URL, json=payload, headers=self.headers, timeout=20, verify=False)
            if res.status_code == 200:
                jres = res.json()
                if jres and jres.get('data') and len(jres.get('data', [])) > 0:
                    return jres['data'][0]
            return None
        except Exception as e:
            raise Exception(f"Error al buscar paciente: {e}")
    
    def obtener_vacunas(self, paciente_id):
        """Obtiene las vacunas de un paciente"""
        try:
            vaccines_url = f"{API_VACCINES_URL}/{paciente_id}/aplicaciones"
            res = self.session.get(vaccines_url, timeout=20, verify=False)
            if res.status_code == 200:
                vaccines = res.json()
                if isinstance(vaccines, list):
                    return vaccines
            return []
        except Exception as e:
            raise Exception(f"Error al obtener vacunas: {e}")
    
    def descargar_carnet(self, fecha_nacimiento, tipo_documento, numero_documento, nombre_completo):
        """Descarga el carnet de vacunación en PDF"""
        payload = {
            "fechaNacimiento": fecha_nacimiento,
            "tipoDocumento": tipo_documento,
            "numeroDocumento": numero_documento,
            "nombreCompleto": nombre_completo
        }
        
        try:
            res = self.session.post(API_CARNET_URL, json=payload, timeout=20, verify=False)
            if res.status_code == 200 and res.headers.get("Content-Type", "").startswith("application/pdf"):
                return res.content
            return None
        except Exception as e:
            raise Exception(f"Error al descargar carnet: {e}")