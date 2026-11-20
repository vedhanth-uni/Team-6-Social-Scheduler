import { useState } from 'react';
import type { FriendRequest } from '../api files/friendsApi';
import FriendRequestRow from './FriendRequestRow';

// how many requests show before "See all"
const COLLAPSED_REQUEST_COUNT = 2;

type FriendRequestsSectionProps = {
    requests: FriendRequest[] | null;
    isRequestBusy: (request: FriendRequest) => boolean;
    onAccept: (request: FriendRequest) => void;
    onDecline: (request: FriendRequest) => void;
};

function FriendRequestsSection({ requests, isRequestBusy, onAccept, onDecline }: FriendRequestsSectionProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const count = requests?.length ?? 0;
    const canExpand = count > COLLAPSED_REQUEST_COUNT;
    const visible = requests && (isExpanded ? requests : requests.slice(0, COLLAPSED_REQUEST_COUNT));

    return (
        <section className="friends-panel__section" aria-labelledby="friend-requests-heading">
            <h3 id="friend-requests-heading" className="friends-panel__heading">
                Requests {requests && `(${count})`}
            </h3>

            {requests === null && <p className="friends-panel__hint">Loading requests…</p>}
            {requests?.length === 0 && <p className="friends-panel__hint">No pending requests.</p>}

            {visible && visible.length > 0 && (
                <ul
                    id="friend-requests-list"
                    className={`friends-panel__list${isExpanded ? ' friends-panel__list--expanded' : ''}`}
                >
                    {visible.map((request) => (
                        <FriendRequestRow
                            key={request.id}
                            request={request}
                            isBusy={isRequestBusy(request)}
                            onAccept={onAccept}
                            onDecline={onDecline}
                        />
                    ))}
                </ul>
            )}

            {canExpand && (
                <button
                    type="button"
                    className="panel-button panel-button--text friends-panel__toggle"
                    aria-expanded={isExpanded}
                    aria-controls="friend-requests-list"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    {isExpanded ? 'Show less ‹' : `See all ${count} ›`}
                </button>
            )}
        </section>
    );
}

export default FriendRequestsSection;
