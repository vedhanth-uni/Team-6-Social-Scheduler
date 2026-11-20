import { useState } from 'react';
import type { Friend } from '../api files/friendsApi';
import LevelChip from './LevelChip';

type FriendRowProps = {
    friend: Friend;
    isBusy: boolean;
    onRemove: (friend: Friend) => void;
};

function FriendRow({ friend, isBusy, onRemove }: FriendRowProps) {
    // removing can't be undone (they'd have to accept a new request), so it takes a second click
    const [isConfirming, setIsConfirming] = useState(false);
    const { user } = friend;

    return (
        <li className={isConfirming ? 'friend-row' : 'friend-row friend-row--compact'}>
            <div className="friend-row__identity">
                <span className="friend-row__name">{user.display_name}</span>
                <span className="friend-row__meta">@{user.username}</span>
            </div>
            <LevelChip level={friend.level} />
            <div className="friend-row__actions">
                {isConfirming ? (
                    <>
                        <button
                            type="button"
                            className="panel-button panel-button--danger"
                            disabled={isBusy}
                            onClick={() => onRemove(friend)}
                        >
                            {isBusy ? 'Removing…' : `Remove @${user.username}`}
                        </button>
                        <button
                            type="button"
                            className="panel-button panel-button--secondary"
                            disabled={isBusy}
                            onClick={() => setIsConfirming(false)}
                        >
                            Cancel
                        </button>
                    </>
                ) : (
                    <button
                        type="button"
                        className="panel-button panel-button--text"
                        onClick={() => setIsConfirming(true)}
                        aria-label={`Remove ${user.display_name} from friends`}
                    >
                        Remove
                    </button>
                )}
            </div>
        </li>
    );
}

export default FriendRow;
