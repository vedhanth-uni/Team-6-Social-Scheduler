import './DashboardPage.css';
import {useState} from 'react';
import ViewDropdown from './components/ViewDropdown';
import PrivacyToggle from './components/PrivacyToggle';
import AddEventForm from './AddEventForm';
import FindFriend from './components/FindFriend';
import ImportButton from './components/ImportButton';
import { createCalendarEvent } from './eventApi';
import type { CalendarEvent } from './AddEventForm';
import ProfilePopup from './components/ProfilePopup';

function DashboardPage() {
    const currentMonth = new Date().toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });

    const calendarId = 1; //temporary calendar Id (replace with actual Id later)
    const [currentView, setCurrentView] = useState('Weekly');
    const [selectedPrivacy, setSelectedPrivacy] = useState('Private');

    //tracks whether add event popup is open
    const [showEventForm, setShowEventForm] = useState(false);


    async function handleSaveEvent(event: CalendarEvent){
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

                    <FindFriend/>
                    <ImportButton/>

                    <div className='add-class-button'>
                        {/* Button to open the popup form for adding event */}
                        <button
                            type="button"
                            onClick={() => setShowEventForm(true)}
                        >
                            Add Event
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

function CalendarEvents() {

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