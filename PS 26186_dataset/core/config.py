import os
import logging
from pathlib import Path
from typing import List

# Load .env file manually if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

class Settings:
    PROJECT_NAME: str = "Personnel Stress & Welfare Monitoring API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "final_stress_prediction_pipeline.pkl")
    
    def __init__(self):
        # Environment & Debug Configuration
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()
        self.DEBUG: bool = os.getenv("DEBUG", "false").strip().lower() in ("true", "1", "yes")
        self.ALLOW_LOCAL_CORS_IN_PROD: bool = os.getenv("ALLOW_LOCAL_CORS_IN_PROD", "false").strip().lower() in ("true", "1", "yes")
        self.ENABLE_DOCS: bool = os.getenv(
            "ENABLE_DOCS",
            "true" if self.ENVIRONMENT != "production" else "false"
        ).strip().lower() in ("true", "1", "yes")

        # Database Settings (PostgreSQL primary with fallback)
        raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./personnel_welfare.db")
        if raw_db_url.startswith("sqlite:///") and not raw_db_url.startswith("sqlite:////") and not (len(raw_db_url) > 11 and raw_db_url[10] == ":"):
            clean_rel = raw_db_url.replace("sqlite:///", "")
            if clean_rel.startswith("./") or clean_rel.startswith(".\\"):
                clean_rel = clean_rel[2:]
            abs_db_path = os.path.join(self.BASE_DIR, clean_rel).replace("\\", "/")
            self.DATABASE_URL = f"sqlite:///{abs_db_path}"
        else:
            self.DATABASE_URL = raw_db_url
        
        # JWT Authentication Security Settings
        # Must be supplied via environment variable; no hardcoded fallback allowed.
        _raw_secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
        if not _raw_secret:
            raise RuntimeError(
                "JWT secret environment variable is required. "
                "Please set 'SECRET_KEY' or 'JWT_SECRET' in your environment or .env file."
            )

        # In production, disallow known development placeholders or short weak secrets
        if self.ENVIRONMENT == "production":
            known_insecure_secrets = {
                "replace-with-a-long-random-secret",
                "secret",
                "secretkey",
                "admin",
                "password",
                "changeme",
                "test",
                "sih_personnel_stress_monitoring_secret_key_2026_secure"
            }
            if _raw_secret.strip().lower() in known_insecure_secrets or len(_raw_secret.strip()) < 32:
                raise RuntimeError(
                    "Insecure SECRET_KEY configured for production environment. "
                    "A cryptographically strong secret of at least 32 characters is required in production."
                )
            if self.DEBUG:
                raise RuntimeError("DEBUG mode cannot be enabled in a production environment.")

        self.SECRET_KEY: str = _raw_secret
        self.ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        
        # CORS Origins (Configurable via ALLOWED_ORIGINS or CORS_ORIGINS)
        _default_origins: List[str] = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3002",
        ]
        _env_origins = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS")
        if _env_origins:
            self.ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _env_origins.split(",") if origin.strip()]
        else:
            self.ALLOWED_ORIGINS: List[str] = _default_origins

        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()

# Configure standardized logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("welfare_api")
