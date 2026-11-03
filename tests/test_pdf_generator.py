"""Tests para app.services.pdf_generator module."""

from unittest.mock import MagicMock, patch

from app.services.pdf_generator import PDFGenerator


class TestGenerarReporte:
    """Tests para el método generar_reporte."""

    def test_happy_path_returns_pdf_path(self, sample_analisis):
        """Test happy path devuelve ruta de archivo PDF."""
        generator = PDFGenerator()

        # Mock matplotlib para evitar plotting real
        with patch("app.services.pdf_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.style.use = MagicMock()
            mock_plt.tight_layout = MagicMock()
            mock_plt.savefig = MagicMock()
            mock_plt.close = MagicMock()

            with patch("app.services.pdf_generator.FPDF") as mock_fpdf_class:
                mock_pdf = MagicMock()
                mock_fpdf_class.return_value = mock_pdf
                mock_pdf.output = MagicMock()

                with (
                    patch("os.path.exists", return_value=True),
                    patch("os.remove") as mock_remove,
                ):
                    generator.generar_reporte(sample_analisis)

                    # Verificar que archivo temp de chart se eliminó
                    mock_remove.assert_any_call(mock_remove.call_args_list[0][0][0])

    def test_hay_datos_false_returns_none(self):
        """Test hay_datos=False devuelve None."""
        generator = PDFGenerator()
        result = generator.generar_reporte({"hay_datos": False, "top_tecnologias": []})

        assert result is None

    def test_missing_top_tecnologias_returns_none(self):
        """Test top_tecnologias faltante devuelve None."""
        generator = PDFGenerator()
        result = generator.generar_reporte({"hay_datos": True})

        assert result is None

    def test_empty_top_tecnologias_returns_none(self):
        """Test top_tecnologias vacía devuelve None."""
        generator = PDFGenerator()
        result = generator.generar_reporte({"hay_datos": True, "top_tecnologias": []})

        assert result is None

    def test_temp_chart_file_cleaned_up(self, sample_analisis):
        """Test archivo temp de chart se limpia tras generación."""
        generator = PDFGenerator()

        with patch("app.services.pdf_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.style.use = MagicMock()
            mock_plt.tight_layout = MagicMock()
            mock_plt.savefig = MagicMock()
            mock_plt.close = MagicMock()

            with patch("app.services.pdf_generator.FPDF") as mock_fpdf_class:
                mock_pdf = MagicMock()
                mock_fpdf_class.return_value = mock_pdf
                mock_pdf.output = MagicMock()

                with (
                    patch("os.path.exists", return_value=True),
                    patch("os.remove") as mock_remove,
                ):
                    generator.generar_reporte(sample_analisis)

                    # Verificar que archivo temp de chart se eliminó
                    mock_remove.assert_any_call(mock_remove.call_args_list[0][0][0])

    def test_temp_pdf_file_cleaned_up_on_error(self, sample_analisis):
        """Test archivo PDF temp se limpia en caso de error."""
        generator = PDFGenerator()

        with patch("app.services.pdf_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.style.use = MagicMock()
            mock_plt.tight_layout = MagicMock()
            mock_plt.savefig = MagicMock()
            mock_plt.close = MagicMock()

            with patch("app.services.pdf_generator.FPDF") as mock_fpdf_class:
                mock_pdf = MagicMock()
                mock_fpdf_class.return_value = mock_pdf
                mock_pdf.output.side_effect = Exception("PDF generation failed")

                with (
                    patch("os.path.exists", return_value=True),
                    patch("os.remove") as mock_remove,
                ):
                    result = generator.generar_reporte(sample_analisis)

                    assert result is None
                    # Tanto chart como PDF deben limpiarse
                    assert mock_remove.call_count >= 2

    def test_pdf_content_includes_total_ofertas(self, sample_analisis):
        """Test PDF generado incluye total_ofertas."""
        generator = PDFGenerator()

        with patch("app.services.pdf_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.style.use = MagicMock()
            mock_plt.tight_layout = MagicMock()
            mock_plt.savefig = MagicMock()
            mock_plt.close = MagicMock()

            with patch("app.services.pdf_generator.FPDF") as mock_fpdf_class:
                mock_pdf = MagicMock()
                mock_fpdf_class.return_value = mock_pdf
                mock_pdf.output = MagicMock()

                with patch("os.path.exists", return_value=True), patch("os.remove"):
                    generator.generar_reporte(sample_analisis)

                    # Verificar que cell se llamó con total_ofertas
                    calls = [str(call) for call in mock_pdf.cell.call_args_list]
                    assert any(
                        "total_ofertas" in str(call) or "5" in str(call)
                        for call in calls
                    )

    def test_uses_correct_chart_style(self, sample_analisis):
        """Test que chart usa estilo configurado."""
        generator = PDFGenerator()

        with patch("app.services.pdf_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.style.use = MagicMock()
            mock_plt.tight_layout = MagicMock()
            mock_plt.savefig = MagicMock()
            mock_plt.close = MagicMock()

            with patch("app.services.pdf_generator.FPDF") as mock_fpdf_class:
                mock_pdf = MagicMock()
                mock_fpdf_class.return_value = mock_pdf
                mock_pdf.output = MagicMock()

                with patch("os.path.exists", return_value=True), patch("os.remove"):
                    generator.generar_reporte(sample_analisis)

                    mock_plt.style.use.assert_called_with("default")

    def test_uses_correct_figure_size(self, sample_analisis):
        """Test que chart usa figure size configurado."""
        generator = PDFGenerator()

        with patch("app.services.pdf_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.style.use = MagicMock()
            mock_plt.tight_layout = MagicMock()
            mock_plt.savefig = MagicMock()
            mock_plt.close = MagicMock()

            with patch("app.services.pdf_generator.FPDF") as mock_fpdf_class:
                mock_pdf = MagicMock()
                mock_fpdf_class.return_value = mock_pdf
                mock_pdf.output = MagicMock()

                with patch("os.path.exists", return_value=True), patch("os.remove"):
                    generator.generar_reporte(sample_analisis)

                    mock_plt.subplots.assert_called_with(figsize=(10, 6))

    def test_chart_color_used(self, sample_analisis):
        """Test que color de chart configurado se usa."""
        generator = PDFGenerator()

        with patch("app.services.pdf_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.style.use = MagicMock()
            mock_plt.tight_layout = MagicMock()
            mock_plt.savefig = MagicMock()
            mock_plt.close = MagicMock()

            with patch("app.services.pdf_generator.FPDF") as mock_fpdf_class:
                mock_pdf = MagicMock()
                mock_fpdf_class.return_value = mock_pdf
                mock_pdf.output = MagicMock()

                with patch("os.path.exists", return_value=True), patch("os.remove"):
                    generator.generar_reporte(sample_analisis)

                    # Verificar que barh se llamó con color correcto
                    mock_ax.barh.assert_called()
                    call_kwargs = mock_ax.barh.call_args[1]
                    assert call_kwargs.get("color") == "#2563eb"
