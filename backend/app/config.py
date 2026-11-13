# settings read from backend/.env (or real env vars). copy .env.example -> .env and fill it in.
# never commit .env, it has the gmail app password in it (.gitignore already blocks it)

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    # where the react app lives -- email links point here, not at the api
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    # emails go out through gmail's smtp server using an app password (free, 500 emails/day).
    # leave either one blank and emails get printed to the backend console instead (dev mode).
    GMAIL_ADDRESS: str = os.getenv("GMAIL_ADDRESS", "").strip()
    # google shows app passwords as "abcd efgh ijkl mnop", spaces don't matter
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Social Scheduler")

    FRIEND_REQUEST_TTL_DAYS: int = int(os.getenv("FRIEND_REQUEST_TTL_DAYS", "7"))

    # --- supabase auth (see app/auth.py) ---
    # the project url, same value as VITE_SUPABASE_URL in the frontend
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    # only for older projects that still sign tokens with a shared secret (HS256). leave blank otherwise.
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    SUPABASE_JWT_AUDIENCE: str = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip()

    # browsers only let the frontend call this api from origins listed here (comma separated).
    # defaults to FRONTEND_URL.
    CORS_ORIGINS: list[str] = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()] or [FRONTEND_URL]

    @property
    def issuer(self) -> str:
        # the "iss" claim of every token supabase issues for this project
        return f"{self.SUPABASE_URL}/auth/v1"

    @property
    def gmail_enabled(self) -> bool:
        return bool(self.GMAIL_ADDRESS and self.GMAIL_APP_PASSWORD)


settings = Settings()
