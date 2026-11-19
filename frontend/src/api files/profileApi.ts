import { apiFetch } from './api';

export interface UserProfile {
    id: string;
    username: string;
    display_name: string;
    email: string | null;
    calendar_id: number;
}

export async function getMyProfile(): Promise<UserProfile> {
    return apiFetch('/me');
}
