"""Shared fixtures for tech-job-reporter tests."""

from typing import Any
from unittest.mock import MagicMock

import pytest

# Sample data fixtures


@pytest.fixture
def sample_ofertas() -> list[dict[str, Any]]:
    """Sample job offers mimicking Supabase ofertas_laborales rows."""
    return [
        {
            "id": 1,
            "titulo": "Senior Backend Developer Python",
            "empresa": "TechCorp SA",
            "enlace": "https://jobs.techcorp.com/1",
            "salario": "$80,000 - $120,000",
            "tecnologias_normalizadas": ["python", "django", "postgresql", "aws"],
            "creado_en": "2026-10-25T10:00:00Z",
        },
        {
            "id": 2,
            "titulo": "Backend Engineer - Node.js",
            "empresa": "StartupXYZ",
            "enlace": "https://jobs.startupxyz.com/2",
            "salario": "$70,000 - $100,000",
            "tecnologias_normalizadas": ["node.js", "express", "mongodb", "docker"],
            "creado_en": "2026-10-26T14:30:00Z",
        },
        {
            "id": 3,
            "titulo": "Python Developer - Django",
            "empresa": "DataFlow Inc",
            "enlace": "https://jobs.dataflow.com/3",
            "salario": "No especificado",
            "tecnologias_normalizadas": ["python", "django", "redis", "kubernetes"],
            "creado_en": "2026-10-27T09:15:00Z",
        },
        {
            "id": 4,
            "titulo": "Full Stack Developer",
            "empresa": "WebApp Co",
            "enlace": "https://jobs.webapp.com/4",
            "salario": "$60,000 - $90,000",
            "tecnologias_normalizadas": ["react", "python", "fastapi", "postgresql"],
            "creado_en": "2026-10-28T16:45:00Z",
        },
        {
            "id": 5,
            "titulo": "DevOps Engineer",
            "empresa": "CloudSystems",
            "enlace": "https://jobs.cloudsystems.com/5",
            "salario": "$90,000 - $130,000",
            "tecnologias_normalizadas": ["aws", "terraform", "kubernetes", "python"],
            "creado_en": "2026-10-29T11:20:00Z",
        },
    ]


@pytest.fixture
def sample_suscriptores() -> list[dict[str, Any]]:
    """Sample subscribers with preferences."""
    return [
        {
            "id": 1,
            "nombre": "Juan Pérez",
            "email": "juan.perez@resend.dev",  # Resend test domain
            "preferencias_busqueda": "python",
            "activo": True,
        },
        {
            "id": 2,
            "nombre": "María García",
            "email": "maria.garcia@resend.dev",
            "preferencias_busqueda": "backend",
            "activo": True,
        },
        {
            "id": 3,
            "nombre": "Carlos López",
            "email": "carlos.lopez@resend.dev",
            "preferencias_busqueda": "django",
            "activo": False,  # inactive subscriber
        },
    ]


@pytest.fixture
def sample_analisis() -> dict[str, Any]:
    """Sample analysis output from DataAnalyzer."""
    return {
        "hay_datos": True,
        "total_ofertas": 5,
        "top_tecnologias": [
            {"nombre": "PYTHON", "cantidad": 4},
            {"nombre": "DJANGO", "cantidad": 2},
            {"nombre": "POSTGRESQL", "cantidad": 2},
            {"nombre": "AWS", "cantidad": 2},
            {"nombre": "NODE.JS", "cantidad": 1},
            {"nombre": "EXPRESS", "cantidad": 1},
            {"nombre": "MONGODB", "cantidad": 1},
            {"nombre": "DOCKER", "cantidad": 1},
            {"nombre": "REDIS", "cantidad": 1},
            {"nombre": "KUBERNETES", "cantidad": 2},
        ],
        "dream_jobs": [
            {
                "titulo": "Senior Backend Developer Python",
                "empresa": "TechCorp SA",
                "enlace": "https://jobs.techcorp.com/1",
                "salario": "$80,000 - $120,000",
            },
            {
                "titulo": "Python Developer - Django",
                "empresa": "DataFlow Inc",
                "enlace": "https://jobs.dataflow.com/3",
                "salario": "No especificado",
            },
        ],
        "ai_summary": "Python domina el mercado con 4 menciones. Django y Kubernetes muestran crecimiento sostenido.",
    }


# Mock fixtures


@pytest.fixture
def mock_supabase() -> MagicMock:
    """Mock Supabase client with chainable query interface."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_gte = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()

    # Chain: client.table().select().gte().eq().execute()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.gte.return_value = mock_gte
    mock_gte.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute

    # Default successful response
    mock_execute.return_value.data = []

    return mock_client


@pytest.fixture
def mock_genai(monkeypatch) -> MagicMock:
    """Mock Google Generative AI model using new google.genai SDK."""
    mock_client = MagicMock()
    mock_models = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "Python domina el mercado esta semana con fuerte demanda en Django y FastAPI."
    )
    mock_models.generate_content.return_value = mock_response
    mock_client.models = mock_models

    mock_genai_module = MagicMock()
    mock_genai_module.Client.return_value = mock_client

    # Patch at the module where it's imported
    monkeypatch.setattr("app.services.ai_client.genai", mock_genai_module)
    return mock_models


@pytest.fixture
def mock_resend(monkeypatch) -> MagicMock:
    """Mock Resend email sender."""
    mock_emails = MagicMock()
    mock_emails.send.return_value = {"id": "test_email_123"}

    mock_resend_module = MagicMock()
    mock_resend_module.Emails = mock_emails

    # Patch at the module where it's imported
    monkeypatch.setattr("app.services.email_sender.resend", mock_resend_module)
    return mock_emails


# Environment fixtures


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Set required environment variables for tests."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key_123")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_123")
    monkeypatch.setenv("EMAIL_SENDER", "onboarding@resend.dev")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
