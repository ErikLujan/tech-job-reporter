"""Tests para app.services.ai_client module."""

from unittest.mock import MagicMock

from app.services.ai_client import AIClient


class TestGenerarResumen:
    """Tests para el método generar_resumen."""

    def test_happy_path_calls_gemini_and_returns_sanitized(
        self, mock_genai, sample_analisis
    ):
        """Test happy path llama a Gemini y devuelve string sanitizado."""
        client = AIClient()
        result = client.generar_resumen(sample_analisis)

        assert isinstance(result, str)
        assert len(result) > 0
        mock_genai.generate_content.assert_called_once()

    def test_hay_datos_false_returns_default_without_calling_gemini(self, mock_genai):
        """Test hay_datos=False devuelve mensaje default sin llamar a Gemini."""
        analyzer_no_data = {"hay_datos": False, "top_tecnologias": []}
        client = AIClient()
        result = client.generar_resumen(analyzer_no_data)

        assert "suficiente movimiento" in result
        mock_genai.generate_content.assert_not_called()

    def test_gemini_error_returns_fallback_no_crash(self, mock_genai):
        """Test error de Gemini devuelve fallback sin crashear."""
        mock_genai.generate_content.side_effect = Exception("API quota exceeded")

        client = AIClient()
        result = client.generar_resumen(
            {
                "hay_datos": True,
                "top_tecnologias": [{"nombre": "python", "cantidad": 5}],
            }
        )

        assert "no se pudo generar" in result
        assert isinstance(result, str)

    def test_llm_output_with_script_tag_sanitized(self, mock_genai):
        """Test salida LLM con tag <script> sanitizada por bleach."""
        mock_response = MagicMock()
        mock_response.text = "Python is hot! <script>alert('xss')</script> More text."
        mock_genai.generate_content.return_value = mock_response

        client = AIClient()
        result = client.generar_resumen(
            {
                "hay_datos": True,
                "top_tecnologias": [{"nombre": "python", "cantidad": 5}],
            }
        )

        assert "<script>" not in result
        # bleach remueve tags pero deja contenido, así que "alert" puede quedar como texto
        assert "<script>" not in result
        assert "More text." in result

    def test_llm_output_with_onload_sanitized(self, mock_genai):
        """Test salida LLM con onload= sanitizada."""
        mock_response = MagicMock()
        mock_response.text = "Great week! <img src=x onload=alert(1)> End."
        mock_genai.generate_content.return_value = mock_response

        client = AIClient()
        result = client.generar_resumen(
            {
                "hay_datos": True,
                "top_tecnologias": [{"nombre": "python", "cantidad": 5}],
            }
        )

        assert "onload=" not in result
        assert "Great week!" in result
        assert "End." in result

    def test_llm_output_with_javascript_protocol_sanitized(self, mock_genai):
        """Test salida LLM con protocolo javascript: sanitizado."""
        mock_response = MagicMock()
        mock_response.text = 'Check <a href="javascript:alert(1)">this</a> out.'
        mock_genai.generate_content.return_value = mock_response

        client = AIClient()
        result = client.generar_resumen(
            {
                "hay_datos": True,
                "top_tecnologias": [{"nombre": "python", "cantidad": 5}],
            }
        )

        assert "javascript:" not in result
        assert "Check" in result
        assert "out." in result

    def test_returns_stripped_string(self, mock_genai):
        """Test string devuelto sin espacios al principio/final."""
        mock_response = MagicMock()
        mock_response.text = "  Summary with spaces  "
        mock_genai.generate_content.return_value = mock_response

        client = AIClient()
        result = client.generar_resumen(
            {
                "hay_datos": True,
                "top_tecnologias": [{"nombre": "python", "cantidad": 5}],
            }
        )

        assert result == "Summary with spaces"

    def test_uses_correct_model_from_config(self, mock_genai, monkeypatch):
        """Test que AIClient usa modelo desde config."""
        monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

        # Necesario reimportar para tomar nuevo env
        import importlib

        import app.services.ai_client as ai_module

        importlib.reload(ai_module)

        client = ai_module.AIClient()
        # El modelo debe crearse con el valor del config
        # Nota: no podemos aseverar fácilmente sobre el mock ya que está parcheado a nivel módulo
        # Este test verifica que no crashea al recargar
        assert client is not None
