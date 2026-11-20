import { useEffect, useRef, useState } from 'react';
import { Users, X } from 'lucide-react';
import './FriendsPanel.css';
import { useFriendsPanel } from '../hooks/useFriendsPanel';
import FriendRequestsSection from './FriendRequestsSection';
import FriendsListSection from './FriendsListSection';

// toolbar button + the left-side drawer it opens (pending requests on top, friends below)
function FriendsPanel() {
    const [isOpen, setIsOpen] = useState(false);
    const panel = useFriendsPanel(isOpen);
    const triggerRef = useRef<HTMLButtonElement>(null);
    const closeRef = useRef<HTMLButtonElement>(null);
    const pendingCount = panel.requests?.length ?? 0;

    function close() {
        setIsOpen(false);
        triggerRef.current?.focus();
    }

    // escape closes the drawer; focus starts on the close button so keyboard users land inside it
    useEffect(() => {
        if (!isOpen) return;
        closeRef.current?.focus();
        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === 'Escape') {
                setIsOpen(false);
                triggerRef.current?.focus();
            }
        }
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isOpen]);

    return (
        <>
            <button
                ref={triggerRef}
                type="button"
                className="view-button friends-panel-trigger"
                aria-expanded={isOpen}
                aria-controls="friends-panel"
                aria-label={pendingCount > 0 ? `Friends, ${pendingCount} pending requests` : 'Friends'}
                onClick={() => (isOpen ? close() : setIsOpen(true))}
            >
                <Users size={22} aria-hidden="true" />
                Friends
                {pendingCount > 0 && (
                    <span className="friends-panel-trigger__badge" aria-hidden="true">{pendingCount}</span>
                )}
            </button>

            {isOpen && (
                <>
                    <div className="friends-panel-backdrop" onClick={close} aria-hidden="true" />
                    <aside id="friends-panel" className="friends-panel" aria-label="Friends">
                        <header className="friends-panel__header">
                            <h2 className="friends-panel__title">Friends</h2>
                            <button
                                ref={closeRef}
                                type="button"
                                className="panel-button panel-button--icon"
                                onClick={close}
                                aria-label="Close friends panel"
                            >
                                <X size={20} aria-hidden="true" />
                            </button>
                        </header>

                        <p className="friends-panel__notice" role="status">{panel.notice}</p>

                        {panel.loadError && (
                            <div className="friends-panel__error" role="alert">
                                <p>Couldn't load your friends: {panel.loadError}</p>
                                <button
                                    type="button"
                                    className="panel-button panel-button--secondary"
                                    onClick={() => void panel.reload()}
                                >
                                    Try again
                                </button>
                            </div>
                        )}

                        {/* with nothing loaded yet, the error above replaces the "Loading…" lines */}
                        {!(panel.loadError && panel.requests === null) && (
                            <>
                                <FriendRequestsSection
                                    requests={panel.requests}
                                    isRequestBusy={panel.isRequestBusy}
                                    onAccept={(request) => void panel.accept(request)}
                                    onDecline={(request) => void panel.decline(request)}
                                />
                                <FriendsListSection
                                    friends={panel.friends}
                                    isFriendBusy={panel.isFriendBusy}
                                    onRemove={(friend) => void panel.remove(friend)}
                                />
                            </>
                        )}
                    </aside>
                </>
            )}
        </>
    );
}

export default FriendsPanel;
