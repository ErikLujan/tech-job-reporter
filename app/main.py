import logging
import sys
from app.services.db_client import DatabaseClient
from app.services.analyzer import DataAnalyzer
from app.services.email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main() -> None:
    """
    Función orquestadora del pipeline ETL (Extract, Transform, Load/Send).
    Coordina los servicios para extraer datos, analizarlos y enviar el reporte.
    """
    logger.info("🚀 Iniciando el pipeline de Tech Job Reporter...")

    try:
        db_client = DatabaseClient()
        analyzer = DataAnalyzer()
        email_sender = EmailSender()

        logger.info("--- PASO 1: Extrayendo datos ---")
        datos_crudos = db_client.obtener_ofertas_recientes(dias=30)

        logger.info("--- PASO 2: Analizando datos ---")
        datos_analizados = analyzer.generar_estadisticas(datos_crudos)

        logger.info("--- PASO 2.5: Guardando historial ---")
        db_client.guardar_estadisticas(datos_analizados)

        logger.info("--- PASO 3: Enviando reporte ---")
        email_sender.enviar_reporte(datos_analizados)

        logger.info("✅ Pipeline ejecutado con éxito. ¡Misión cumplida!")

    except Exception as e:
        logger.critical(f"❌ El pipeline falló catastróficamente: {e}", exc_info=True)
        sys.exit(1)
if __name__ == "__main__":
    main()