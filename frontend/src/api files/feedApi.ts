import { apiFetch } from './api';
import { fetchFriends } from './friendsApi';
import type { FriendOccurrence } from './friendsApi';

// the feed shows friends' events. there's no public-events endpoint, so "the feed" is
// everything your friends have coming up, pulled from GET /friends/{id}/events.

export interface FeedEvent {
    id: string;
    eventId: number;
    hostName: string;
    hostColor: string;
    title: string;
    location: string | null;
    start: Date;
    end: Date;
    allDay: boolean;
}

// a slot of your own time, used to grey out events you're busy for
interface BusySlot {
    start: Date;
    end: Date;
}

export interface FeedData {
    events: FeedEvent[];
    busy: BusySlot[];
}

const PALETTE = ['#F4A6A6', '#A6C8F4', '#A6F4C1', '#F4E3A6', '#D5A6F4', '#F4C9A6'];

const WINDOW_DAYS = 14;

function windowRange(): { start: Date; end: Date } {
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const end = new Date(start);
    end.setDate(end.getDate() + WINDOW_DAYS);
    return { start, end };
}

export async function getFeed(): Promise<FeedData> {
    const { start, end } = windowRange();
    const qs = `start=${start.toISOString()}&end=${end.toISOString()}`;

    const friends = await fetchFriends();

    // each friend's upcoming events, with the friend as the host
    const perFriend = await Promise.all(
        friends.map(async (friend, i) => {
            const occ: FriendOccurrence[] = await apiFetch(`/friends/${friend.user.id}/events?${qs}`);
            return occ.map((o): FeedEvent => ({
                id: `${friend.user.id}-${o.event_id}-${o.start}`,
                eventId: o.event_id,
                hostName: friend.user.display_name,
                hostColor: PALETTE[i % PALETTE.length],
                title: o.title,
                location: o.location,
                start: new Date(o.start),
                end: new Date(o.end),
                allDay: o.all_day,
            }));
        }),
    );

    const events = perFriend.flat().sort((a, b) => a.start.getTime() - b.start.getTime());

    // your own events over the same window, so "For you" can skip the ones you're busy for
    const mine: { start: string; end: string }[] = await apiFetch(`/events?${qs}`);
    const busy = mine.map((o) => ({ start: new Date(o.start), end: new Date(o.end) }));

    return { events, busy };
}

// true if this event's time clashes with any of your own events
export function clashesWithBusy(event: FeedEvent, busy: BusySlot[]): boolean {
    return busy.some((slot) => event.start < slot.end && slot.start < event.end);
}

export async function joinEvent(eventId: number): Promise<void> {
    await apiFetch(`/events/${eventId}/join`, { method: 'POST' });
}

export async function leaveEvent(eventId: number): Promise<void> {
    await apiFetch(`/events/${eventId}/join`, { method: 'DELETE' });
}
