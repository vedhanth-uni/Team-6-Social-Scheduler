import { useState } from 'react';
import type { Friend } from '../api files/friendsApi';
import FriendRow from './FriendRow';

type FriendsListSectionProps = {
    friends: Friend[] | null;
    isFriendBusy: (friend: Friend) => boolean;
    onRemove: (friend: Friend) => void;
};

function matchesSearch(friend: Friend, query: string): boolean {
    const { display_name, username } = friend.user;
    return display_name.toLowerCase().includes(query) || username.toLowerCase().includes(query);
}

function FriendsListSection({ friends, isFriendBusy, onRemove }: FriendsListSectionProps) {
    const [search, setSearch] = useState('');
    const query = search.trim().toLowerCase().replace(/^@/, '');
    const visible = friends && (query ? friends.filter((friend) => matchesSearch(friend, query)) : friends);

    return (
        <section className="friends-panel__section friends-panel__section--grow" aria-labelledby="friends-heading">
            <h3 id="friends-heading" className="friends-panel__heading">
                Friends {friends && `(${friends.length})`}
            </h3>

            {friends !== null && friends.length > 0 && (
                <>
                    <label htmlFor="friends-search" className="visually-hidden">Search friends</label>
                    <input
                        id="friends-search"
                        type="search"
                        className="friends-panel__search"
                        placeholder="Search friends"
                        autoComplete="off"
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                    />
                </>
            )}

            {friends === null && <p className="friends-panel__hint">Loading friends…</p>}
            {friends?.length === 0 && (
                <p className="friends-panel__hint">No friends yet. Use Find Friends to send a request.</p>
            )}
            {friends && friends.length > 0 && visible?.length === 0 && (
                <p className="friends-panel__hint">No friends match "{search.trim()}".</p>
            )}

            {visible && visible.length > 0 && (
                <ul className="friends-panel__list friends-panel__list--fill">
                    {visible.map((friend) => (
                        <FriendRow
                            key={friend.user.id}
                            friend={friend}
                            isBusy={isFriendBusy(friend)}
                            onRemove={onRemove}
                        />
                    ))}
                </ul>
            )}
        </section>
    );
}

export default FriendsListSection;
