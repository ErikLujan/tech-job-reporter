import logging
import os
import sys

from app.services.ai_client import AIClient
from app.services.analyzer import DataAnalyzer
from app.services.db_client import DatabaseClient
from app.services.email_sender import EmailSender
from app.services.pdf_generator import PDFGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Función orquestadora del pipeline ETL (Extract, Transform, Load/Send).
    Coordina los servicios para extraer datos, analizarlos y enviar un reporte
    personalizado a cada suscriptor activo.
    """
    logger.info("Iniciando el pipeline multi-usuario de Tech Job Reporter...")

    try:
        db_client = DatabaseClient()
        analyzer = DataAnalyzer()
        pdf_generator = PDFGenerator()
        email_sender = EmailSender()
        ai_client = AIClient()

        logger.info("--- PASO 1: Extrayendo datos generales del mercado ---")
        datos_crudos = db_client.obtener_ofertas_recientes(dias=7)

        if not datos_crudos:
            logger.warning(
                "No hay datos nuevos en la base de datos. Abortando ejecución."
            )
            return

        logger.info("--- PASO 2: Obteniendo lista de suscriptores activos ---")
        suscriptores = db_client.obtener_suscriptores()

        if not suscriptores:
            logger.warning(
                "No hay suscriptores activos para enviar reportes. Abortando ejecución."
            )
            return

        for usuario in suscriptores:
            email = str(usuario["email"])
            nombre = str(usuario["nombre"])
            preferencias = str(usuario["preferencias_busqueda"])

            logger.info(f"\n--- Procesando reporte para: {nombre} ({email}) ---")

            try:
                logger.info("  -> Analizando datos según preferencias...")
                datos_analizados = analyzer.generar_estadisticas(
                    datos_crudos, patron_busqueda=preferencias
                )

                logger.info("  -> Guardando historial de métricas...")
                db_client.guardar_estadisticas(datos_analizados)

                logger.info("  -> Consultando a la IA de Gemini...")
                resumen_ia = ai_client.generar_resumen(datos_analizados)
                datos_analizados["ai_summary"] = resumen_ia

                logger.info("  -> Generando reporte PDF...")
                ruta_pdf = pdf_generator.generar_reporte(datos_analizados)

                logger.info("  -> Enviando correo personalizado...")
                email_sender.enviar_reporte(
                    datos_analisis=datos_analizados,
                    destinatario=email,
                    nombre_usuario=nombre,
                    ruta_pdf=ruta_pdf,
                )

            except Exception:
                logger.error(f"  Fallo aislado al procesar al usuario {nombre}")
                continue

            finally:
                # Esto se ejecuta siempre, haya fallado o no, para limpiar la basura
                if "ruta_pdf" in locals() and ruta_pdf and os.path.exists(ruta_pdf):
                    os.remove(ruta_pdf)

        logger.info(
            "\nPipeline ejecutado con éxito para todos los suscriptores. Misión cumplida."
        )

    except Exception as e:
        logger.critical("El pipeline falló catastróficamente: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
