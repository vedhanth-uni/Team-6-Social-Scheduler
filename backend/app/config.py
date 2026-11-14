# settings read from backend/.env, copy .env.example to .env and fill it in

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    # same value as VITE_SUPABASE_URL in the frontend
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    # only for older projects that sign tokens with a shared secret, leave blank otherwise
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    SUPABASE_JWT_AUDIENCE: str = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip()

    # emails go out through gmail with an app password. leave either blank and they get printed
    # to the backend console instead
    GMAIL_ADDRESS: str = os.getenv("GMAIL_ADDRESS", "").strip()
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Social Scheduler")

    CORS_ORIGINS: list[str] = [
        o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
    ] or [FRONTEND_URL]

    @property
    def issuer(self) -> str:
        return f"{self.SUPABASE_URL}/auth/v1"

    @property
    def gmail_enabled(self) -> bool:
        return bool(self.GMAIL_ADDRESS and self.GMAIL_APP_PASSWORD)


settings = Settings()
