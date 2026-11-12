import { useState } from "react";
import '../FriendsChecklist.css';


type FriendsChecklistProps ={
    //the selected friends from the checklist
    onSelectionChange: (friendIds: number[])=>void;
}

export const friends = [ //temporary data, use actual data from backend later 
        {id: 1, name:"Daniela", color: "#F4A6A6", borderColor: "#D98282" },
        {id: 2, name: "John", color: "#B5D6A7", borderColor: "#7EAB6A"},
        {id:3, name: "Manasi", color: "#D2B5E8", borderColor: "#AB93BD"},
        {id: 4, name: "Misha", color: "#A6C8F4", borderColor: "#84A0C4"},
        {id: 5, name:"Naysa", color: "#E9B949", borderColor: "#C7962F"},
        {id: 6, name: "Vedhanth", color: "#A6D9D1", borderColor:"#86B0AA" }

    ];

function FriendsChecklist({onSelectionChange}:FriendsChecklistProps){
    const [selectedFriends, setSelectedFriends] = useState<number[]>([]); //stores the selected friends, based on Id, starts off as an empty array since no friends are selected in the beginning
    const selectFunc = (friendId: number)=>{
        let updatedFriends: number[]; //this holds the updates list of friend Ids
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