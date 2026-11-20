
import { supabase } from './supabaseClient';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

export async function apiFetch(path: string, options: RequestInit = {}) {
    const { data } = await supabase.auth.getSession();
    const session = data.session;

    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string>),
    };
    // For file uploads the browser must set the multipart boundary itself
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    if (session) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
    }

    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail;
        // FastAPI validation errors (422) return detail as a list
        const msg = typeof detail === 'string'
            ? detail
            : Array.isArray(detail) ? detail.map((d: { msg: string }) => d.msg).join(', ') : null;
        throw new Error(msg ?? `Request failed (${res.status})`);
    }
    return res.status === 204 ? null : res.json();
}