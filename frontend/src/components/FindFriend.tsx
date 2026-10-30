import { useState } from 'react';
import { apiFetch } from '../api';

interface Profile {
    id: string;
    username: string;
    display_name: string;
}

function FindFriend() {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<Profile[]>([]);

    async function search(e: React.FormEvent) {
        e.preventDefault();
        setResults(await apiFetch(`/profiles/search?q=${encodeURIComponent(query)}`));
    }

    return (
        <div>
            <button type="button" className="view-button" onClick={() => setIsOpen(!isOpen)}>Find Friends</button>
            {isOpen && (
                <form onSubmit={search}>
                    <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search" />
                    <button type="submit">Search</button>
                    {results.map((p) => (
                        <p key={p.id}>{p.display_name} @{p.username}</p>
                    ))}
                </form>
            )}
        </div>
    );
}

export default FindFriend;
