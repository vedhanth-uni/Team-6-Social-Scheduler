import './DashboardPage.css';
import {useState} from 'react';
import ViewDropdown from './components/ViewDropdown';
import PrivacyToggle from './components/PrivacyToggle';
import AddEventForm from './AddEventForm';
import FindFriend from './components/FindFriend';
import ImportButton from './components/ImportButton';

function DashboardPage() {
    const currentMonth = new Date().toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });

    const [currentView, setCurrentView] = useState('Weekly');
    const [selectedPrivacy, setSelectedPrivacy] = useState('Private');

    //tracks whether add event popup is open
    const [showEventForm, setShowEventForm] = useState(false);

    return (<div>
        <div className = "month-view-container">
            <div className = "month-container">
                <input
                    id ="current-month"
                    type="text"
                    value={currentMonth}
                    readOnly

                />
            </div>
            <ViewDropdown 
                currentView = {currentView} 
                setCurrentView = {setCurrentView}
            />
          </div>
        <PrivacyToggle 
            selectedPrivacy = {selectedPrivacy} 
            setSelectedPrivacy={setSelectedPrivacy}
        />
        <FindFriend/>
        <ImportButton/>

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
    </div>
    )
}

export default DashboardPage;