"""
Application configuration using Pydantic Settings.

Centralizes all configurable values: file paths, CORS origins,
salary bands, tenure bands, and API metadata.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


# ── Base directory resolution ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
DATA_DIR = BASE_DIR / "data"
DATASET_PATH = DATA_DIR / "dataset.xlsx"
BENEFITS_DATASET_PATH = DATA_DIR / "Ranking_Beneficios_Base_Dashboard.xlsx"


class Settings(BaseSettings):
    """Global application settings."""

    # ── API metadata ───────────────────────────────────────────────────
    app_title: str = "HR Analytics Dashboard API"
    app_version: str = "1.0.0"
    app_description: str = "Backend API for the HR Analytics Dashboard"
    environment: str = "development"

    # ── Data source ────────────────────────────────────────────────────
    dataset_path: Path = Field(default=DATASET_PATH)
    benefits_dataset_path: Path = Field(default=BENEFITS_DATASET_PATH)

    # ── CORS ───────────────────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # CRM_MG — o Dash RH agora roda embarcado como sistema nativo do CRM;
        # o frontend do CRM chama esta API a partir de outra origem.
        "https://crmmg.mendoncagalvao.com.br",
    ]

    # ── Salary bands (BRL) ─────────────────────────────────────────────
    salary_band_junior_max: float = 1_621.00
    salary_band_pleno_max: float = 2_593.72
    salary_band_senior_max: float = 4_052.50
    # Especialista: everything above senior_max

    # ── Security ───────────────────────────────────────────────────────
    confidential_password: str = "senha_segura_123"  # legado, não mais usado (ver auth.py)

    # SSO com o CRM_MG. `crm_jwt_secret` (env HR_CRM_JWT_SECRET) DEVE ser igual
    # ao JWT_SECRET do backend-fastapi do CRM. Sem ele, toda chamada /api/* é
    # recusada com 401. `confidential_allowlist`: e-mails (separados por vírgula)
    # autorizados na Área Restrita; vazio = qualquer usuário autenticado pelo CRM.
    crm_jwt_secret: str = ""
    confidential_allowlist: str = ""
    allowed_email_domains: str = "mendoncagalvao.com.br,nucleodigital.cloud"

    # ── Tenure bands (years) ──────────────────────────────────────────
    tenure_band_newcomer_max: float = 1.0
    tenure_band_growing_max: float = 3.0
    tenure_band_established_max: float = 5.0
    tenure_band_veteran_max: float = 10.0
    # Legacy: everything above veteran_max

    model_config = {"env_prefix": "HR_"}


# Singleton instance
settings = Settings()
