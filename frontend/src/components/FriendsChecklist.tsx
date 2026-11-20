import { useState } from "react";
import '../FriendsChecklist.css';
import type { CalendarFriend } from "../api files/friendsApi";

type FriendsChecklistProps = {
    friends: CalendarFriend[];
    onSelectionChange: (friendIds: string[]) => void; // sent up to the dashboard
}

function FriendsChecklist({ friends, onSelectionChange }: FriendsChecklistProps) {
    const [selectedFriends, setSelectedFriends] = useState<string[]>([]);

    const selectFunc = (friendId: string) => {
        const updatedFriends = selectedFriends.includes(friendId)
            ? selectedFriends.filter((id) => id !== friendId)
            : [...selectedFriends, friendId];
        setSelectedFriends(updatedFriends);
        onSelectionChange(updatedFriends);
    }

    return (
        <div className="friends-checklist-container">
            <div className="friends-checklist-box">
                <h3>Friends</h3>
                <div className="friends-list">
                    {friends.length === 0 && <p style={{ margin: 0, opacity: 0.7 }}>No friends yet</p>}
                    {friends.map((friend) => (
                        <label className="friends-option" key={friend.id}>
                            <input
                                type="checkbox"
                                checked={selectedFriends.includes(friend.id)}
                                onChange={() => selectFunc(friend.id)}
                            />
                            <span
                                className="friend-color"
                                style={{ backgroundColor: friend.color }}></span>
                            {friend.name}
                        </label>
                    ))}
                </div>
            </div>
        </div>
    )
}
export default FriendsChecklist;