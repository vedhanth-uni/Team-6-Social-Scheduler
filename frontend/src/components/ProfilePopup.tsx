import {useState} from 'react';
import {UserRound} from 'lucide-react'; 
import './ProfilePopup.css';

function ProfilePopup(){
    const [showProfile, setShowProfile] = useState(false);
    const username = 'User123'; //temp username & followers values, change later
    const followers = 28;
    return(
        <div className = 'profile-container'>
            <button className ='profile-icon' 
                onClick={() => setShowProfile(!showProfile)}
            >
                <UserRound size={50}/>
            </button>
            {showProfile && (<div className = "profile-popup">
                <h3>{username}</h3>
                <p>{followers} Followers</p>
            </div>)}
        </div>
    )

}

export default ProfilePopup; 