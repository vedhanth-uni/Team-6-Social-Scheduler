import './DashboardPage.css';
import {useState} from 'react';
import ViewDropdown from './components/ViewDropdown';
import PrivacyToggle from './components/PrivacyToggle';
import AddEventForm from './AddEventForm';
import FindFriend from './components/FindFriend';
import ImportButton from './components/ImportButton';
import { createCalendarEvent } from './eventApi';
import type { CalendarEvent } from './AddEventForm';

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
                                onSave={() => setShowEventForm(false)}
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
function CalendarEvents() {

    const events = [
        {id: 1, x: 2, y: 3, title: "Gym Sesh", privacyTag: "Private", location: "Lederle"}, 
        {id: 2, x: 3, y: 4, title: "Partyyy", privacyTag: "Shared", location: "In the Bush"}, 
        {id: 3, x: 1, y: 5, title: "Class", privacyTag: "Professional", location: "White House"}, 
    ]


    return (
        <div className='canvas'>
            {events.map((event) => (
                <div
                key={event.id}
                className='calendar-event'
                style={{
                    left: `${event.x}`,
                    top: `${event.y}%`,
                }}
                >
                    <h1> {event.title} </h1>
                    <p> {event.location} </p>
                </div>    
            ))}
        </div>
    )
}

export default DashboardPage;