import './FeedPage.css';
import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { apiFetch } from './api files/api';
import { getFeed, clashesWithBusy, joinEvent, leaveEvent } from './api files/feedApi';
import type { FeedEvent, FeedData } from './api files/feedApi';

const filters = ['For you', 'This week'] as const;
type Filter = (typeof filters)[number];

function greeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
}

function dayLabel(date: Date): string {
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);
    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function timeRange(start: Date, end: Date, allDay: boolean): string {
    if (allDay) return 'All day';
    const fmt = (d: Date) => d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    return `${fmt(start)} to ${fmt(end)}`;
}

function isThisWeek(date: Date): boolean {
    const weekEnd = new Date();
    weekEnd.setHours(0, 0, 0, 0);
    weekEnd.setDate(weekEnd.getDate() + (7 - weekEnd.getDay())); // next Sunday
    return date < weekEnd;
}

function FeedPage() {
    const [name, setName] = useState('');
    const [data, setData] = useState<FeedData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeFilter, setActiveFilter] = useState<Filter>('For you');
    const [joined, setJoined] = useState<Set<number>>(new Set());

    useEffect(() => {
        apiFetch('/me')
            .then((me) => setName(me.display_name))
            .catch(() => setError('Please log in to see your feed.'));
        getFeed()
            .then(setData)
            .catch((err) => setError(err instanceof Error ? err.message : 'Could not load your feed.'));
    }, []);

    function toggleJoin(event: FeedEvent) {
        const next = new Set(joined);
        if (next.has(event.eventId)) {
            next.delete(event.eventId);
            void leaveEvent(event.eventId).catch(() => {});
        } else {
            next.add(event.eventId);
            void joinEvent(event.eventId).catch(() => {});
        }
        setJoined(next);
    }

    let shown: FeedEvent[] = data?.events ?? [];
    if (data && activeFilter === 'For you') {
        shown = shown.filter((e) => !clashesWithBusy(e, data.busy)); // only events you're free for
    }
    if (activeFilter === 'This week') {
        shown = shown.filter((e) => isThisWeek(e.start));
    }

    return (
        <div className='feed-page'>
            <div className='feed-blob' />

            <aside className='feed-sidebar'>
                <div className='feed-logo'>
                    <img src='/logo.svg' className='feed-logo-human' alt='' />
                    <div className='feed-logo-green'>
                        <img src='/green_logo.svg' alt='' />
                        <p>social <br /> calendar</p>
                    </div>
                </div>

                <nav className='feed-nav'>
                    <button className='feed-nav-item active'>Feed</button>
                    <Link to='/Dash' className='feed-nav-item'>Friends</Link>
                    <Link to='/Dash' className='feed-nav-item'>My Calendar</Link>
                </nav>
            </aside>

            <main className='feed-main'>
                <header className='feed-header'>
                    <h1>{greeting()}{name && `, ${name}`}</h1>
                    <div className='feed-user'>
                        {name && <div className='feed-avatar small'>{name[0]}</div>}
                        {name}
                    </div>
                </header>

                <div className='feed-title-row'>
                    <h2>Happening around campus</h2>
                    <div className='feed-filters'>
                        {filters.map((filter) => (
                            <button
                                key={filter}
                                className={activeFilter === filter ? 'feed-filter active' : 'feed-filter'}
                                onClick={() => setActiveFilter(filter)}
                            >
                                {filter}
                            </button>
                        ))}
                    </div>
                </div>

                <div className='feed-list'>
                    {error && <p className='feed-message'>{error}</p>}
                    {!error && !data && <p className='feed-message'>Loading…</p>}
                    {data && !error && shown.length === 0 && (
                        <p className='feed-message'>Nothing here yet. Add some friends to see their events.</p>
                    )}

                    {shown.map((event) => (
                        <article className='feed-card' key={event.id}>
                            <div className='feed-card-top'>
                                <div className='feed-host'>
                                    <div className='feed-avatar' style={{ backgroundColor: event.hostColor }}>
                                        {event.hostName[0]}
                                    </div>
                                    <div>
                                        <strong>{event.hostName}</strong>
                                    </div>
                                </div>
                                <span className='feed-day'>{dayLabel(event.start)}</span>
                            </div>

                            <h3>{event.title}</h3>

                            <div className='feed-details'>
                                <div className='feed-detail'>
                                    <span>When</span>
                                    <strong>{timeRange(event.start, event.end, event.allDay)}</strong>
                                </div>
                                <div className='feed-detail'>
                                    <span>Where</span>
                                    <strong>{event.location ?? 'TBD'}</strong>
                                </div>
                            </div>

                            <div className='feed-card-bottom'>
                                <div className='feed-card-actions'>
                                    <button
                                        className={joined.has(event.eventId) ? 'feed-join active' : 'feed-join'}
                                        onClick={() => toggleJoin(event)}
                                    >
                                        {joined.has(event.eventId) ? 'Going' : 'Join'}
                                    </button>
                                </div>
                            </div>
                        </article>
                    ))}

                    {data && !error && shown.length > 0 && (
                        <p className='feed-message'>you're all caught up</p>
                    )}
                </div>
            </main>
        </div>
    );
}

export default FeedPage;
