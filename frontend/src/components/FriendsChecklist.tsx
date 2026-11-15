import { useState } from "react";
import '../FriendsChecklist.css';
import type { Friend } from "../friendsApi";


type FriendsChecklistProps ={
    friends: Friend[];
    //the selected friends from the checklist
    onSelectionChange: (friendIds: string[])=>void;
}

function FriendsChecklist({friends, onSelectionChange}:FriendsChecklistProps){
    const [selectedFriends, setSelectedFriends] = useState<string[]>([]); //stores the selected friends, based on Id, starts off as an empty array since no friends are selected in the beginning
    const selectFunc = (friendId: string)=>{
        let updatedFriends: string[]; //this holds the updates list of friend Ids
        if(selectedFriends.includes(friendId)){ //first check if that friends have been selected alr
            updatedFriends = selectedFriends.filter((id) => id !== friendId); //remove a friend if they're already selected
        }
        else{ //if not selected alr, add them to the list along with the rest of the selected friends 
            updatedFriends = [...selectedFriends, friendId]; //Add a friend if they haven't already been selected yet
        }
        setSelectedFriends(updatedFriends);
        onSelectionChange(updatedFriends); //this will send to the dashboard page
    }


    return(
        <div className = "friends-checklist-container">
        <div className = "friends-checklist-box">
            <h3>Friends</h3>
            <div className = "friends-list">
                {friends.length === 0 && <p style = {{margin: 0, opacity: 0.7}}>No friends yet</p>}
                {friends.map((friend)=>(
                    <label className = "friends-option" key = {friend.id}>
                        <input 
                            type = "checkbox"
                            checked = {selectedFriends.includes(friend.id)}
                            onChange ={()=> selectFunc(friend.id)}

                        />
                        <span 
                            className = "friend-color"
                            style = {{backgroundColor: friend.color}}></span>
                        {friend.name}
                    </label>
                ))}
            </div>
        </div>
        </div>
    )
}
export default FriendsChecklist;