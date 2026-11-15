import { apiFetch } from './api';

export type Friend = {
    id: string;
    name: string;
    level: string;
    color: string;
    borderColor: string;
};

export type FriendEvent = {
    id: string;
    friendId: string;
    weekday: number;
    timeStartPixels: number;
    timeLengthPixels: number;
    title: string;
    location: string | null;
};

type FriendResponse = {
    user: { id: string; username: string; display_name: string };
    level: string;
};

type OccurrenceResponse = {
    event_id: number;
    title: string;
    location: string | null;
    start: string;
    end: string;
    all_day: boolean;
};

//same colors the checklist used before, friends get one each in order
const colors = [
    { color: '#F4A6A6', borderColor: '#D98282' },
    { color: '#B5D6A7', borderColor: '#7EAB6A' },
    { color: '#D2B5E8', borderColor: '#AB93BD' },
    { color: '#A6C8F4', borderColor: '#84A0C4' },
    { color: '#E9B949', borderColor: '#C7962F' },
    { color: '#A6D9D1', borderColor: '#86B0AA' },
];

const DAY_MINUTES = 24 * 60;

export async function getFriends(): Promise<Friend[]> {
    const data: FriendResponse[] = await apiFetch('/friends');
    return data.map((f, i) => ({
        id: f.user.id,
        name: f.user.display_name,
        level: f.level,
        ...colors[i % colors.length],
    }));
}

export function startOfWeek(date: Date) {
    const d = new Date(date);
    d.setDate(d.getDate() - d.getDay());
    d.setHours(0, 0, 0, 0);
    return d;
}

//the calendar is 1px per minute and sunday is column 1
function toCalendarEvent(friendId: string, o: OccurrenceResponse): FriendEvent {
    const start = new Date(o.start);
    const end = new Date(o.end);
    const minutes = start.getHours() * 60 + start.getMinutes();
    const length = o.all_day ? 30 : Math.round((end.getTime() - start.getTime()) / 60000);

    return {
        id: `${friendId}-${o.event_id}-${o.start}`,
        friendId,
        weekday: start.getDay() + 1,
        timeStartPixels: o.all_day ? 0 : minutes,
        timeLengthPixels: Math.max(15, Math.min(length, DAY_MINUTES - minutes)),
        title: o.title,
        location: o.location,
    };
}

export async function getFriendEvents(friendId: string, weekStart: Date): Promise<FriendEvent[]> {
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 7);
    const query = new URLSearchParams({ start: weekStart.toISOString(), end: weekEnd.toISOString() });
    const data: OccurrenceResponse[] = await apiFetch(`/friends/${friendId}/events?${query}`);
    //skip ones that started last week and run into this one, they'd land on the wrong day
    return data
        .filter((o) => new Date(o.start) >= weekStart)
        .map((o) => toCalendarEvent(friendId, o));
}
