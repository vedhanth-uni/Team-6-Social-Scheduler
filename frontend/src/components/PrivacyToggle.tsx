

function PrivacyToggle({selectedPrivacy, setSelectedPrivacy}){
    return(
        <div className = "privacy-toggle-container">
            <div className = "privacy-toggle-box">
            <label className = "privacy-toggle-option">
             
                <input
                    type ="radio"
                    name="privacy-toggle"
                    value="Private"
                    checked={selectedPrivacy ==="Private"}
                    onChange={()=>setSelectedPrivacy('Private')}
                />
                <span>Private</span>
            </label>

            <label className = "privacy-toggle-option">
                
                <input
                    type ="radio"
                    name="privacy-toggle"
                    value="Close"
                    checked={selectedPrivacy ==="Close"}
                    onChange={()=>setSelectedPrivacy('Close')}
                />
                <span>Close</span>
            </label>

            <label className = "privacy-toggle-option">
                
                <input
                    type ="radio"
                    name="privacy-toggle"
                    value="Professional"
                    checked={selectedPrivacy ==="Professional"}
                    onChange={()=>setSelectedPrivacy('Professional')}
                />
                <span>Professional</span>
            </label>
            </div>
        </div>
    )

}

export default PrivacyToggle; 