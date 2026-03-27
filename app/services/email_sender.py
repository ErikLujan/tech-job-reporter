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

    def enviar_reporte(self, datos_analisis: dict, destinatario: str, nombre_usuario: str, ruta_pdf: str | None = None) -> None:
        """
        Toma los datos analizados, renderiza el HTML y dispara el correo al suscriptor.
        Si no hay datos, dispara una alerta de texto plano.
        
        **Args:**
        - datos_analisis (dict): El diccionario devuelto por DataAnalyzer.
        - destinatario (str): El email del usuario que recibe el reporte.
        - nombre_usuario (str): El nombre del usuario.
        - ruta_pdf (str | None): Ruta local al archivo PDF generado, opcional.
        """

        if not datos_analisis.get("hay_datos"):
            logger.info(f"No hay datos para {nombre_usuario}. Enviando alerta simple...")
            self._enviar_alerta_sin_datos(destinatario, nombre_usuario) 
            return

        try:
            template = self.entorno_jinja.get_template("email_body.html")
            html_renderizado = template.render(
                nombre=nombre_usuario,
                total_ofertas=datos_analisis["total_ofertas"],
                top_tecnologias=datos_analisis["top_tecnologias"],
                dream_jobs=datos_analisis.get("dream_jobs", []),
                ai_summary=datos_analisis.get("ai_summary", "")
            )

            parametros_email = {
                "from": settings.EMAIL_SENDER,
                "to": [destinatario],
                "subject": f"🔥 Tech Job Report para {nombre_usuario}: {datos_analisis['total_ofertas']} nuevas ofertas",
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
            logger.info(f"¡Reporte enviado exitosamente a {destinatario}! ID de Resend: {respuesta.get('id')}")

        except Exception as e:
            logger.error(f"Fallo crítico al enviar el reporte por Resend a {destinatario}: {e}")
            raise

    def _enviar_alerta_sin_datos(self, destinatario: str, nombre_usuario: str) -> None:
        """
        Envía un correo de texto simple avisando que el ETL corrió pero no encontró datos
        que coincidan con las preferencias del usuario.
        """
        try:
            parametros_email = {
                "from": settings.EMAIL_SENDER,
                "to": [destinatario],
                "subject": f"⚠️ Tech Job Report: Sin novedades para {nombre_usuario}",
                "text": f"Hola {nombre_usuario}.\n\nEl motor de automatización se ejecutó correctamente, pero esta semana no se encontraron nuevas ofertas laborales que coincidan con tus preferencias de búsqueda.\n\n¡La próxima semana habrá más suerte!"
            }
            resend.Emails.send(parametros_email)
            logger.info(f"Alerta de 'sin datos' enviada exitosamente a {destinatario}.")
        except Exception as e:
            logger.error(f"Fallo al enviar la alerta por Resend a {destinatario}: {e}")
            raise