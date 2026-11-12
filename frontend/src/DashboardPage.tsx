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
import FriendsChecklist from './components/FriendsChecklist';
import {friends} from "./components/FriendsChecklist";

function DashboardPage() {
    const currentMonth = new Date().toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });
    const calendarId = 1; //temporary calendar Id (replace with actual Id later)
    const [currentView, setCurrentView] = useState('Weekly');
    const [selectedPrivacy, setSelectedPrivacy] = useState<string[]>([]);
    const [selectedFriends, setSelectedFriends] = useState<number[]>([]); //stores selected friend ids from FriendsChecklist.tsx

    const handleFriendSelection = (friendIds: number[])=>{
        setSelectedFriends(friendIds); //receives the ids and updates state
    }

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
                {/* <h1>Social <br/> Calendar</h1> */}
                <img
                    src="/logo_small.svg"
                    className="dash-logo"
                />
                <div className = "month-title">
                    <input
                        id ="current-month"
                        type="text"
                        value={currentMonth}
                        readOnly
                    />
                </div>
                <FindFriend/>
                <ImportButton/>
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
                    <FriendsChecklist
                        onSelectionChange={handleFriendSelection}
                    />

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
                    <CalendarEvents selectedFriends={selectedFriends}/>
                </div>
            </div>
        </div>
    )
}

//TODO: create function that gets event data from database and translates it to coordinates.
//you can then pass the events list as an arg to CalendarEvents()
//notice you need to filter why which radial button is chosen
//def filter in another function, maybe in the same file as the one that gets the data from the database? but like what about caching?
//when do we check again for data... probably when an event has been added or deleted so Ill have to make sure it doesn't do it too often

//TODO: add function that translates the time to an attribute on the style component
//TODO: make sure that event is on line exactly because YAY! confirmed line is exactly on grid lines
//TODO: change to not military time lol

function CalendarEvents({selectedFriends}: {selectedFriends: number[]}) {
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
        {id: 1, weekday: 2, timeStartPixels: 30, timeLengthPixels: 90, title: "Gym Sesh", privacyTag: "Private", location: "Lederle"}, 
        {id: 2, weekday: 1, timeStartPixels: 1140, timeLengthPixels: 180, title: "Partyyy", privacyTag: "Shared", location: "At My House"}, 
        {id: 3, weekday: 4, timeStartPixels: 885, timeLengthPixels: 50, title: "Class", privacyTag: "Professional", location: "White House"}, 
    ]

    //fake friends events data
    const friendsEvents= [
        {id:1, friendId:3, weekday: 3, timeStartPixels: 920, timeLengthPixels: 120, title: "CS 311 Study Sesh", privacyTag: "Shared", location: "ILC"},
        {id:2,friendId:2, weekday: 6, timeStartPixels: 1280, timeLengthPixels: 180, title: "Movie Night", privacyTag: "Shared", location: "At My House"},
        {id:3,friendId:2, weekday: 6, timeStartPixels: 300, timeLengthPixels: 75, title: "Sunrise Watch", privacyTag: "Shared", location: "OHill"},
        {id:4, friendId:4, weekday: 7, timeStartPixels: 840, timeLengthPixels: 240, title: "Marathon", privacyTag: "Shared", location: "Boston"},
        {id:5, friendId:1, weekday: 3, timeStartPixels: 100, timeLengthPixels: 180, title: "Academic Lock In", privacyTag: "Private", location: "Du Bois Library"},
        {id:6, friendId:1, weekday: 1, timeStartPixels: 440, timeLengthPixels: 60, title: "Yoga Class", privacyTag: "Private", location: "Boyden Gym"},
        {id:7, friendId:6, weekday: 5, timeStartPixels: 1040, timeLengthPixels: 180, title: "Friendsgiving Dinner", privacyTag: "Shared", location: "Amherst"},
        {id:8, friendId:6, weekday: 2, timeStartPixels: 500, timeLengthPixels: 100, title: "Internship Interview", privacyTag: "Professional", location: "CS Building"},
        {id:9, friendId:5, weekday: 2, timeStartPixels: 760, timeLengthPixels: 90, title: "Farmer's Market Trip", privacyTag: "Shared", location: "Student Union"},
        {id:10, friendId:5, weekday: 6, timeStartPixels: 400, timeLengthPixels: 90, title: "Coffee Run", privacyTag: "Private", location: "ISB Café"},
        {id:11, friendId:3, weekday: 4, timeStartPixels: 430, timeLengthPixels: 120, title: "Picnic", privacyTag: "Shared", location: "Campus Pond"},
        {id:12, friendId:4, weekday: 1, timeStartPixels: 1200, timeLengthPixels: 120, title: "Pickleball", privacyTag: "Shared", location: "Rec Center"},
        {id:13, friendId:2, weekday: 7, timeStartPixels: 900, timeLengthPixels: 120, title: "Basketball Match", privacyTag: "Shared", location: "Rec Center"},
        {id:14, friendId:1, weekday: 7, timeStartPixels: 1160, timeLengthPixels: 300, title: "Concert", privacyTag: "Shared", location: "Mullins Center"},
        {id:15, friendId:5, weekday: 7, timeStartPixels: 320, timeLengthPixels: 120, title: "Breakfast w/h Friends", privacyTag: "Shared", location: "Amherst Coffee + Bar"}

    ]

    //array from 2-24
    const hours = Array.from({ length: 24 }, (_, i) => i+1);
    const hourLabels = ["1AM", "2AM", "3AM", "4AM", "5AM", "6AM", "7AM", "8AM", "9AM", "10AM", "11AM", "12PM", 
        "1PM", "2PM", "3PM", "4PM", "5PM", "6PM", "7PM", "8PM", "9PM", "10PM", "11PM", "12AM"];



    //layer that allows row line styling and hours written on calendar
    const labels = [];

    for (let i = 1; i <= 7; i++) {
        labels.push(
            hours.map((hour) => (
                    <div 
                        className='hour-row' 
                        id="first-row" 
                        key={1} 
                        style={{ 
                            gridColumnStart: i, 
                            gridRowStart: hour, 
                            borderRight: i === 7 ? 'none': '1px solid gray',
                            borderTop: hour === 1 ? 'none': '1px solid gray'
                    }}>
                        <div className='time-label'>
                            {hourLabels[hour-1]} 
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
                        top: `${event.timeStartPixels}px`,
                        height: `${event.timeLengthPixels}px`
                    }}
                    >
                        <h1> {event.title} </h1>
                        <p> {event.location} </p>
                    </div>    
                ))}
                {friendsEvents.filter((event)=>selectedFriends.includes(event.friendId)).map((event)=>{
                const friend = friends.find((f) => f.id === event.friendId);

                return (
                    <div
                    key={event.id}
                    className='calendar-event friend-event'
                    style={{
                        gridColumnStart: `${event.weekday}`,
                        gridColumnEnd: `${event.weekday + 1}`,
                        top: `${event.timeStartPixels}px`,
                        height: `${event.timeLengthPixels}px`,
                        backgroundColor: friend ? `${friend.color}A6`: "#EEEEEE", //A6 turns the background color into 65% opacity 
                        borderColor: friend ? `${friend.borderColor}A6`: "#CCCCCC"
                    }}
                >
                    <h1>{event.title}</h1>
                    <p>{event.location}</p>
        </div>
    );
})}
            </div>
        </div>
    )
}



export default DashboardPage;

//recall JSX needs an expression, not a statement. 