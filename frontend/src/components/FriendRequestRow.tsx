import type { FriendRequest } from '../api files/friendsApi';
import LevelChip from './LevelChip';

type FriendRequestRowProps = {
    request: FriendRequest;
    isBusy: boolean;
    onAccept: (request: FriendRequest) => void;
    onDecline: (request: FriendRequest) => void;
};

const SENT_DATE_FORMAT: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };

function FriendRequestRow({ request, isBusy, onAccept, onDecline }: FriendRequestRowProps) {
    const { sender } = request;
    const sentOn = new Date(request.created_at).toLocaleDateString('en-US', SENT_DATE_FORMAT);

    return (
        <li className="friend-row">
            <div className="friend-row__identity">
                <span className="friend-row__name">{sender.display_name}</span>
                <span className="friend-row__meta">@{sender.username} · {sentOn}</span>
            </div>
            <LevelChip level={request.level} />
            <div className="friend-row__actions">
                <button
                    type="button"
                    className="panel-button panel-button--primary"
                    disabled={isBusy}
                    onClick={() => onAccept(request)}
                    aria-label={`Accept friend request from ${sender.display_name}`}
                >
                    Accept
                </button>
                <button
                    type="button"
                    className="panel-button panel-button--secondary"
                    disabled={isBusy}
                    onClick={() => onDecline(request)}
                    aria-label={`Decline friend request from ${sender.display_name}`}
                >
                    Decline
                </button>
            </div>
        </li>
    );
}

export default FriendRequestRow;
