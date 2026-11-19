import { supabase } from './supabaseClient';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

export async function apiFetch(path: string, options: RequestInit = {}) {
    const { data } = await supabase.auth.getSession();
    const session = data.session;

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    };
    if (session) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
        headers['X-Dev-User-Id'] = session.user.id;
    }

    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Request failed (${res.status})`);
    }
    return res.status === 204 ? null : res.json();
}
