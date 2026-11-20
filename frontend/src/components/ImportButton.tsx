import { useRef, useState } from 'react';
import { importSchedule } from '../api files/importApi';

function ImportButton() {
    const fileInput = useRef<HTMLInputElement>(null);
    const [status, setStatus] = useState('');

    async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (!file) return;
        setStatus('Importing...');
        try {
            const r = await importSchedule(file);
            setStatus(
                `Imported ${r.created} event${r.created === 1 ? '' : 's'}` +
                (r.duplicates ? `, ${r.duplicates} duplicate${r.duplicates === 1 ? '' : 's'} skipped` : '') +
                (r.failed.length ? `, ${r.failed.length} failed` : '')
            );
        } catch (err) {
            setStatus((err as Error).message);
        } finally {
            e.target.value = ''; // allows picking the same file again
        }
    }

    return (
        <div>
            <button type="button" className="view-button" onClick={() => fileInput.current?.click()}>
                Import Schedule
            </button>
            <input ref={fileInput} type="file" accept=".ics" hidden onChange={handleFile} />
            {status && <span>{status}</span>}
        </div>
    );
}

export default ImportButton;