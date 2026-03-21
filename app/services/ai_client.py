import logging
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIClient:
    """
    Servicio encargado de interactuar con la API de Google Gemini 
    para generar análisis de mercado basados en los datos extraídos.
    """

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generar_resumen(self, datos_analisis: dict) -> str:
        """
        Toma las estadísticas de la semana y arma un prompt para que 
        la IA redacte un resumen ejecutivo.
        """
        if not datos_analisis.get("hay_datos"):
            return "El mercado no presentó suficiente movimiento esta semana para generar un análisis."

        try:
            top_techs = ", ".join([f"{t['nombre']} ({t['cantidad']})" for t in datos_analisis['top_tecnologias']])
            dream_jobs = ", ".join([j['titulo'] for j in datos_analisis.get('dream_jobs', [])])

            prompt = f"""
            Actúa como un Headhunter IT Senior analizando el mercado laboral actual.
            Aquí tienes los datos extraídos de esta semana:
            - Top 10 tecnologías más demandadas: {top_techs}
            - Títulos de ofertas destacadas (Backend): {dream_jobs}

            Redacta un breve resumen ejecutivo (máximo 3 oraciones) sobre las tendencias de esta semana 
            para un desarrollador Backend. Sé directo, profesional e insightful. 
            No uses saludos ni despedidas, ve directo al análisis.
            """

            logger.info("Solicitando análisis de mercado a Gemini AI...")
            respuesta = self.model.generate_content(prompt)
            logger.info("Resumen de IA generado exitosamente.")
            
            return respuesta.text.strip()

        except Exception as e:
            logger.error(f"Fallo no crítico al contactar a la API de Gemini: {e}")
            return "El análisis inteligente del mercado no se pudo generar en esta ejecución."