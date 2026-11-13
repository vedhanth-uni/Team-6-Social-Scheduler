import './DashboardPage.css';
import {useEffect, useState} from 'react';
import ViewDropdown from './components/ViewDropdown';
import PrivacyToggle from './components/PrivacyToggle';
import AddEventForm from './AddEventForm';
import FindFriend from './components/FindFriend';
import ImportButton from './components/ImportButton';
import { createCalendarEvent, getPrimaryCalendar } from './eventApi';
import type { CalendarEvent } from './AddEventForm';
import ProfilePopup from './components/ProfilePopup';
import FriendsChecklist from './components/FriendsChecklist';

function DashboardPage() {
    const currentMonth = new Date().toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });
    //the logged-in user's own calendar, loaded from the backend (null until it arrives)
    const [calendarId, setCalendarId] = useState<number | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [currentView, setCurrentView] = useState('Weekly');
    const [selectedPrivacy, setSelectedPrivacy] = useState<string[]>([]);

    //tracks whether add event popup is open
    const [showEventForm, setShowEventForm] = useState(false);


    useEffect(() => {
        getPrimaryCalendar()
            .then((cal) => setCalendarId(cal.id))
            .catch((error: Error) => setLoadError(error.message));
    }, []);

    async function handleSaveEvent(event: CalendarEvent){
        if (calendarId === null) return;
        try{
            await createCalendarEvent(calendarId, event);
            setShowEventForm(false);

        } catch(error){
            console.error('Error creating the event:', error);
        }
    }

    return (
        <div className='dashboard'>
            <header className='toolbar'>
                <h1>Social Calendar</h1>
                <div className = "month-title">
                    <input
                        id ="current-month"
                        type="text"
                        value={currentMonth}
                        readOnly
                    />
                </div>
                <ProfilePopup/>
            </header>
            {loadError && <p role="alert">Could not load your calendar: {loadError}</p>}

            <div className='content'>
                <aside className='sidebar'>
                    <ViewDropdown 
                        currentView = {currentView} 
                        setCurrentView = {setCurrentView}
                    />

                    <PrivacyToggle 
                        selectedPrivacy = {selectedPrivacy} 
                        setSelectedPrivacy={setSelectedPrivacy}
                    />
                    <FriendsChecklist/>

                    <FindFriend/>
                    <ImportButton/>

                    <div className='add-class-button'>
                        {/* Button to open the popup form for adding event */}
                        <button
                            type="button"
                            onClick={() => setShowEventForm(true)}
                        >
                            + Add Event
                        </button>
                        {/* Display the form only when the popup is open */}
                        {showEventForm && (
                            <AddEventForm
                                onSave={handleSaveEvent}
                                onCancel={() => setShowEventForm(false)}
                            />
                        )}
                    </div>
                </aside>

                <div className='calendar-container'> 
                    <CalendarEvents/>
                </div>
            </div>
        </div>
    )
}

//TODO: add overlay for add event button to the calendar container.

//TODO: create function that gets event data from database and translates it to coordinates.
//you can then pass the events list as an arg to CalendarEvents()
//notice you need to filter why which radial button is chosen
//def filter in another function, maybe in the same file as the one that gets the data from the database? but like what about caching?
//when do we check again for data... probably when an event has been added or deleted so Ill have to make sure it doesn't do it too often

//TODO: add function that translates the time to an attribute on the style component
//TODO: make sure that event is on line exactly because YAY! confirmed line is exactly on grid lines
//TODO: change to not military time lol

function CalendarEvents() {
    const weekdays = [
        "Sun",
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat"
    ]; 

    const [currDate] = useState(new Date()); //if we add a prev/next week buttons, we would need setCurrDate 
    const weekDate = weekdays.map((_, i)=>{
        const date = new Date(currDate);
        date.setDate(date.getDate()-date.getDay()+i); //getDate gets day number, getDay gets weekday, + index updates the dates  
        return date;
    });

    //practice data
    const events = [
        {id: 1, weekday: 2, timeStart: 11.50, timeEnd: 12.30, title: "Gym Sesh", privacyTag: "Private", location: "Lederle"}, 
        {id: 2, weekday: 1, timeStart: 4, timeEnd: 5, title: "Partyyy", privacyTag: "Shared", location: "At My House"}, 
        {id: 3, weekday: 4, timeStart: 3.45, timeEnd: 5.45, title: "Class", privacyTag: "Professional", location: "White House"}, 
    ]

    //array from 2-24
    const hours = Array.from({ length: 24 }, (_, i) => i+1);



    //layer that allows row line styling and hours written on calendar
    const labels = [];

    for (let i = 1; i <= 7; i++) {
        labels.push(
            hours.map((hour) => (
                    <div 
                        className='hour-row' 
                        id="first-row" key={1} 
                        style={{ 
                            gridColumnStart: i, 
                            gridRowStart: hour, 
                            borderRight: i === 7 ? 'none': '1px solid gray',
                            borderTop: hour === 1 ? 'none': '1px solid gray'
                    }}>
                        <div className='time-label'>
                            {hour}:00
                        </div>
                    </div>
            ))
        );
    }


    return (
        <div className='calendar'>
            <div className = "week-header">
                {weekdays.map((day, i)=>(
                    <div className = "weekday" key={day}>{day} {weekDate[i].getDate()}</div> //displays the days of the week as a header 
                ))}
            </div>
            <div className='canvas'>
                {labels}

                {events.map((event) => (
                    <div
                    key={event.id}
                    className='calendar-event'
                    style={{
                        gridColumnStart: `${event.weekday}`,
                        gridColumnEnd: `${event.weekday + 1}`,
                        height: "100px"
                    }}
                    >
                        <h1> {event.title} </h1>
                        <p> {event.location} </p>
                    </div>    
                ))}
            </div>
        </div>
    )
}

export default DashboardPage;

//recall JSX needs an expression, not a statement. 