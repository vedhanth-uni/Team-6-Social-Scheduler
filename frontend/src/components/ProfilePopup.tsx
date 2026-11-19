import {useState, useEffect} from 'react';
import {UserRound} from 'lucide-react'; 
import './ProfilePopup.css';
import { getMyProfile } from '../api files/profileApi';
import type { UserProfile } from '../api files/profileApi';

function ProfilePopup(){
    const [showProfile, setShowProfile] = useState(false);
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!showProfile) return;

        async function fetchProfile() {
            try {
                setLoading(true);
                setError('');
                const data = await getMyProfile();
                setProfile(data);
            } catch (error) {
                console.error('Error fetching profile:', error);
                setError('Could not load profile information.');
            } finally {
                setLoading(false);
            }
        }

        fetchProfile();
    }, [showProfile]);

    return(
        <div className="profile-container">
            <button
                className="profile-icon"
                onClick={() => setShowProfile(!showProfile)}
            >
                <UserRound size={50} />
            </button>

            {showProfile && (
                <div className="profile-popup">
                    {loading && <p>Loading profile...</p>}
                    {error && <p>{error}</p>}
                    {profile && !loading && (
                        <>
                            <h3>{profile.display_name}</h3>
                            <p>@{profile.username}</p>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

export default ProfilePopup; 