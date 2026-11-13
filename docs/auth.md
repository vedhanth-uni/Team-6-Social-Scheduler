# Authentication

Login is handled by Supabase. The frontend logs people in and sends the resulting access token
(a JWT) on every API call. The backend never trusts the frontend: it verifies the token itself.

```
browser --signInWithPassword--> Supabase            (gets a session + access token)
browser --Authorization: Bearer <token>--> FastAPI   (verifies it, finds/creates the users row)
```

## Setup

1. **Backend** — copy `backend/.env.example` to `backend/.env` and set `SUPABASE_URL`
   (Supabase dashboard -> Project Settings -> API). The server refuses to start without it.
   `SUPABASE_JWT_SECRET` is only needed if the project still uses the legacy shared JWT secret.
2. **Frontend** — copy `frontend/.env.example` to `frontend/.env.local` and set
   `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` (publishable key only, never the secret key)
   and `VITE_API_URL` if the backend is not on `http://127.0.0.1:8000`.
3. **Existing database** — `users` gained an `auth_id` column. `create_all` does not alter existing
   tables, so either delete your local `backend/scheduler.db` (it is recreated on start) or run:
   ```sql
   ALTER TABLE users ADD COLUMN auth_id TEXT;
   CREATE UNIQUE INDEX ix_users_auth_id ON users (auth_id);
   ```
   The same two statements work on Postgres.

## How the backend checks a token (`backend/app/auth.py`)

- Signature, `exp`, `aud` (`authenticated`) and `iss` (`<SUPABASE_URL>/auth/v1`) must all be valid, and
  `sub` must be present. Only ES256/RS256 (public keys from Supabase's JWKS endpoint, cached) and,
  if `SUPABASE_JWT_SECRET` is set, HS256 are accepted.
- Bad or missing token -> `401`. Supabase unreachable -> `503` (so an outage doesn't log everyone out).
- The first request from a new login creates their `users` row (`auth_id` = token `sub`). An existing
  row with the same email is only linked if Supabase says the email is verified.
- Every route except `/`, `/health` and `/health/db` depends on `current_user`.
  `tests/test_auth.py` fails if a new route is added without it.
- A token stays valid until it expires (1 hour by default) even after sign-out. Lower the JWT expiry in
  the Supabase dashboard if you want a shorter window.

## How the frontend enforces a session (`frontend/src/auth/`)

- `AuthProvider` loads the saved session, asks Supabase's server whether it is still valid (catches
  revoked sessions), then follows login / logout / token refresh events.
- `RequireAuth` wraps protected routes; without a session it redirects to `/` and the login page
  returns the user to where they were headed afterwards. Wrap new pages the same way.
- `apiFetch` (`src/api.ts`) attaches the token, refreshes once and retries on a `401`, and signs the
  user out if Supabase refuses to refresh.

Route guards in the browser are only a convenience; the backend check is what protects the data.
