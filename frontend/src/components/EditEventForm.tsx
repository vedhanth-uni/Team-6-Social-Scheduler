import { useState } from 'react';
import '../AddEventForm.css';
import type { CalendarEvent } from '../AddEventForm';

interface EditableCalendarEvent{
    id:number;
    title:string;
    location:string;
    privacyTag:string; //this is visibility 
    date: string;
    allDay: boolean;
    startTime: string;
    endTime: string;
    description: string;
}

interface EditEventFormProps{
    event: EditableCalendarEvent;
    onCancel:()=>void;
    onDelete: (eventId:number)=>void;
    onUpdate:(updatedEvent: CalendarEvent)=>void;
}

function EditEventForm({event, onCancel, onDelete, onUpdate}:EditEventFormProps){
    function handleUpdate(){
        if(!allDay && startTime >=endTime){
            alert('The end time cant be less than the start time');
            return;
        }
        onUpdate({title, date, allDay, startTime: allDay? '' :startTime, endTime: allDay ? '' :endTime, location, description, visibility: privacyTag as CalendarEvent['visibility']})
    }
    const [title, setTitle] = useState(event.title);
    const [date, setDate] = useState(event.date);
    const [location, setLocation] = useState(event.location);
    const [privacyTag, setPrivacyTag] = useState(event.privacyTag);
    const [allDay, setAllDay] = useState(event.allDay);
    const [startTime, setStartTime] = useState(event.startTime);
    const [endTime, setEndTime] = useState(event.endTime);
    const [description, setDescription] = useState(event.description);

    return (
        <div className = "event-modal-backdrop"
        onMouseDown={(mouseEvent)=>{
            if(mouseEvent.target === mouseEvent.currentTarget){
                onCancel();
            }
        }}>
            <section 
                className = "event-modal"
                role = "dialog"
                aria-modal="true"
                aria-labelledby="event-form-title"

            >
                <h2 id = "event-form-title">Edit Event</h2>
                <div className = "form-group">
                    <label>Event Name</label>
                    <input
                        id= "event-title"
                        type = "text"
                        value = {title}
                        onChange={(e) => setTitle(e.target.value)}
                    />
                </div>
                <div className = "form-group">
                    <label>Date</label>
                    <input
                        id= "event-date"
                        type = "date"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
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
                {!allDay && (
                    <>
                        <div className="form-group">
                            <label htmlFor="event-start-time">Start Time</label>
                            <input
                                id="event-start-time"
                                type="time"
                                value={startTime}
                                onChange={(event) => setStartTime(event.target.value)}
                            />
                        </div>
                <div className = "form-group">
                    <label>End Time</label>
                    <input
                        id= "event-end-time"
                        type = "time"
                        value = {endTime}
                        onChange = {(event)=> setEndTime(event.target.value)}
                    />
                </div>
                </>)}
                <div className ="form-group">
                    <label>Location</label>
                    <input
                        id= "event-location"
                        type = "text"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                    />
                </div>
                <div className ="form-group">
                    <label>Description</label>
                    <textarea
                        id= "event-description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}

                    />
                </div>
                <div className ="form-group">
                    <label>Visibility</label>
                    <select
                        id="event-visibility"
                        value={privacyTag}
                        onChange={(e) => setPrivacyTag(e.target.value)}
                    >
                        <option value="Private">Private</option>
                        <option value="Close">Close</option>
                        <option value="Professional">Professional</option>
                    </select>
                
                </div>
                <div className = "event-form-buttons">

                    <button type = "button" onClick={onCancel}> Close</button> 
                    <button type = "button" onClick={handleUpdate}>Update Event</button>
                    <button type = "button" className = "delete-event-button" onClick={()=> onDelete(event.id)}>Delete Event</button>
                    
                </div>
            </section>

        </div>
    )
}

export default EditEventForm;