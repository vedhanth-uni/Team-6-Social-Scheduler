import {useEffect, useState} from 'react';
import {UserRound} from 'lucide-react'; 
import './ProfilePopup.css';
import { apiFetch } from '../api';
import { supabase } from '../supabaseClient';

function ProfilePopup(){
    const [showProfile, setShowProfile] = useState(false);
    const [username, setUsername] = useState('');
    const followers = 28; //temp followers value, change later

    //ask the backend who we are (it also creates our user row on first login)
    useEffect(() => {
        apiFetch('/me')
            .then((me) => setUsername(me.display_name))
            .catch(() => setUsername('Unknown user'));
    }, []);

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
                {/* signing out clears the session, which sends us back to the login page */}
                <button type="button" className="view-button" onClick={() => supabase.auth.signOut()}>
                    Sign out
                </button>
            </div>)}
        </div>
    )

}

export default ProfilePopup; 