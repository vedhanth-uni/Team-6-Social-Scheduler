import {useState} from 'react';

function ViewDropdown({currentView, setCurrentView}){
    const [isViewOpen, setIsViewOpen] = useState(false);
    return(
        <div className = "view-container">
            <div className = "view-dropdown">
                <button className = "view-button" onClick={()=> setIsViewOpen(!isViewOpen)}>
                    <span className = "dropdown-arrow">▾</span>
                    {currentView}
                    
                </button>
                {isViewOpen &&(
                    <div className = "view-options">
                        <button 
                            className = "view-option"
                            onClick={()=>{
                                setCurrentView('Weekly');
                                setIsViewOpen(false);
                            }}

                        > Weekly</button>
                        <button 
                            className = "view-option"
                            onClick={()=>{
                                setCurrentView('Monthly');
                                setIsViewOpen(false);
                            }}

                        > Monthly</button>
                    </div>
                )}
            </div>
        </div>
    )

}

export default ViewDropdown;