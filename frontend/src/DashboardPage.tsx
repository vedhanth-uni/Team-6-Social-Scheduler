import './DashboardPage.css';
import {useState} from 'react';
import ViewDropdown from './components/ViewDropdown';
import PrivacyToggle from './components/PrivacyToggle';



function DashboardPage() {
    const currentMonth = new Date().toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });

    const [currentView, setCurrentView] = useState('Weekly');
    const [selectedPrivacy, setSelectedPrivacy] = useState('Private');

    return (<div>
        <p className='default-text'>
            Dashboard goes here.
        </p>
        <div className = "month-container">
            <input
                id ="current-month"
                type="text"
                value={currentMonth}
                readOnly

            />
        </div>
        <ViewDropdown currentView = {currentView} setCurrentView = {setCurrentView}/>
        <PrivacyToggle selectedPrivacy = {selectedPrivacy} setSelectedPrivacy={setSelectedPrivacy}/>
        </div>
    )
}

export default DashboardPage;