import { useRef } from 'react';

function ImportButton() {
    const fileInput = useRef<HTMLInputElement>(null);

    return (
        <div>
            <button type="button" className="view-button" onClick={() => fileInput.current?.click()}>
                Import Schedule
            </button>
            <input ref={fileInput} type="file" accept=".ics" hidden />
        </div>
    );
}

export default ImportButton;
