import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """
    Servicio encargado de procesar los datos crudos extraídos de la base de datos
    utilizando Pandas para generar estadísticas y resúmenes estructurados.
    """

    def generar_estadisticas(self, datos_crudos: list[dict]) -> dict:
        """
        Toma una lista de ofertas laborales y calcula métricas clave.

        **Args:**
        - **datos_crudos** (list[dict]): Los datos tal cual vienen de Supabase.

        **Returns:**
        - **dict**: Un diccionario con el total de ofertas, el top de tecnologías y un flag booleano.
        """

        if not datos_crudos:
            logger.warning("No hay datos para analizar esta semana.")
            return {
                "total_ofertas": 0,
                "top_tecnologias": [],
                "dream_jobs": [],
                "hay_datos": False
            }

        try:
            df = pd.DataFrame(datos_crudos)
            total_ofertas = len(df)

            patron_busqueda = 'python|backend|fastapi|flask'

            mask_dream = df['titulo'].str.contains(patron_busqueda, case=False, na=False)
            df_dream_jobs = df[mask_dream].head(5)

            dream_jobs = df_dream_jobs[['titulo', 'empresa', 'enlace', 'salario']].fillna('No especificado').to_dict('records')
            logger.info(f"Se encontraron {len(dream_jobs)} Dream Jobs destacados.")

            df['tecnologias_normalizadas'] = df['tecnologias_normalizadas'].apply(
                lambda x: x if isinstance(x, list) else []
            )

            df_techs = df.explode('tecnologias_normalizadas')
            df_techs = df_techs.dropna(subset=['tecnologias_normalizadas'])
            df_techs = df_techs[df_techs['tecnologias_normalizadas'].str.strip().astype(bool)]

            top_10 = df_techs['tecnologias_normalizadas'].value_counts().head(10)

            top_tecnologias = [
                {"nombre": nombre.upper(), "cantidad": int(cantidad)}
                for nombre, cantidad in top_10.items()
            ]

            logger.info(f"Análisis completado: {total_ofertas} ofertas procesadas. Top 1: {top_tecnologias[0]['nombre'] if top_tecnologias else 'N/A'}")

            return {
                "total_ofertas": total_ofertas,
                "top_tecnologias": top_tecnologias,
                "dream_jobs": dream_jobs,
                "hay_datos": True
            }

        except Exception as e:
            logger.error(f"Error crítico al procesar los datos con Pandas: {e}")

            return {
                "total_ofertas": 0,
                "top_tecnologias": [],
                "dream_jobs": [],
                "hay_datos": False
            }