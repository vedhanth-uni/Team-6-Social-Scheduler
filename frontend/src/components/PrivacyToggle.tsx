

function PrivacyToggle({selectedPrivacy, setSelectedPrivacy}){
    const privacyOptions=[
        "Private",
        "Close",
        "Professional"
    ];
    const selectFunc = (privacy: string) => {
        if (selectedPrivacy.includes(privacy)) {
            setSelectedPrivacy(
                selectedPrivacy.filter((selected) => selected !== privacy)
            );
        }
        else {
            setSelectedPrivacy([...selectedPrivacy, privacy]);
        }
    };
    return(
        <div className = "privacy-toggle-container">
            <div className = "privacy-toggle-box">
            {privacyOptions.map((privacy) => (
                    <label className="privacy-toggle-option" key={privacy}>
                        <input
                            type="checkbox"
                            checked={selectedPrivacy.includes(privacy)} //allows you to check multiple privacy options
                            onChange={() => selectFunc(privacy)}
                        />
                        <span>{privacy}</span>
                    </label>
                ))}
            </div>
        </div>
    )

}

export default PrivacyToggle; 