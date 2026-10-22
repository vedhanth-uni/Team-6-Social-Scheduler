import './DashboardPage.css';
import { useState } from 'react';
import AddEventForm from './AddEventForm';

function DashboardPage() {
    //tracks whether add event popup is open
    const [showEventForm, setShowEventForm] = useState(false);

    return (
        // <p className='default-text'>
        //     Dashboard goes here.
        // </p>
        <main>
            <h1>Social Calendar</h1>
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
        </main>
    )
}

export default DashboardPage;