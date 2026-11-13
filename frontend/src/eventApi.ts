import { apiFetch } from "./api";
import type { CalendarEvent } from "./AddEventForm";

export async function createCalendarEvent(
    calendarId: number,
    event: CalendarEvent
) {
    const body = {
        title: event.title,
        description: event.description || null,
        location: event.location || null,
        all_day: event.allDay,
        start: event.allDay ? `${event.date}T00:00:00` : `${event.date}T${event.startTime}:00`,
        end: event.allDay ? null : `${event.date}T${event.endTime}:00`,
        timezone: null,
        visibility: event.visibility,

    };

    return apiFetch(`/calendars/${calendarId}/events`,{
        method: 'POST',
        body: JSON.stringify(body),
    });
}

export interface Calendar {
    id: number;
    name: string;
    is_primary: boolean;
    my_access: 'owner' | 'editor' | 'viewer';
}

// The calendar new events go into: the user's own primary calendar. New accounts have none yet,
// so make one. Shared in-flight so React StrictMode's double effect doesn't create two.
let inflight: Promise<Calendar> | null = null;

async function loadPrimaryCalendar(): Promise<Calendar> {
    const calendars: Calendar[] = await apiFetch('/calendars');
    const mine = calendars.filter((c) => c.my_access === 'owner');
    const primary = mine.find((c) => c.is_primary) ?? mine[0];
    if (primary) return primary;
    return apiFetch('/calendars', {
        method: 'POST',
        body: JSON.stringify({ name: 'My Calendar' }),
    });
}

export function getPrimaryCalendar(): Promise<Calendar> {
    inflight ??= loadPrimaryCalendar().finally(() => { inflight = null; });
    return inflight;
}
