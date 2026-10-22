import { useState, type SubmitEvent  } from 'react';
//double check - should add event have visibility (public/private/professional for each event)?

//information to be collected for one event
export interface CalendarEvent {
    title: string;
    date: string;
    allDay: boolean;
    startTime: string;
    endTime: string;
    location: string;
    description: string;
    visibility: 'public' | 'private' | 'professional';
}

//info the parent component passes to the form
interface AddEventFormProps {
    onSave: (event: CalendarEvent) => void;
    onCancel: () => void;
}

function AddEventForm({ onSave, onCancel }: AddEventFormProps) {
    //store current values of the form
    const [title, setTitle] = useState('');
    const [date, setDate] = useState('');
    const [allDay, setAllDay] = useState(false);
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');
    const [location, setLocation] = useState('');
    const [description, setDescription] = useState('');
    const [visibility, setVisibility] = useState<CalendarEvent['visibility']>('private');

    //call when user submits form
    function handleSubmit(event: SubmitEvent <HTMLFormElement>) {
        event.preventDefault();

    //check that the events times are logical unless it's an all-day event
    if (!allDay && startTime >= endTime) {
        alert('The end time must be later than the start time.');
        return;
    }

    //package the form values into one event object
    const newEvent: CalendarEvent = {
        title,
        date,
        allDay,
        startTime: allDay ? '' : startTime,
        endTime: allDay ? '' : endTime,
        location,
        description,
        visibility,
    };

    //now parent component can handle saved event
    onSave(newEvent);
  }

    return (
        <div
            className="event-modal-backdrop"
            //clicking outside the form should close the popup
            onMouseDown={(event) => {
                if (event.target === event.currentTarget) {
                onCancel();
                }
            }}
        >
        <section
            className="event-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="event-form-title"
        >
        <h2 id="event-form-title">Add New Event</h2>

        <form onSubmit={handleSubmit}>
            <div className="form-group">
            <label htmlFor="event-title">Event Name *</label>
            <input
                id="event-title"
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Enter event name"
                required
            />
           </div>

            <div className="form-group">
                <label htmlFor="event-date">Date *</label>
                <input
                    id="event-date"
                    type="date"
                    value={date}
                    onChange={(event) => setDate(event.target.value)}
                    required
                />
            </div>

            <div className="form-group">
                <label htmlFor="event-all-day">
                <input
                    id="event-all-day"
                    type="checkbox"
                    checked={allDay}
                    onChange={(event) => setAllDay(event.target.checked)}
                />
                All-day event
                </label>
            </div>

            {/* Only display the time inputs for timed events, events not lasting all-day*/}
            {!allDay && (
                <>
                <div className="form-group">
                    <label htmlFor="event-start-time">Start Time *</label>
                    <input
                        id="event-start-time"
                        type="time"
                        value={startTime}
                        onChange={(event) => setStartTime(event.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="event-end-time">End Time *</label>
                    <input
                        id="event-end-time"
                        type="time"
                        value={endTime}
                        onChange={(event) => setEndTime(event.target.value)}
                        required
                    />
                </div>
                </>
            )}

            <div className="form-group">
                <label htmlFor="event-location">Location</label>
                <input
                    id="event-location"
                    type="text"
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                    placeholder="Location (optional)"
                />
            </div>

            <div className="form-group">
                <label htmlFor="event-description">Description</label>
                <textarea
                    id="event-description"
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    placeholder="Additional details (optional)"
                    rows={3}
                />
            </div>

            <div className="form-group">
                <label htmlFor="event-visibility">Visibility</label>
                <select
                    id="event-visibility"
                    value={visibility}
                    onChange={(event) =>
                        setVisibility(event.target.value as CalendarEvent['visibility'])
                    }
                >
                <option value="public">Public</option>
                <option value="private">Private</option>
                <option value="professional">Professional</option>
                </select>
            </div>

            <div className="event-form-buttons">
                <button type="submit">Save Event</button>
                <button type="button" onClick={onCancel}>
                    Cancel
                </button>
            </div>
        </form>
    </section>
    </div>
  );
}

export default AddEventForm;