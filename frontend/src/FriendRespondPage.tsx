// the page the Accept / Decline buttons in a friend request email open:
//   /friends/respond?token=...&action=accept|decline
//
// not logged in -> send them to the login page. ?next= is added so the login page can bring them back
//                  here once that's wired up (auth branch) -- for now they just click the email link again
// logged in     -> do the accept/decline right away (that's what the email button said) and show the result
//
// the token only works for the account the email was sent to, the backend checks that.

import './FriendRespondPage.css';
import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router';
import { supabase } from './supabaseClient';
import { apiFetch } from './api';

// just the fields this page uses from the backend's FriendRequestRead
interface FriendRequest {
    level: 'close' | 'professional';
    status: 'pending' | 'accepted' | 'declined' | 'cancelled' | 'expired';
    sender: { display_name: string };
}

type State =
    | { kind: 'working' }
    | { kind: 'done'; request: FriendRequest }
    | { kind: 'error'; message: string };

function FriendRespondPage() {
    const [params] = useSearchParams();
    const location = useLocation();
    const navigate = useNavigate();
    const token = params.get('token');
    const action = params.get('action');

    const linkOk = !!token && (action === 'accept' || action === 'decline');

    const [state, setState] = useState<State>(
        linkOk
            ? { kind: 'working' }
            : { kind: 'error', message: 'This link is incomplete. Try opening it from the email again.' }
    );
    const started = useRef(false); // StrictMode runs effects twice in dev, only respond once

    useEffect(() => {
        if (!linkOk || started.current) return;
        started.current = true;

        (async () => {
            const { data } = await supabase.auth.getSession();
            if (!data.session) {
                const next = location.pathname + location.search;
                navigate(`/?next=${encodeURIComponent(next)}`, { replace: true });
                return;
            }
            try {
                const request: FriendRequest = await apiFetch('/friend-requests/respond', {
                    method: 'POST',
                    body: JSON.stringify({ token, action }),
                });
                setState({ kind: 'done', request });
            } catch (err) {
                setState({ kind: 'error', message: err instanceof Error ? err.message : 'Something went wrong' });
            }
        })();
    }, [linkOk, token, action, location, navigate]);

    return (
        <main className='friend-respond-page'>
            <section className='friend-respond-card'>
                {state.kind === 'working' && <p>One sec…</p>}

                {state.kind === 'done' && state.request.status === 'accepted' && (
                    <>
                        <h2>You're connected!</h2>
                        <p>
                            You and <strong>{state.request.sender.display_name}</strong> are now{' '}
                            {state.request.level === 'close' ? 'close friends' : 'professional contacts'}.
                        </p>
                    </>
                )}

                {state.kind === 'done' && state.request.status === 'declined' && (
                    <>
                        <h2>Request declined</h2>
                        <p>
                            You declined <strong>{state.request.sender.display_name}</strong>'s friend request.
                            They won't be notified.
                        </p>
                    </>
                )}

                {state.kind === 'error' && (
                    <>
                        <h2>Couldn't do that</h2>
                        <p>{state.message}</p>
                    </>
                )}

                {state.kind !== 'working' && (
                    <Link className='friend-respond-link' to='/Dash'>Go to my calendar</Link>
                )}
            </section>
        </main>
    );
}

export default FriendRespondPage;
