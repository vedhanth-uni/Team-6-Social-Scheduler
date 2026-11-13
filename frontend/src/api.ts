import { supabase } from './supabaseClient';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

export class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

// FastAPI sends errors as {"detail": "text"} or, for bad input, {"detail": [{"msg": ...}, ...]}
function errorMessage(body: unknown, status: number): string {
    const detail = (body as { detail?: unknown } | null)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail.map((d) => (d as { msg?: string }).msg ?? 'Invalid input').join(', ');
    }
    return `Request failed (${status})`;
}

async function request(path: string, options: RequestInit, token: string): Promise<Response> {
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    // only JSON bodies get a JSON content type -- a file upload (FormData) must set its own boundary
    if (typeof options.body === 'string' && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }
    try {
        return await fetch(`${API_URL}${path}`, { ...options, headers });
    } catch {
        throw new ApiError('Cannot reach the server. Is the backend running?', 0);
    }
}

// Calls the backend as the logged-in user. The backend verifies the token on every request;
// we never send anything that identifies the user except that token.
export async function apiFetch(path: string, options: RequestInit = {}) {
    // getSession() hands back a fresh token (it refreshes an expired one automatically)
    const { data } = await supabase.auth.getSession();
    if (!data.session) throw new ApiError('You are not signed in', 401);

    let res = await request(path, options, data.session.access_token);

    if (res.status === 401) {
        // the token may have expired in flight: refresh once and retry
        const refreshed = await supabase.auth.refreshSession();
        if (refreshed.error || !refreshed.data.session) {
            // Supabase refused to renew it, so the session is really over -> log out, which
            // sends the user to the login page
            await supabase.auth.signOut();
            throw new ApiError('Your session has expired. Please log in again.', 401);
        }
        res = await request(path, options, refreshed.data.session.access_token);
    }

    if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new ApiError(errorMessage(body, res.status), res.status);
    }
    return res.status === 204 ? null : res.json();
}
