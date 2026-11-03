"""Tests para app.services.email_sender module."""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.services.email_sender import EmailSender


class TestEnviarReporte:
    """Tests para el método enviar_reporte."""

    def test_happy_path_renders_template_and_sends(
        self, mock_resend, mock_genai, sample_analisis, sample_suscriptores
    ):
        """Test happy path renderiza plantilla Jinja2 y envía via Resend."""
        sender = EmailSender()
        usuario = sample_suscriptores[0]

        # Mock template rendering
        with patch.object(sender.entorno_jinja, "get_template") as mock_get_template:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Test email</html>"
            mock_get_template.return_value = mock_template

            sender.enviar_reporte(
                datos_analisis=sample_analisis,
                destinatario=usuario["email"],
                nombre_usuario=usuario["nombre"],
                ruta_pdf="/tmp/test.pdf",
            )

        mock_get_template.assert_called_once_with("email_body.html")
        mock_template.render.assert_called_once()
        mock_resend.send.assert_called_once()

        # Verificar parámetros del email
        call_args = mock_resend.send.call_args[0][0]
        assert call_args["to"] == [usuario["email"]]
        assert call_args["from"] == "onboarding@resend.dev"
        assert "html" in call_args
        # PDF attachment es opcional si el archivo no existe

    def test_hay_datos_false_sends_plain_text_alert(
        self, mock_resend, sample_suscriptores
    ):
        """Test hay_datos=False envía alerta de texto plano en vez de HTML."""
        sender = EmailSender()
        usuario = sample_suscriptores[0]
        analisis = {"hay_datos": False}

        sender.enviar_reporte(
            datos_analisis=analisis,
            destinatario=usuario["email"],
            nombre_usuario=usuario["nombre"],
        )

        mock_resend.send.assert_called_once()
        call_args = mock_resend.send.call_args[0][0]
        assert "text" in call_args
        assert "html" not in call_args
        assert "Sin novedades" in call_args["subject"]

    def test_resend_error_propagates(self, mock_resend, sample_analisis):
        """Test error de Resend se propaga al caller."""
        mock_resend.send.side_effect = Exception("Resend API error")

        sender = EmailSender()
        with pytest.raises(Exception) as exc_info:
            sender.enviar_reporte(
                datos_analisis=sample_analisis,
                destinatario="test@resend.dev",
                nombre_usuario="Test User",
            )

        assert "Resend API error" in str(exc_info.value)

    def test_pdf_attachment_read_error_logged_but_sends_without_attachment(
        self, mock_resend, sample_analisis, caplog
    ):
        """Test error de lectura PDF se loguea pero email se envía sin adjunto."""
        sender = EmailSender()

        # Mock template para evitar acceso a sistema de archivos
        with patch.object(sender.entorno_jinja, "get_template") as mock_get_template:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Test</html>"
            mock_get_template.return_value = mock_template

            with patch("builtins.open", side_effect=OSError("File not found")):
                sender.enviar_reporte(
                    datos_analisis=sample_analisis,
                    destinatario="test@resend.dev",
                    nombre_usuario="Test User",
                    ruta_pdf="/nonexistent.pdf",
                )

        # Debe seguir enviando email (sin adjunto)
        mock_resend.send.assert_called_once()
        call_args = mock_resend.send.call_args[0][0]
        assert "attachments" not in call_args or call_args["attachments"] == []

        # Verificar que se logueó el error
        assert "No se pudo leer el archivo PDF" in caplog.text

    def test_pdf_attachment_bytes_passed_correctly(self, mock_resend, sample_analisis):
        """Test bytes de adjunto PDF se pasan correctamente (no lista de ints)."""
        sender = EmailSender()
        pdf_content = b"%PDF-1.4 test pdf content"

        with (
            patch("builtins.open", mock_open(read_data=pdf_content)),
            patch.object(sender.entorno_jinja, "get_template") as mock_get_template,
        ):
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Test</html>"
            mock_get_template.return_value = mock_template

            sender.enviar_reporte(
                datos_analisis=sample_analisis,
                destinatario="test@resend.dev",
                nombre_usuario="Test User",
                ruta_pdf="/tmp/test.pdf",
            )

        mock_resend.send.assert_called_once()
        call_args = mock_resend.send.call_args[0][0]
        attachments = call_args.get("attachments", [])
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "Tech_Report_Semanal.pdf"
        # El contenido debe ser bytes, no lista de ints
        assert isinstance(attachments[0]["content"], bytes)
        assert attachments[0]["content"] == pdf_content

    def test_template_receives_correct_context(self, sample_analisis):
        """Test template recibe todas las variables de contexto esperadas."""
        sender = EmailSender()

        with patch.object(sender.entorno_jinja, "get_template") as mock_get_template:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Test</html>"
            mock_get_template.return_value = mock_template

            sender.enviar_reporte(
                datos_analisis=sample_analisis,
                destinatario="test@resend.dev",
                nombre_usuario="Juan",
                ruta_pdf="/tmp/test.pdf",
            )

        render_call = mock_template.render.call_args[1]
        assert render_call["nombre"] == "Juan"
        assert render_call["total_ofertas"] == sample_analisis["total_ofertas"]
        assert render_call["top_tecnologias"] == sample_analisis["top_tecnologias"]
        assert render_call["dream_jobs"] == sample_analisis["dream_jobs"]
        assert render_call["ai_summary"] == sample_analisis["ai_summary"]

    def test_email_subject_contains_total_ofertas(self, sample_analisis):
        """Test subject del email incluye total_ofertas."""
        sender = EmailSender()

        with patch.object(sender.entorno_jinja, "get_template") as mock_get_template:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Test</html>"
            mock_get_template.return_value = mock_template

            with patch("app.services.email_sender.resend.Emails.send") as mock_send:
                sender.enviar_reporte(
                    datos_analisis=sample_analisis,
                    destinatario="test@resend.dev",
                    nombre_usuario="Juan",
                )

                mock_send.assert_called_once()
                subject = mock_send.call_args[0][0]["subject"]
                assert "5" in subject  # total_ofertas = 5
                assert "Juan" in subject
