import './DashboardPage.css';
import { useEffect, useState } from 'react';
import ViewDropdown from './components/ViewDropdown';
import PrivacyToggle from './components/PrivacyToggle';
import AddEventForm from './AddEventForm';
import FindFriend from './components/FindFriend';
import ImportButton from './components/ImportButton';
import { createCalendarEvent, deleteCalendarEvent, updateCalendarEvent } from './api files/eventApi';
import { getCalendarFriends, getFriendEvents, startOfWeek } from './api files/friendsApi';
import type { CalendarFriend, FriendEvent } from './api files/friendsApi';
import type { CalendarEvent } from './AddEventForm';
import ProfilePopup from './components/ProfilePopup';
import FriendsChecklist from './components/FriendsChecklist';
import EditEventForm from './components/EditEventForm';

function DashboardPage() {
    const currentMonth = new Date().toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });
    const [currentView, setCurrentView] = useState('Weekly');
    const [selectedPrivacy, setSelectedPrivacy] = useState<string[]>([]);
    const [selectedFriends, setSelectedFriends] = useState<string[]>([]); //friend ids (UUIDs) ticked in FriendsChecklist
    const [friends, setFriends] = useState<CalendarFriend[]>([]);

    useEffect(() => {
        getCalendarFriends()
            .then(setFriends)
            .catch((error) => console.error('Error loading friends:', error));
    }, []);

    const handleFriendSelection = (friendIds: string[]) => {
        setSelectedFriends(friendIds);
    }

    //tracks whether add event popup is open
    const [showEventForm, setShowEventForm] = useState(false);

    async function handleSaveEvent(event: CalendarEvent) {
        try {
            await createCalendarEvent(event);
            setShowEventForm(false);
        } catch (error) {
            console.error('Error creating the event:', error);
        }
    }

    return (
        <div className='dashboard'>
            <header className='toolbar'>
                <img
                    src="/logo_small.svg"
                    className="dash-logo"
                />
                <div className="month-title">
                    <input
                        id="current-month"
                        type="text"
                        value={currentMonth}
                        readOnly
                    />
                </div>
                <FindFriend />
                <ImportButton />
                <ProfilePopup />
            </header>

            <div className='content'>
                <aside className='sidebar'>
                    <ViewDropdown
                        currentView={currentView}
                        setCurrentView={setCurrentView}
                    />

                    <PrivacyToggle
                        selectedPrivacy={selectedPrivacy}
                        setSelectedPrivacy={setSelectedPrivacy}
                    />
                    <FriendsChecklist
                        friends={friends}
                        onSelectionChange={handleFriendSelection}
                    />

                    <div className='add-class-button'>
                        <button
                            type="button"
                            onClick={() => setShowEventForm(true)}
                        >
                            + Add Event
                        </button>
                        {showEventForm && (
                            <AddEventForm
                                onSave={handleSaveEvent}
                                onCancel={() => setShowEventForm(false)}
                            />
                        )}
                    </div>
                </aside>

                <div className='calendar-container'>
                    <CalendarEvents
                        friends={friends}
                        selectedFriends={selectedFriends}
                        privacyToggleSetting={selectedPrivacy}
                    />
                </div>
            </div>
        </div>
    )
}

type EventProps = {
    friends: CalendarFriend[],
    selectedFriends: string[],
    privacyToggleSetting: string[];
}

