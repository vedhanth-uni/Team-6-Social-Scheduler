import { useCallback, useEffect, useRef, useState } from 'react';
import {
    acceptFriendRequest,
    declineFriendRequest,
    deleteFriend,
    fetchFriends,
    fetchIncomingRequests,
} from '../api files/friendsApi';
import type { Friend, FriendRequest } from '../api files/friendsApi';

function errorMessage(error: unknown): string {
    return error instanceof Error ? error.message : 'Something went wrong. Try again.';
}

/**
 * Incoming requests + friends for the friends panel.
 *
 * Loads once on mount (so the toolbar badge has a count) and again every time the panel opens.
 * After every action, success or failure, both lists are refetched so the panel always matches
 * the database -- e.g. if a request was already answered from the email link, it just disappears.
 */
export function useFriendsPanel(isOpen: boolean) {
    // null = not loaded yet
    const [requests, setRequests] = useState<FriendRequest[] | null>(null);
    const [friends, setFriends] = useState<Friend[] | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    // result of the last accept/decline/remove, shown at the top of the panel
    const [notice, setNotice] = useState<string | null>(null);
    // keys like "request:12" or "friend:<uuid>" for rows with a call in flight
    const [busyKeys, setBusyKeys] = useState<ReadonlySet<string>>(new Set());
    const hasLoaded = useRef(false);

    const reload = useCallback(async () => {
        try {
            const [nextRequests, nextFriends] = await Promise.all([fetchIncomingRequests(), fetchFriends()]);
            setRequests(nextRequests);
            setFriends(nextFriends);
            setLoadError(null);
        } catch (error) {
            setLoadError(errorMessage(error));
        } finally {
            hasLoaded.current = true;
        }
    }, []);

    useEffect(() => {
        if (isOpen || !hasLoaded.current) {
            void reload();
        }
    }, [isOpen, reload]);

    async function runAction(key: string, action: () => Promise<unknown>, successNotice: string) {
        setBusyKeys((keys) => new Set(keys).add(key));
        setNotice(null);
        try {
            await action();
            setNotice(successNotice);
        } catch (error) {
            setNotice(errorMessage(error));
        } finally {
            await reload();
            setBusyKeys((keys) => {
                const next = new Set(keys);
                next.delete(key);
                return next;
            });
        }
    }

    function accept(request: FriendRequest) {
        return runAction(`request:${request.id}`, () => acceptFriendRequest(request.id),
            `You and ${request.sender.display_name} are now friends.`);
    }

    function decline(request: FriendRequest) {
        return runAction(`request:${request.id}`, () => declineFriendRequest(request.id),
            `Declined ${request.sender.display_name}'s request.`);
    }

    function remove(friend: Friend) {
        return runAction(`friend:${friend.user.id}`, () => deleteFriend(friend.user.id),
            `Removed ${friend.user.display_name} from your friends.`);
    }

    return {
        requests,
        friends,
        loadError,
        notice,
        reload,
        accept,
        decline,
        remove,
        isRequestBusy: (request: FriendRequest) => busyKeys.has(`request:${request.id}`),
        isFriendBusy: (friend: Friend) => busyKeys.has(`friend:${friend.user.id}`),
    };
}
