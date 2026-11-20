import { useState } from 'react';
import { searchProfiles, sendFriendRequest } from '../api files/friendsApi';
import type { ProfileBrief, FriendLevel } from '../api files/friendsApi';

function FindFriend() {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<ProfileBrief[]>([]);
    const [level, setLevel] = useState<FriendLevel>('close');
    const [message, setMessage] = useState('');

    async function search(e: React.FormEvent) {
        e.preventDefault();
        setMessage('');
        try {
            setResults(await searchProfiles(query.trim()));
        } catch (err) {
            setMessage((err as Error).message);
        }
    }

    async function addFriend(username: string) {
        try {
            await sendFriendRequest(username, level);
            setMessage(`Request sent to @${username}`);
            setResults((prev) => prev.filter((p) => p.username !== username));
        } catch (err) {
            setMessage((err as Error).message); // e.g. already friends / request pending
        }
    }

    return (
        <div>
            <button type="button" className="view-button" onClick={() => setIsOpen(!isOpen)}>
                Find Friends
            </button>
            {isOpen && (
                <div>
                    <form onSubmit={search}>
                        <input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search by name or username"
                        />
                        <button type="submit">Search</button>
                    </form>

                    <label>
                        Relationship:{' '}
                        <select value={level} onChange={(e) => setLevel(e.target.value as FriendLevel)}>
                            <option value="close">Close</option>
                            <option value="professional">Professional</option>
                        </select>
                    </label>

                    {results.map((p) => (
                        <p key={p.id}>
                            {p.display_name} @{p.username}{' '}
                            <button type="button" onClick={() => addFriend(p.username)}>Add</button>
                        </p>
                    ))}
                    {message && <p>{message}</p>}
                </div>
            )}
        </div>
    );
}

export default FindFriend;