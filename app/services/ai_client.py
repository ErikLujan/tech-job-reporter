import logging
from typing import cast

import bleach
from google import genai

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lista blanca estricta para sanitizar salida del LLM — solo texto plano permitido
_ALLOWED_TAGS: list[str] = []
_ALLOWED_ATTRIBUTES: dict[str, list[str]] = {}


class AIClient:
    """
    Servicio encargado de interactuar con la API de Google Gemini
    para generar análisis de mercado basados en los datos extraídos.
    """

    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def _sanitize_llm_output(self, text: str) -> str:
        """
        Sanitiza la salida del LLM para prevenir XSS/inyección al embeber en emails HTML.
        Usa bleach con lista blanca estricta: sin etiquetas, sin atributos — solo texto plano.
        """
        if not text:
            return ""
        # bleach.clean con tags vacíos elimina todo HTML y escapa entidades
        return bleach.clean(
            text, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES, strip=True
        )

    def generar_resumen(self, datos_analisis: dict[str, object]) -> str:
        """
        Toma las estadísticas de la semana y arma un prompt para que
        la IA redacte un resumen ejecutivo.
        """
        if not datos_analisis.get("hay_datos"):
            return "El mercado no presentó suficiente movimiento esta semana para generar un análisis."

        try:
            # Casteamos la estructura conocida del output de DataAnalyzer
            top_tecnologias = cast(
                list[dict[str, str | int]], datos_analisis["top_tecnologias"]
            )
            dream_jobs_list = cast(
                list[dict[str, str]], datos_analisis.get("dream_jobs", [])
            )

            top_techs = ", ".join(
                [f"{t['nombre']} ({t['cantidad']})" for t in top_tecnologias]
            )
            dream_jobs = ", ".join([j["titulo"] for j in dream_jobs_list])

            prompt = f"""
            Actúa como un Headhunter IT Senior analizando el mercado laboral actual.
            Aquí tenés los datos extraídos de esta semana:
            - Top 10 tecnologías más demandadas: {top_techs}
            - Títulos de ofertas destacadas (Backend): {dream_jobs}

            Redactá un breve resumen ejecutivo (máximo 3 oraciones) sobre las tendencias de esta semana
            para un desarrollador Backend. Sé directo, profesional e insightful.
            No uses saludos ni despedidas, andá directo al análisis.
            """

            logger.info("Solicitando análisis de mercado a Gemini AI...")
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            logger.info("Resumen de IA generado exitosamente.")

            # Sanitizamos antes de devolver — la salida del LLM es entrada no confiable
            # El nuevo SDK devuelve response.text directamente
            response_text = response.text or ""
            return self._sanitize_llm_output(response_text.strip())

        except Exception as e:  # noqa: BLE001 — degradación elegante: fallback ante cualquier error de IA
            logger.error("Fallo no crítico al contactar a la API de Gemini: %s", e)
            return "El análisis inteligente del mercado no se pudo generar en esta ejecución."
