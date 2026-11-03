"""Tests para app.services.analyzer module."""

from app.services.analyzer import DataAnalyzer


class TestGenerarEstadisticas:
    """Tests para el método generar_estadisticas."""

    def test_empty_input_returns_hay_datos_false(self):
        """Test entrada vacía devuelve hay_datos=False."""
        analyzer = DataAnalyzer()
        result = analyzer.generar_estadisticas([], "python")

        assert result["hay_datos"] is False
        assert result["total_ofertas"] == 0
        assert result["top_tecnologias"] == []
        assert result["dream_jobs"] == []

    def test_normal_input_computes_total_ofertas(self, sample_ofertas):
        """Test entrada normal computa total_ofertas correctamente."""
        analyzer = DataAnalyzer()
        result = analyzer.generar_estadisticas(sample_ofertas, "python")

        assert result["hay_datos"] is True
        assert result["total_ofertas"] == 5

    def test_computes_top_10_technologies(self, sample_ofertas):
        """Test computa top 10 tecnologías con conteos correctos."""
        analyzer = DataAnalyzer()
        result = analyzer.generar_estadisticas(sample_ofertas, "python")

        top_tech = result["top_tecnologias"]
        assert len(top_tech) <= 10
        # Python aparece en 4 de 5 ofertas
        python_entry = next((t for t in top_tech if t["nombre"] == "PYTHON"), None)
        assert python_entry is not None
        assert python_entry["cantidad"] == 4
        # Los resultados deben estar ordenados por cantidad descendente
        counts = [t["cantidad"] for t in top_tech]
        assert counts == sorted(counts, reverse=True)

    def test_dream_jobs_limit_5(self, sample_ofertas):
        """Test dream_jobs limitado a 5 entradas."""
        # Creamos muchas ofertas que coincidan
        many_offers = sample_ofertas * 3  # 15 ofertas, todas coinciden con "python"
        analyzer = DataAnalyzer()
        result = analyzer.generar_estadisticas(many_offers, "python")

        assert len(result["dream_jobs"]) == 5

    def test_patron_busqueda_filters_case_insensitive(self, sample_ofertas):
        """Test patron_busqueda filtra títulos sin distinción de mayúsculas."""
        analyzer = DataAnalyzer()
        result = analyzer.generar_estadisticas(sample_ofertas, "PYTHON")  # uppercase

        dream_jobs = result["dream_jobs"]
        assert len(dream_jobs) > 0
        # Debe coincidir con "Senior Backend Developer Python" y "Python Developer - Django"
        titles = [j["titulo"].lower() for j in dream_jobs]
        assert any("python" in t for t in titles)

    def test_patron_busqueda_no_match_returns_empty_dream_jobs(self, sample_ofertas):
        """Test sin coincidencias devuelve dream_jobs vacío."""
        analyzer = DataAnalyzer()
        result = analyzer.generar_estadisticas(sample_ofertas, "nonexistent_tech")

        assert result["dream_jobs"] == []

    def test_missing_tecnologias_normalizadas_handled_gracefully(self):
        """Test tecnologias_normalizadas faltante manejado sin error."""
        analyzer = DataAnalyzer()
        offers_without_tech = [
            {
                "id": 1,
                "titulo": "Backend Dev",
                "empresa": "Test",
                "enlace": "http://test.com",
                "salario": "$50k",
                "tecnologias_normalizadas": [],
            },
        ]
        result = analyzer.generar_estadisticas(offers_without_tech, "backend")

        assert result["hay_datos"] is True
        assert result["top_tecnologias"] == []

    def test_tecnologias_normalizadas_not_list_handled(self):
        """Test tecnologias_normalizadas que no es lista se maneja."""
        analyzer = DataAnalyzer()
        offers_bad_tech = [
            {
                "id": 1,
                "titulo": "Backend Dev",
                "empresa": "Test",
                "enlace": "http://test.com",
                "salario": "$50k",
                "tecnologias_normalizadas": "python",  # string en vez de lista
            },
        ]
        result = analyzer.generar_estadisticas(offers_bad_tech, "backend")

        assert result["hay_datos"] is True
        # Debe tratar string como lista vacía (lambda lo maneja)
        assert result["top_tecnologias"] == []

    def test_dream_jobs_includes_correct_fields(self, sample_ofertas):
        """Test dream_jobs incluye titulo, empresa, enlace, salario."""
        analyzer = DataAnalyzer()
        result = analyzer.generar_estadisticas(sample_ofertas, "python")

        for job in result["dream_jobs"]:
            assert "titulo" in job
            assert "empresa" in job
            assert "enlace" in job
            assert "salario" in job

    def test_salario_missing_filled_with_no_especificado(self):
        """Test salario faltante se completa con 'No especificado'."""
        analyzer = DataAnalyzer()
        offers = [
            {
                "id": 1,
                "titulo": "Python Dev",
                "empresa": "Test",
                "enlace": "http://test.com",
                "tecnologias_normalizadas": ["python"],
                "salario": None,
            },
        ]
        result = analyzer.generar_estadisticas(offers, "python")

        assert result["dream_jobs"][0]["salario"] == "No especificado"