function CalendarEvents({ friends, selectedFriends, privacyToggleSetting }: EventProps) {
    const [selectedEvent, setSelectedEvent] = useState<{
        id: number;
        title: string;
        location: string;
        privacyTag: string;
        date: string;
        allDay: boolean;
        startTime: string;
        endTime: string;
        description: string;
    } | null>(null);

    const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

    const [currDate] = useState(new Date()); //if we add prev/next week buttons, we would need setCurrDate
    const weekDate = weekdays.map((_, i) => {
        const date = new Date(currDate);
        date.setDate(date.getDate() - date.getDay() + i);
        return date;
    });

    //fake event data (your own events are not wired up yet)
    const [events, setEvents] = useState([
        {id: 1, weekday: 2, timeStartPixels: 30, timeLengthPixels: 90, title: "Gym Sesh", privacyTag: "Private", location: "Lederle", date: "2026-11-18", allDay: true, startTime:"", endTime:"", description:"Gym Sesh at Lederle!"},
        {id: 2, weekday: 1, timeStartPixels: 1140, timeLengthPixels: 180, title: "Partyyy", privacyTag: "Close", location: "At My House", date: "2026-11-18", allDay: true, startTime:"", endTime:"", description:"Party at my house!"},
        {id: 3, weekday: 4, timeStartPixels: 885, timeLengthPixels: 50, title: "Class", privacyTag: "Professional", location: "White House", date: "2026-11-18", allDay: true, startTime:"", endTime:"", description:"Class time :)"},
    ]);

    //real friends' events, loaded from the backend for the ticked friends
    const [friendEvents, setFriendEvents] = useState<FriendEvent[]>([]);

    useEffect(() => {
        if (selectedFriends.length === 0) return; // nothing to fetch; render filter hides old events

        let cancelled = false; //ignore results from an outdated selection
        const weekStart = startOfWeek(currDate);
        Promise.allSettled(selectedFriends.map((id) => getFriendEvents(id, weekStart)))
            .then((results) => {
                if (cancelled) return;
                const loaded: FriendEvent[] = [];
                results.forEach((r) => {
                    if (r.status === 'fulfilled') loaded.push(...r.value);
                    else console.error('Error loading friend events:', r.reason);
                });
                setFriendEvents(loaded); // runs asynchronously in .then, so the lint rule is fine with it
            });
        return () => { cancelled = true; };
    }, [selectedFriends, currDate]);

    async function handleDeleteEvent(eventId: number) {
        try {
            await deleteCalendarEvent(eventId);
            setEvents(events.filter((event) => event.id !== eventId));
            setSelectedEvent(null);
        }
        catch (error) {
            console.error("Error deleting event ", error);
        }
    }

    async function handleUpdateEvent(updatedEvent: CalendarEvent) {
        if (!selectedEvent) return;
        try {
            await updateCalendarEvent(selectedEvent.id, updatedEvent);
            setEvents((prevEvents) =>
                prevEvents.map((event) =>
                    event.id === selectedEvent.id
                        ? {
                            ...event,
                            title: updatedEvent.title,
                            location: updatedEvent.location,
                            description: updatedEvent.description,
                            privacyTag: updatedEvent.visibility,
                            allDay: updatedEvent.allDay,
                        }
                        : event
                )
            );
            setSelectedEvent(null);
        } catch (error) {
            console.error("Error updating event:", error);
        }
    }

    const hours = Array.from({ length: 24 }, (_, i) => i + 1);
    //row 1 starts at midnight (1px = 1 min from the top), so the first label is 12AM
    const hourLabels = ["12AM", "1AM", "2AM", "3AM", "4AM", "5AM", "6AM", "7AM", "8AM", "9AM", "10AM", "11AM",
        "12PM", "1PM", "2PM", "3PM", "4PM", "5PM", "6PM", "7PM", "8PM", "9PM", "10PM", "11PM"];

    //layer that allows row line styling and hours written on calendar
    const labels = [];

    for (let i = 1; i <= 7; i++) {
        labels.push(
            hours.map((hour) => (
                <div
                    className='hour-row'
                    id="first-row"
                    key={`${i}-${hour}`}
                    style={{
                        gridColumnStart: i,
                        gridRowStart: hour,
                        borderRight: i === 7 ? 'none' : '1px solid gray',
                        borderTop: hour === 1 ? 'none' : '1px solid gray'
                    }}>
                    <div className='time-label'>
                        {hourLabels[hour - 1]}
                    </div>
                </div>
            ))
        );
    }

    return (
        <div className='calendar'>
            <div className="week-header">
                {weekdays.map((day, i) => (
                    <div className="weekday" key={day}>{day} {weekDate[i].getDate()}</div>
                ))}
            </div>
            <div className='canvas'>
                {labels}

                {events.map((event) => (
                    privacyToggleSetting.includes(event.privacyTag) ? (
                        <div
                            key={event.id}
                            className='calendar-event'
                            onClick={() => setSelectedEvent(event)}
                            style={{
                                gridColumnStart: `${event.weekday}`,
                                gridColumnEnd: `${event.weekday + 1}`,
                                top: `${event.timeStartPixels}px`, //1 px = 1 min
                                height: `${event.timeLengthPixels}px`
                            }}
                        >
                            <h1> {event.title} </h1>
                            <p> {event.location} </p>
                        </div>
                    ) : (undefined)
                ))}

                {friendEvents
                    .filter((event) => selectedFriends.includes(event.friendId))
                    .map((event) => {
                        const friend = friends.find((f) => f.id === event.friendId);

                        return (
                            <div
                                key={`${event.friendId}-${event.id}-${event.weekday}-${event.timeStartPixels}`}
                                className='calendar-event friend-event'
                                style={{
                                    gridColumnStart: `${event.weekday}`,
                                    gridColumnEnd: `${event.weekday + 1}`,
                                    top: `${event.timeStartPixels}px`,
                                    height: `${event.timeLengthPixels}px`,
                                    backgroundColor: friend ? `${friend.color}A6` : "#EEEEEE", //A6 = 65% opacity
                                    borderColor: friend ? `${friend.borderColor}A6` : "#CCCCCC"
                                }}
                            >
                                <h1>{event.title}</h1>
                                <p>{event.location}</p>
                            </div>
                        );
                    })}

                {selectedEvent && (
                    <EditEventForm
                        event={selectedEvent}
                        onCancel={() => setSelectedEvent(null)}
                        onDelete={handleDeleteEvent}
                        onUpdate={handleUpdateEvent}
                    />
                )}
            </div>
        </div>
    )
}

export default DashboardPage;