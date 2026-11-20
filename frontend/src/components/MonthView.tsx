import type { CSSProperties } from 'react';
import './MonthView.css';
import type { CalendarFriend, FriendEvent } from '../api files/friendsApi';
import type { OwnEvent } from '../mockEvents';
import { addDays, buildMonthGrid, formatDateKey, formatMinutes, isSameDay, startOfWeek } from '../lib/dates';

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MAX_EVENTS_PER_DAY = 3;

interface DayEvent {
    key: string;
    title: string;
    startMinutes: number;
    ownEvent: OwnEvent | null; //null for friend events, which can't be edited
    style?: CSSProperties;
}

interface MonthViewProps {
    viewDate: Date; //any day in the month to show
    now: Date;
    friends: CalendarFriend[];
    events: OwnEvent[]; //already filtered by the privacy toggle
    friendEvents: FriendEvent[]; //already filtered by the friends checklist
    onSelectEvent: (event: OwnEvent) => void;
}

//groups events by "YYYY-MM-DD", sorted by start time within each day
function buildEventsByDate(
    events: OwnEvent[],
    friendEvents: FriendEvent[],
    friends: CalendarFriend[],
    now: Date,
): Map<string, DayEvent[]> {
    const eventsByDate = new Map<string, DayEvent[]>();
    const addToDay = (dateKey: string, dayEvent: DayEvent) => {
        eventsByDate.set(dateKey, [...(eventsByDate.get(dateKey) ?? []), dayEvent]);
    };

    //TODO(misha): own events are still mock data with only a weekday, so they're placed in the current week
    const currentWeekStart = startOfWeek(now);
    for (const event of events) {
        addToDay(formatDateKey(addDays(currentWeekStart, event.weekday - 1)), { //weekday is 1-7 (Sun-Sat)
            key: `own-${event.id}`,
            title: event.title,
            startMinutes: event.timeStartPixels,
            ownEvent: event,
        });
    }

    for (const event of friendEvents) {
        const friend = friends.find((f) => f.id === event.friendId);
        addToDay(event.date, {
            key: `friend-${event.friendId}-${event.id}-${event.date}-${event.timeStartPixels}`,
            title: event.title,
            startMinutes: event.timeStartPixels,
            ownEvent: null,
            style: { //same colors as friend events in the weekly view
                backgroundColor: friend ? `${friend.color}A6` : "#EEEEEE",
                borderColor: friend ? `${friend.borderColor}A6` : "#CCCCCC",
            },
        });
    }

    for (const dayEvents of eventsByDate.values()) {
        dayEvents.sort((a, b) => a.startMinutes - b.startMinutes);
    }
    return eventsByDate;
}

function MonthView({viewDate, now, friends, events, friendEvents, onSelectEvent}: MonthViewProps) {
    const cells = buildMonthGrid(viewDate);
    const eventsByDate = buildEventsByDate(events, friendEvents, friends, now);

    return (
        <div className='calendar month-view'>
            <div className='week-header'>
                {WEEKDAYS.map((day) => (
                    <div className='weekday' key={day}>{day}</div>
                ))}
            </div>
            <div className='month-grid'>
                {cells.map((date) => {
                    const dateKey = formatDateKey(date);
                    const dayEvents = eventsByDate.get(dateKey) ?? [];
                    const isOutsideMonth = date.getMonth() !== viewDate.getMonth();
                    const hiddenCount = dayEvents.length - MAX_EVENTS_PER_DAY;

                    return (
                        <div key={dateKey} className={isOutsideMonth ? 'month-cell outside-month' : 'month-cell'}>
                            <span className={isSameDay(date, now) ? 'day-number today' : 'day-number'}>
                                {date.getDate()}
                            </span>

                            {dayEvents.slice(0, MAX_EVENTS_PER_DAY).map((dayEvent) => {
                                const label = (
                                    <>
                                        <span className='month-event-time'>{formatMinutes(dayEvent.startMinutes)}</span>
                                        {dayEvent.title}
                                    </>
                                );
                                const { ownEvent } = dayEvent;
                                return ownEvent ? (
                                    <button
                                        key={dayEvent.key}
                                        type='button'
                                        className='calendar-event month-event'
                                        onClick={() => onSelectEvent(ownEvent)}
                                    >
                                        {label}
                                    </button>
                                ) : (
                                    <div
                                        key={dayEvent.key}
                                        className='calendar-event friend-event month-event'
                                        style={dayEvent.style}
                                    >
                                        {label}
                                    </div>
                                );
                            })}

                            {hiddenCount > 0 && (
                                <span className='month-more'>+{hiddenCount} more</span>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default MonthView;
