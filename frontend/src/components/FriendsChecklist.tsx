import { useState } from "react";
import '../FriendsChecklist.css';

function FriendsChecklist(){

    const friends = [ //temporary data, use actual data from backend later 
        "Daniela",
        "John",
        "Manasi",
        "Misha",
        "Naysa",
        "Vedhanth"

    ];
    const [selectedFriends, setSelectedFriends] = useState<string[]>([]); //stores the selected friends
    const selectFunc = (friend: string)=>{
        if(selectedFriends.includes(friend)){
            setSelectedFriends(selectedFriends.filter((selected) => selected !== friend)); //remove a friend if they're already selected
        }
        else{
            setSelectedFriends([...selectedFriends, friend]); //Add a friend if they haven't already been selected yet
        }
    }


    return(
        <div className = "friends-checklist-container">
        <div className = "friends-checklist-box">
            <h3>Friends</h3>
            <div className = "friends-list">
                {friends.map((friend)=>(
                    <label className = "friends-option" key = {friend}>
                        <input 
                            type = "checkbox"
                            checked = {selectedFriends.includes(friend)}
                            onChange ={()=> selectFunc(friend)}

                        />
                        {friend}
                    </label>
                ))}
            </div>
        </div>
        </div>
    )
}
export default FriendsChecklist;