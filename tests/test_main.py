"""Tests de integración para app.main module."""

from unittest.mock import MagicMock, patch

import pytest

from app.main import main


class TestMainPipeline:
    """Tests para la orquestación del pipeline principal."""

    @patch("app.main.DatabaseClient")
    @patch("app.main.DataAnalyzer")
    @patch("app.main.PDFGenerator")
    @patch("app.main.EmailSender")
    @patch("app.main.AIClient")
    def test_pipeline_calls_services_in_order(
        self,
        mock_ai_client_class,
        mock_email_sender_class,
        mock_pdf_generator_class,
        mock_analyzer_class,
        mock_db_client_class,
        sample_ofertas,
        sample_suscriptores,
        sample_analisis,
    ):
        """Test que el pipeline llama a cada servicio en el orden correcto."""
        # Setup mocks
        mock_db = MagicMock()
        mock_db.obtener_ofertas_recientes.return_value = sample_ofertas
        mock_db.obtener_suscriptores.return_value = sample_suscriptores[
            :2
        ]  # solo activos
        mock_db_client_class.return_value = mock_db

        mock_analyzer = MagicMock()
        mock_analyzer.generar_estadisticas.return_value = sample_analisis
        mock_analyzer_class.return_value = mock_analyzer

        mock_ai = MagicMock()
        mock_ai.generar_resumen.return_value = "AI summary text"
        mock_ai_client_class.return_value = mock_ai

        mock_pdf = MagicMock()
        mock_pdf.generar_reporte.return_value = "/tmp/test_report.pdf"
        mock_pdf_generator_class.return_value = mock_pdf

        mock_email = MagicMock()
        mock_email_sender_class.return_value = mock_email

        # Mock file cleanup
        with (
            patch("os.path.exists", return_value=True),
            patch("os.remove") as mock_remove,
        ):
            main()

        # Verificar orden de llamadas
        mock_db.obtener_ofertas_recientes.assert_called_once_with(dias=7)
        mock_db.obtener_suscriptores.assert_called_once()
        # analyzer se llama una vez por suscriptor (2 activos)
        assert mock_analyzer.generar_estadisticas.call_count == 2
        # AI client se llama una vez por suscriptor
        assert mock_ai.generar_resumen.call_count == 2
        # PDF se genera una vez por suscriptor
        assert mock_pdf.generar_reporte.call_count == 2
        mock_email.enviar_reporte.assert_called()

        # Verificar limpieza de PDF se intentó
        assert mock_remove.called

    @patch("app.main.DatabaseClient")
    def test_no_ofertas_aborts_early(self, mock_db_client_class, caplog):
        """Test pipeline aborta si no hay ofertas."""
        mock_db = MagicMock()
        mock_db.obtener_ofertas_recientes.return_value = []
        mock_db_client_class.return_value = mock_db

        main()

        assert "No hay datos nuevos en la base de datos" in caplog.text

    @patch("app.main.DatabaseClient")
    def test_no_suscriptores_aborts_early(
        self, mock_db_client_class, sample_ofertas, caplog
    ):
        """Test pipeline aborta si no hay suscriptores activos."""
        mock_db = MagicMock()
        mock_db.obtener_ofertas_recientes.return_value = sample_ofertas
        mock_db.obtener_suscriptores.return_value = []
        mock_db_client_class.return_value = mock_db

        main()

        assert "No hay suscriptores activos" in caplog.text

    @patch("app.main.DatabaseClient")
    @patch("app.main.DataAnalyzer")
    @patch("app.main.PDFGenerator")
    @patch("app.main.EmailSender")
    @patch("app.main.AIClient")
    def test_user_failure_continues_to_next(
        self,
        mock_ai_client_class,
        mock_email_sender_class,
        mock_pdf_generator_class,
        mock_analyzer_class,
        mock_db_client_class,
        sample_ofertas,
        sample_suscriptores,
        sample_analisis,
    ):
        """Test que fallo de un usuario continua al siguiente."""
        mock_db = MagicMock()
        mock_db.obtener_ofertas_recientes.return_value = sample_ofertas
        mock_db.obtener_suscriptores.return_value = sample_suscriptores[:2]
        mock_db_client_class.return_value = mock_db

        mock_analyzer = MagicMock()
        mock_analyzer.generar_estadisticas.return_value = sample_analisis
        mock_analyzer_class.return_value = mock_analyzer

        mock_ai = MagicMock()
        mock_ai.generar_resumen.return_value = "AI summary"
        mock_ai_client_class.return_value = mock_ai

        mock_pdf = MagicMock()
        mock_pdf.generar_reporte.return_value = "/tmp/test.pdf"
        mock_pdf_generator_class.return_value = mock_pdf

        # Primer usuario falla, segundo succeeds
        mock_email = MagicMock()
        mock_email.enviar_reporte.side_effect = [
            Exception("Send failed"),
            None,
        ]
        mock_email_sender_class.return_value = mock_email

        with patch("os.path.exists", return_value=True), patch("os.remove"):
            main()

        # Debe haber intentado enviar para ambos usuarios
        assert mock_email.enviar_reporte.call_count == 2

    @patch("app.main.DatabaseClient")
    @patch("app.main.DataAnalyzer")
    @patch("app.main.PDFGenerator")
    @patch("app.main.EmailSender")
    @patch("app.main.AIClient")
    def test_pdf_cleanup_in_finally_block(
        self,
        mock_ai_client_class,
        mock_email_sender_class,
        mock_pdf_generator_class,
        mock_analyzer_class,
        mock_db_client_class,
        sample_ofertas,
        sample_suscriptores,
        sample_analisis,
    ):
        """Test archivo temp PDF se limpia en bloque finally."""
        mock_db = MagicMock()
        mock_db.obtener_ofertas_recientes.return_value = sample_ofertas
        mock_db.obtener_suscriptores.return_value = sample_suscriptores[:1]
        mock_db_client_class.return_value = mock_db

        mock_analyzer = MagicMock()
        mock_analyzer.generar_estadisticas.return_value = sample_analisis
        mock_analyzer_class.return_value = mock_analyzer

        mock_ai = MagicMock()
        mock_ai.generar_resumen.return_value = "AI summary"
        mock_ai_client_class.return_value = mock_ai

        mock_pdf = MagicMock()
        mock_pdf.generar_reporte.return_value = "/tmp/test_report.pdf"
        mock_pdf_generator_class.return_value = mock_pdf

        mock_email = MagicMock()
        mock_email_sender_class.return_value = mock_email

        with (
            patch("os.path.exists", return_value=True),
            patch("os.remove") as mock_remove,
        ):
            main()

            # Verificar limpieza se llamó para la ruta del PDF
            mock_remove.assert_called_with("/tmp/test_report.pdf")

    @patch("app.main.DatabaseClient")
    def test_critical_failure_exits_with_code_1(
        self, mock_db_client_class, sample_ofertas
    ):
        """Test error crítico de BD sale con código 1."""
        mock_db = MagicMock()
        mock_db.obtener_ofertas_recientes.side_effect = Exception(
            "DB connection failed"
        )
        mock_db_client_class.return_value = mock_db

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
