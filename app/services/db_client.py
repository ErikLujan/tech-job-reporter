import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from postgrest import APIError
from supabase import Client, create_client

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuración de reintentos para errores transitorios
_MAX_RETRIES = 1
_BASE_BACKOFF_SECONDS = 2

# Códigos de estado HTTP fatales que no se reintentan
_FATAL_STATUS_CODES: set[int] = {400, 401, 403, 404, 422}

# Códigos de estado HTTP transitorios que ameritan reintento
_TRANSIENT_STATUS_CODES: set[int] = {408, 429, 500, 502, 503, 504}

T = TypeVar("T")


class DatabaseClient:
    """
    Cliente encargado exclusivamente de la comunicación con Supabase.
    Aísla la lógica de base de datos del resto de la aplicación.
    """

    def __init__(self) -> None:
        """
        Inicializa la conexión usando las credenciales validadas por Pydantic.
        """

        try:
            self.cliente: Client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_KEY
            )
        except Exception as e:
            logger.error("Error crítico al conectar con Supabase: %s", e)
            raise

    def _validate_top_tecnologias(
        self, top_tecnologias: Any
    ) -> list[dict[str, str | int]]:
        """
        Valida que top_tecnologias sea una lista de {"nombre": str, "cantidad": int}.
        Lanza TypeError si la validación falla.
        """
        if not isinstance(top_tecnologias, list):
            raise TypeError(
                f"top_tecnologias debe ser una lista, se recibió {type(top_tecnologias).__name__}"
            )

        validated: list[dict[str, str | int]] = []
        for idx, item in enumerate(top_tecnologias):
            if not isinstance(item, dict):
                raise TypeError(
                    f"top_tecnologias[{idx}] debe ser un dict, se recibió {type(item).__name__}"
                )

            if "nombre" not in item or "cantidad" not in item:
                raise ValueError(
                    f"top_tecnologias[{idx}] faltan claves requeridas 'nombre' y/o 'cantidad'"
                )

            nombre = item["nombre"]
            cantidad = item["cantidad"]

            if not isinstance(nombre, str):
                raise TypeError(
                    f"top_tecnologias[{idx}].nombre debe ser str, se recibió {type(nombre).__name__}"
                )

            if not isinstance(cantidad, int):
                raise TypeError(
                    f"top_tecnologias[{idx}].cantidad debe ser int, se recibió {type(cantidad).__name__}"
                )

            validated.append({"nombre": nombre, "cantidad": cantidad})

        return validated

    def _es_error_fatal(self, error: Exception) -> bool:
        """
        Determina si un error es fatal (no se debe reintentar).
        Fatal: 401, 403, 404, 422, errores de schema, errores de auth.
        Transitorios: 408, 429, 500, 502, 503, 504, timeouts de red.
        """
        if isinstance(error, APIError):
            status_code = getattr(error, "status_code", None) or getattr(
                error, "code", None
            )
            if status_code in _FATAL_STATUS_CODES:
                return True
            if status_code in _TRANSIENT_STATUS_CODES:
                return False
            # Código desconocido — tratamos como transitorio por seguridad
            return False

        # Errores de red, timeouts, conexión — tratamos como transitorios
        error_msg = str(error).lower()
        transient_indicators = [
            "timeout",
            "connection",
            "connect",
            "dns",
            "network",
            "unreachable",
        ]
        return not any(indicator in error_msg for indicator in transient_indicators)

    def _execute_with_retry(self, operation: Callable[[], T], operation_name: str) -> T:
        """
        Ejecuta una operación de base de datos con lógica de reintento para errores transitorios.
        """
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                return operation()
            except APIError as e:
                last_error = e
                if self._es_error_fatal(e):
                    logger.exception("Error fatal en %s", operation_name)
                    raise
                # Error transitorio — logueamos y reintentamos si quedan intentos
                if attempt < _MAX_RETRIES:
                    backoff = _BASE_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        "Error transitorio en %s (intento %s/%s): %s. Reintentando en %ss...",
                        operation_name,
                        attempt + 1,
                        _MAX_RETRIES + 1,
                        e,
                        backoff,
                    )
                    time.sleep(backoff)
                else:
                    logger.exception(
                        "Error transitorio en %s persistió tras %s intentos",
                        operation_name,
                        _MAX_RETRIES + 1,
                    )
                    raise
            except Exception as e:
                last_error = e
                if self._es_error_fatal(e):
                    logger.exception("Error fatal en %s", operation_name)
                    raise
                # Error transitorio — logueamos y reintentamos si quedan intentos
                if attempt < _MAX_RETRIES:
                    backoff = _BASE_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        "Error transitorio en %s (intento %s/%s): %s. Reintentando en %ss...",
                        operation_name,
                        attempt + 1,
                        _MAX_RETRIES + 1,
                        e,
                        backoff,
                    )
                    time.sleep(backoff)
                else:
                    logger.exception(
                        "Error transitorio en %s persistió tras %s intentos",
                        operation_name,
                        _MAX_RETRIES + 1,
                    )
                    raise

        # No deberíamos llegar acá, pero por las dudas
        if last_error is None:
            raise RuntimeError("Lógica de reintentos agotada sin capturar error")
        raise last_error

    def obtener_ofertas_recientes(self, dias: int = 7) -> list[dict[str, object]]:
        """
        Consulta la base de datos para traer las ofertas de los últimos N días.

        **Args:**
        - **dias** (int): Cantidad de días hacia atrás para filtrar. Por defecto 7.

        **Returns:**
        - **list[dict]**: Lista con los registros obtenidos.

        **Raises:**
        - **APIError**: En errores fatales de base de datos (auth, schema, permisos).
        - **Exception**: En errores transitorios persistentes tras reintentos.
        """

        fecha_limite = (datetime.now(UTC) - timedelta(days=dias)).isoformat()

        logger.info("Buscando ofertas publicadas desde: %s", fecha_limite)

        def _query() -> list[dict[str, object]]:
            respuesta = (
                self.cliente.table("ofertas_laborales")
                .select("*")
                .gte("creado_en", fecha_limite)
                .execute()
            )
            return respuesta.data  # type: ignore[return-value]  # Supabase devuelve list[JSON], compatible con list[dict[str, object]]

        datos = self._execute_with_retry(_query, "obtener_ofertas_recientes")
        logger.info("Se extrajeron %s ofertas exitosamente", len(datos))
        return datos

    def guardar_estadisticas(self, datos_analisis: dict[str, object]) -> None:
        """
        Guarda las métricas del reporte semanal en la base de datos
        para permitir análisis histórico en el futuro.

        **Args:**
            datos_analisis (dict): Diccionario generado por DataAnalyzer con las métricas de la semana. Debe contener al menos las claves 'hay_datos', 'total_ofertas' y 'top_tecnologias'.

        **Returns**: None

        **Raises:**
        - **ValueError**: Si la estructura de top_tecnologias es inválida.
        - **APIError**: En errores fatales de base de datos (auth, schema, permisos).
        - **Exception**: En errores transitorios persistentes tras reintentos.
        """
        if not datos_analisis.get("hay_datos"):
            logger.info("No hay datos nuevos para guardar en el historial.")
            return

        # Validamos estructura del payload antes de insertar
        try:
            top_tecnologias_validated = self._validate_top_tecnologias(
                datos_analisis["top_tecnologias"]
            )
        except (KeyError, ValueError) as e:
            logger.error(
                "Validación de payload fallida para guardar_estadisticas: %s", e
            )
            raise ValueError(f"Estructura de top_tecnologias inválida: {e}") from e

        payload: dict[str, object] = {
            "total_ofertas": datos_analisis["total_ofertas"],
            "top_tecnologias": top_tecnologias_validated,
        }

        def _insert() -> None:
            self.cliente.table("estadisticas_semanales").insert(payload).execute()  # type: ignore[arg-type]  # payload dict compatible with JSON

        self._execute_with_retry(_insert, "guardar_estadisticas")
        logger.info("Estadísticas semanales guardadas en Supabase exitosamente.")

    def obtener_suscriptores(self) -> list[dict[str, object]]:
        """
        Obtiene la lista de suscriptores activos desde Supabase.

        **Returns:**
        - **list[dict]**: Lista de suscriptores activos.

        **Raises:**
        - **APIError**: En errores fatales de base de datos (auth, schema, permisos).
        - **Exception**: En errores transitorios persistentes tras reintentos.
        """

        def _query() -> list[dict[str, object]]:
            respuesta = (
                self.cliente.table("suscriptores")
                .select("*")
                .eq("activo", True)
                .execute()
            )
            return respuesta.data  # type: ignore[return-value]  # Supabase devuelve list[JSON], compatible con list[dict[str, object]]

        suscriptores = self._execute_with_retry(_query, "obtener_suscriptores")
        logger.info("Se encontraron %s suscriptores activos.", len(suscriptores))
        return suscriptores
