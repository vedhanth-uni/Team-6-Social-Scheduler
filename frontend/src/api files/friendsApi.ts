import { apiFetch } from './api';

// ---- shapes match backend/app/schemas/friend.py ----

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

// ---- friend requests / friends list (Mikhail's functions) ----

export async function fetchIncomingRequests(): Promise<FriendRequest[]> {
    return apiFetch('/friend-requests?direction=incoming');
}

export async function acceptFriendRequest(requestId: number): Promise<FriendRequest> {
    return apiFetch(`/friend-requests/${requestId}/accept`, { method: 'POST' });
}

export async function declineFriendRequest(requestId: number): Promise<FriendRequest> {
    return apiFetch(`/friend-requests/${requestId}/decline`, { method: 'POST' });
}

export async function fetchFriends(): Promise<Friend[]> {
    return apiFetch('/friends');
}

export async function deleteFriend(profileId: string): Promise<void> {
    await apiFetch(`/friends/${profileId}`, { method: 'DELETE' });
}

// ---- Find Friends ----

export async function searchProfiles(q: string): Promise<ProfileBrief[]> {
    return apiFetch(`/profiles/search?q=${encodeURIComponent(q)}`);
}

export async function sendFriendRequest(username: string, level: FriendLevel): Promise<FriendRequest> {
    return apiFetch('/friend-requests', {
        method: 'POST',
        body: JSON.stringify({ username, level }),
    });
}

// ---- Friends' events on the calendar ----

// matches backend FriendOccurrence
export interface FriendOccurrence {
    event_id: number;
    title: string;
    location: string | null;
    start: string;
    end: string;
    all_day: boolean;
    visibility: 'public' | 'professional' | 'private';
}

// shape the calendar UI works with
export interface CalendarFriend {
    id: string;
    name: string;
    level: FriendLevel;
    color: string;
    borderColor: string;
}

export interface FriendEvent {
    id: number;
    friendId: string;
    weekday: number;          // 1 = Sun ... 7 = Sat
    timeStartPixels: number;  // 1 px = 1 minute from midnight
    timeLengthPixels: number;
    title: string;
    location: string | null;
}

const PALETTE = [
    { color: '#F4A6A6', borderColor: '#D96C6C' },
    { color: '#A6C8F4', borderColor: '#6C9AD9' },
    { color: '#A6F4C1', borderColor: '#6CD99A' },
    { color: '#F4E3A6', borderColor: '#D9C26C' },
    { color: '#D5A6F4', borderColor: '#A66CD9' },
    { color: '#F4C9A6', borderColor: '#D99B6C' },
];

export async function getCalendarFriends(): Promise<CalendarFriend[]> {
    const friends = await fetchFriends();
    return friends.map((f, i) => ({
        id: f.user.id,
        name: f.user.display_name,
        level: f.level,
        ...PALETTE[i % PALETTE.length],
    }));
}

export function startOfWeek(date: Date): Date {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - d.getDay()); // Sunday
    return d;
}

export async function getFriendEvents(friendId: string, weekStart: Date): Promise<FriendEvent[]> {
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 7);

    const qs = new URLSearchParams({
        start: weekStart.toISOString(),
        end: weekEnd.toISOString(),
    });
    const occurrences: FriendOccurrence[] = await apiFetch(`/friends/${friendId}/events?${qs}`);

    return occurrences
        .map((o) => {
            const s = new Date(o.start);
            const e = new Date(o.end);
            return { o, s, e };
        })
        .filter(({ s }) => s >= weekStart) // skip events that began in a previous week
        .map(({ o, s, e }): FriendEvent => ({
            id: o.event_id,
            friendId,
            weekday: s.getDay() + 1,
            timeStartPixels: o.all_day ? 0 : s.getHours() * 60 + s.getMinutes(),
            timeLengthPixels: o.all_day ? 30 : Math.max(15, (e.getTime() - s.getTime()) / 60000),
            title: o.title,
            location: o.location,
        }));
}