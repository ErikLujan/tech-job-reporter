import logging
import os
import tempfile
from datetime import datetime
from typing import cast

import matplotlib.pyplot as plt
from fpdf import FPDF

from app.core.config import (
    CHART_COLOR,
    CHART_STYLE,
    FIGURE_SIZE,
)

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Servicio encargado de generar un reporte en formato PDF altamente visual y profesional.
    Demuestra habilidades avanzadas en renderizado de documentos y visualización de datos.
    """

    def generar_reporte(self, datos_analisis: dict[str, object]) -> str | None:
        if not datos_analisis.get("hay_datos") or not datos_analisis.get(
            "top_tecnologias"
        ):
            logger.info("No hay datos suficientes para generar el PDF.")
            return None

        color_tech_blue = CHART_COLOR

        # Usamos tempfile para no ensuciar el directorio actual
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_chart:
            ruta_grafico = tmp_chart.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            ruta_pdf = tmp_pdf.name

        try:
            # Casteamos la estructura conocida del output de DataAnalyzer
            top_tecnologias = cast(
                list[dict[str, str | int]], datos_analisis["top_tecnologias"]
            )

            tecnologias = [item["nombre"] for item in top_tecnologias][::-1]
            cantidades = [item["cantidad"] for item in top_tecnologias][::-1]

            plt.style.use(CHART_STYLE)
            _fig, ax = plt.subplots(figsize=FIGURE_SIZE)

            bars = ax.barh(
                tecnologias,
                cantidades,
                color=color_tech_blue,
                edgecolor="white",
                height=0.7,
            )

            ax.set_title(
                "TOP 10 TECNOLOGÍAS MÁS DEMANDADAS",
                fontsize=18,
                fontweight="bold",
                color="#333333",
                pad=20,
            )
            ax.set_xlabel("CANTIDAD DE OFERTAS LABORALES", fontsize=12, labelpad=10)

            for spine in ["top", "right", "bottom"]:
                ax.spines[spine].set_visible(False)

            ax.grid(axis="x", linestyle="--", alpha=0.5)
            ax.tick_params(axis="both", which="major", labelsize=11)

            ax.bar_label(
                bars,
                fmt="%d",
                padding=5,
                fontsize=11,
                fontweight="bold",
                color=color_tech_blue,
            )

            plt.tight_layout()

            plt.savefig(ruta_grafico, dpi=200, bbox_inches="tight")
            plt.close()

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            r, g, b = tuple(
                int(color_tech_blue.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
            )
            pdf.set_fill_color(r, g, b)
            pdf.rect(0, 0, 210, 50, "F")

            pdf.set_font("helvetica", "B", 24)
            pdf.set_text_color(255, 255, 255)
            pdf.ln(10)
            pdf.cell(0, 15, "Tech Job Market Report", ln=True, align="C")

            pdf.set_font("helvetica", "I", 12)
            fecha_actual = datetime.now().strftime("%d/%m/%Y")
            pdf.cell(
                0,
                10,
                f"Resumen automatizado de la última semana - {fecha_actual}",
                ln=True,
                align="C",
            )

            pdf.set_text_color(51, 51, 51)
            pdf.ln(25)

            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Resumen General", ln=True)

            pdf.set_font("helvetica", "", 12)
            pdf.set_draw_color(226, 232, 240)
            pdf.line(pdf.get_x(), pdf.get_y(), 195, pdf.get_y())
            pdf.ln(5)

            pdf.cell(
                0,
                10,
                f"Se analizaron un total de {datos_analisis['total_ofertas']} nuevas ofertas laborales.",
                ln=True,
            )
            pdf.ln(10)

            pdf.image(ruta_grafico, x=15, w=180)

            pdf.set_y(-25)
            pdf.set_font("helvetica", "I", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(
                0,
                5,
                "Este reporte fue generado automáticamente por tu motor ETL en Python.",
                ln=True,
                align="C",
            )
            pdf.cell(0, 5, "Powered by Supabase & Resend API.", ln=True, align="C")

            pdf.output(ruta_pdf)
            logger.info("PDF generado exitosamente en: %s", ruta_pdf)

            return ruta_pdf

        except Exception:
            logger.exception("Error al generar el PDF o el gráfico")
            return None

        finally:
            for path in (ruta_grafico, ruta_pdf):
                if os.path.exists(path):
                    os.remove(path)
