"""Tests para app.services.db_client module."""

from unittest.mock import MagicMock, patch

import pytest
from postgrest import APIError

from app.services.db_client import DatabaseClient


class TestObtenerOfertasRecientes:
    """Tests para el método obtener_ofertas_recientes."""

    def test_method_signature(self):
        """Test que el método existe y es invocable."""
        assert callable(DatabaseClient.obtener_ofertas_recientes)

    def test_method_signature_has_dias_param(self):
        """Test que el método tiene parámetro dias con default."""
        import inspect

        sig = inspect.signature(DatabaseClient.obtener_ofertas_recientes)
        assert "dias" in sig.parameters
        assert sig.parameters["dias"].default == 7


class TestObtenerSuscriptores:
    """Tests para el método obtener_suscriptores."""

    def test_happy_path_returns_active_subscribers(self, sample_suscriptores):
        """Test consulta exitosa devuelve solo suscriptores activos."""
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            s for s in sample_suscriptores if s["activo"]
        ]

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            result = client.obtener_suscriptores()

        assert len(result) == 2
        assert all(s["activo"] for s in result)

    def test_empty_returns_empty_list(self):
        """Test tabla de suscriptores vacía devuelve lista vacía."""
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            result = client.obtener_suscriptores()

        assert result == []

    def test_error_propagates(self):
        """Test que error de base de datos se propaga."""
        error = APIError({"message": "Connection failed", "code": "500"})
        error.code = "500"
        error.status_code = 500

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = error

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            with pytest.raises(APIError):
                client.obtener_suscriptores()


class TestGuardarEstadisticas:
    """Tests para el método guardar_estadisticas."""

    def test_happy_path_calls_insert(self, sample_analisis):
        """Test inserción exitosa llama a Supabase."""
        mock_client = MagicMock()
        mock_execute = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_execute

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            client.guardar_estadisticas(sample_analisis)

        mock_client.table.assert_called_with("estadisticas_semanales")
        mock_client.table.return_value.insert.assert_called_once()
        mock_client.table.return_value.insert.return_value.execute.assert_called_once()

    def test_hay_datos_false_skips_insert(self):
        """Test que hay_datos=False saltea la inserción en base de datos."""
        analisis = {"hay_datos": False, "total_ofertas": 0, "top_tecnologias": []}
        mock_client = MagicMock()

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            client.guardar_estadisticas(analisis)

        mock_client.table.assert_not_called()

    def test_invalid_top_tecnologias_raises_type_error(self):
        """Test estructura inválida de top_tecnologias lanza TypeError."""
        analisis = {
            "hay_datos": True,
            "total_ofertas": 5,
            "top_tecnologias": "not a list",  # inválido
        }
        mock_client = MagicMock()

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            with pytest.raises(TypeError) as exc_info:
                client.guardar_estadisticas(analisis)
        assert "top_tecnologias debe ser una lista" in str(exc_info.value)

    def test_missing_nombre_raises_value_error(self):
        """Test 'nombre' faltante en top_tecnologias lanza ValueError."""
        analisis = {
            "hay_datos": True,
            "total_ofertas": 5,
            "top_tecnologias": [{"cantidad": 10}],  # falta nombre
        }
        mock_client = MagicMock()

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            with pytest.raises(ValueError) as exc_info:
                client.guardar_estadisticas(analisis)
        assert "faltan claves requeridas" in str(exc_info.value)

    def test_non_int_cantidad_raises_type_error(self):
        """Test cantidad no entera lanza TypeError."""
        analisis = {
            "hay_datos": True,
            "total_ofertas": 5,
            "top_tecnologias": [{"nombre": "python", "cantidad": "diez"}],  # string no int
        }
        mock_client = MagicMock()

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            with pytest.raises(TypeError) as exc_info:
                client.guardar_estadisticas(analisis)
        assert "cantidad debe ser int" in str(exc_info.value)

    def test_insert_error_propagates(self, sample_analisis):
        """Test que error de inserción se propaga."""
        error = APIError({"message": "Insert failed", "code": "500"})
        error.code = "500"
        error.status_code = 500

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.side_effect = error

        with patch("app.services.db_client.create_client", return_value=mock_client):
            client = DatabaseClient()
            with pytest.raises(APIError):
                client.guardar_estadisticas(sample_analisis)