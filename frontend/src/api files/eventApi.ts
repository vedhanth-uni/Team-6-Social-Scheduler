import { apiFetch } from "./api";
import type { CalendarEvent } from "../AddEventForm";

export async function createCalendarEvent(event: CalendarEvent) {
    const body = {
        title: event.title,
        description: event.description || null,
        location: event.location || null,
        all_day: event.allDay,
        start: event.allDay ? `${event.date}T00:00:00` : `${event.date}T${event.startTime}:00`,
        end: event.allDay ? null : `${event.date}T${event.endTime}:00`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        visibility: event.visibility,
        rrule: event.rrule,
    };

    return apiFetch('/events', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

// apiFetch already throws on any non-2xx response, so no res.ok checks here
export async function deleteCalendarEvent(eventId: number) {
    await apiFetch(`/events/${eventId}`, { method: "DELETE" });
}

export async function updateCalendarEvent(eventId: number, event: CalendarEvent) {
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
    return apiFetch(`/events/${eventId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
    });
}