import { apiFetch } from './api';

export interface ImportResult {
    created: number;
    duplicates: number;
    event_ids: number[];
    skipped: unknown[];
    failed: unknown[];
    warnings: string[];
}

export async function importSchedule(
    file: File,
    visibility: 'public' | 'professional' | 'private' = 'private',
): Promise<ImportResult> {
    const form = new FormData();
    form.append('file', file); // field name must be "file"

    const qs = new URLSearchParams({
        default_tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
        visibility,
    });
    return apiFetch(`/events/import?${qs}`, { method: 'POST', body: form });
}