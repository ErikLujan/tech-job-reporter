import logging

from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class DatabaseClient:
    """
    Cliente encargado exclusivamente de la comunicación con Supabase.
    Aísla la lógica de base de datos del resto de la aplicación.
    """

    def __init__(self):
        """
        Inicializa la conexión usando las credenciales validadas por Pydantic.
        """

        try:
            self.cliente: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        except Exception as e:
            logger.error(f"Error critico al conectar con Supabase: {e}")
            raise

    def obtener_ofertas_recientes(self, dias: int = 7) -> list[dict]:
        """
        Consulta la base de datos para traer las ofertas de los últimos N días.
        
        **Args:**
        - **dias** (int): Cantidad de días hacia atrás para filtrar. Por defecto 7.

        **Returns:**
        - **list[dict]**: Lista con los registros obtenidos.
        """

        fecha_limite = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()

        logger.info(F"Buscando ofertas publicadas desde: {fecha_limite}")

        try:
            respuesta = self.cliente.table("ofertas_laborales") \
                        .select("*") \
                        .gte("creado_en", fecha_limite) \
                        .execute()
            
            datos = respuesta.data
            logger.info(f"Se extrajeron {len(datos)} ofertas exitosamente")

            return datos
        except Exception as e:
            logger.error(f"Fallo al realizar la consulta en Supabase: {e}")
            return []