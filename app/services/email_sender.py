import logging
import resend
import os

from jinja2 import Environment, FileSystemLoader
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Servicio encargado de renderizar plantillas HTML con Jinja2 
    y enviar correos electrónicos utilizando la API de Resend.
    """

    def __init__(self):
        """Inicializa el SDK de Resend y el entorno de plantillas Jinja2."""
        resend.api_key = settings.RESEND_API_KEY
        
        self.entorno_jinja = Environment(loader=FileSystemLoader("app/templates"))

    def enviar_reporte(self, datos_analisis: dict, ruta_pdf: str | None = None) -> None:
        """
        Toma los datos analizados, renderiza el HTML y dispara el correo.
        Si no hay datos, dispara una alerta de texto plano.
        
        **Args:**
        - datos_analisis (dict): El diccionario devuelto por DataAnalyzer.
        - ruta_pdf (str | None): Ruta local al archivo PDF generado, opcional.
        """

        if not datos_analisis.get("hay_datos"):
            logger.info("No hay datos para reportar. Enviando alerta simple...")
            self._enviar_alerta_sin_datos()
            return

        try:
            template = self.entorno_jinja.get_template("email_body.html")
            html_renderizado = template.render(
                total_ofertas=datos_analisis["total_ofertas"],
                top_tecnologias=datos_analisis["top_tecnologias"],
                dream_jobs=datos_analisis.get("dream_jobs", [])
            )

            parametros_email = {
                "from": settings.EMAIL_SENDER,
                "to": [settings.EMAIL_RECIPIENT],
                "subject": f"🔥 Tech Job Report: {datos_analisis['total_ofertas']} nuevas ofertas",
                "html": html_renderizado
            }

            if ruta_pdf:
                try:
                    with open(ruta_pdf, "rb") as f:
                        contenido_pdf = f.read()
                        
                    parametros_email["attachments"] = [
                        {
                            "filename": "Tech_Report_Semanal.pdf",
                            "content": list(contenido_pdf)
                        }
                    ]
                except IOError as e:
                    logger.error(f"No se pudo leer el archivo PDF para adjuntar: {e}")

            respuesta = resend.Emails.send(parametros_email)
            logger.info(f"¡Reporte enviado exitosamente! ID de Resend: {respuesta.get('id')}")

        except Exception as e:
            logger.error(f"Fallo crítico al enviar el reporte por Resend: {e}")
            raise

    def _enviar_alerta_sin_datos(self) -> None:
        """
        Envía un correo de texto simple avisando que el ETL corrió pero no encontró datos.
        Es un método privado (por eso arranca con guion bajo).
        """
        try:
            parametros_email = {
                "from": settings.EMAIL_SENDER,
                "to": [settings.EMAIL_RECIPIENT],
                "subject": "⚠️ Tech Job Report: Sin movimiento esta semana",
                "text": "Hola. El motor de automatización se ejecutó correctamente, pero no se encontraron nuevas ofertas laborales en la base de datos durante los últimos 7 días."
            }
            resend.Emails.send(parametros_email)
            logger.info("Alerta de 'sin datos' enviada exitosamente.")
        except Exception as e:
            logger.error(f"Fallo al enviar la alerta por Resend: {e}")
            raise