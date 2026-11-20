import { apiFetch } from './api';

// shapes match backend/app/schemas/friend.py

export type FriendLevel = 'close' | 'professional';

export interface ProfileBrief {
    id: string;
    username: string;
    display_name: string;
}

export interface FriendRequest {
    id: number;
    level: FriendLevel;
    status: 'pending' | 'accepted' | 'declined';
    sender: ProfileBrief;
    recipient: ProfileBrief;
    created_at: string;
}

export interface Friend {
    user: ProfileBrief;
    level: FriendLevel;
    since: string;
}

export async function fetchIncomingRequests(): Promise<FriendRequest[]> {
    return apiFetch('/friend-requests?direction=incoming');
}

export async function acceptFriendRequest(requestId: number): Promise<FriendRequest> {
    return apiFetch(`/friend-requests/${requestId}/accept`, { method: 'POST' });
}

// the backend deletes the row on decline, so the request just disappears
export async function declineFriendRequest(requestId: number): Promise<FriendRequest> {
    return apiFetch(`/friend-requests/${requestId}/decline`, { method: 'POST' });
}

export async function fetchFriends(): Promise<Friend[]> {
    return apiFetch('/friends');
}

// unfriending deletes the row, so it's removed for both people
export async function deleteFriend(profileId: string): Promise<void> {
    await apiFetch(`/friends/${profileId}`, { method: 'DELETE' });
}
