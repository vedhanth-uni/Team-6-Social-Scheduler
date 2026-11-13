import './FeedPage.css';
import { useState } from 'react';
import { Link } from 'react-router';
import { House, Users, CalendarDays, Search, Bell, Plus } from 'lucide-react';
import { feedEvents } from './feedData';

const discoverFriends = [ //temp, replace with people you might know from the backend
    {id: 1, name: 'Misha', color: '#A6C8F4', publicEvents: 3},
    {id: 2, name: 'Dani', color: '#F4A6A6', publicEvents: 2},
    {id: 3, name: 'Sahasra', color: '#B5D6A7', publicEvents: 1},
];

const filters = ['For you', 'This week', 'Saved'];

function greeting() {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
}

function dayLabel(date: Date) {
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
    return date.toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric'});
}

function timeRange(start: Date, end: Date) {
    const format = (d: Date) => d.toLocaleTimeString('en-US', {hour: 'numeric', minute: '2-digit'});
    return `${format(start)} to ${format(end)}`;
}

function isThisWeek(date: Date) {
    const weekFromNow = new Date();
    weekFromNow.setDate(weekFromNow.getDate() + 7);
    return date < weekFromNow;
}

function FeedPage() {
    const username = 'John'; //temp, use the logged in user later
    const [activeFilter, setActiveFilter] = useState('For you');
    const [joined, setJoined] = useState<number[]>([]);
    const [saved, setSaved] = useState<number[]>([]);
    const [added, setAdded] = useState<number[]>([]);
    const toggle = (list: number[], setList: (ids: number[]) => void, id: number) => {
        setList(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
    };

    let shownEvents = feedEvents;
    if (activeFilter === 'Saved') shownEvents = feedEvents.filter((e) => saved.includes(e.id));
    if (activeFilter === 'This week') shownEvents = feedEvents.filter((e) => isThisWeek(e.start));

    return (
        <div className='feed-page'>
            <div className='feed-blob' />

            <aside className='feed-sidebar'>
                <div className='feed-logo'>
                    <img src='/logo.svg' className='feed-logo-human' />
                    <div className='feed-logo-green'>
                        <img src='/green_logo.svg' />
                        <p>social <br /> calendar</p>
                    </div>
                </div>

                <nav className='feed-nav'>
                    <button className='feed-nav-item active'>
                        <House size={22} /> Feed
                    </button>
                    <button className='feed-nav-item'>
                        <Users size={22} /> Friends
                    </button>
                    <Link to='/Dash' className='feed-nav-item'>
                        <CalendarDays size={22} /> My Calendar
                    </Link>
                </nav>

                <div className='feed-discover'>
                    <h3>People you might know</h3>
                    {discoverFriends.map((friend) => (
                        <div className='feed-discover-row' key={friend.id}>
                            <div className='feed-avatar large' style={{backgroundColor: friend.color}}>
                                {friend.name[0]}
                            </div>
                            <div className='feed-discover-info'>
                                <strong>{friend.name}</strong>
                                <span>{friend.publicEvents} {friend.publicEvents === 1 ? 'event' : 'events'} this week</span>
                            </div>
                            <button
                                className={added.includes(friend.id) ? 'feed-pill-button done' : 'feed-pill-button'}
                                onClick={() => toggle(added, setAdded, friend.id)}
                            >
                                {added.includes(friend.id) ? 'Sent' : 'Add'}
                            </button>
                        </div>
                    ))}
                </div>
            </aside>

            <main className='feed-main'>
                <header className='feed-header'>
                    <h1>{greeting()}, {username}</h1>
                    <div className='feed-header-actions'>
                        <button className='feed-icon-button' aria-label='Search'>
                            <Search size={24} />
                        </button>
                        <button className='feed-icon-button' aria-label='Notifications'>
                            <Bell size={24} />
                        </button>
                        <div className='feed-user'>
                            <div className='feed-avatar small'>{username[0]}</div>
                            {username}
                        </div>
                    </div>
                </header>

                <section className='feed-create'>
                    <div>
                        <h2>Hosting something?</h2>
                        <p>Post it here and anyone can join.</p>
                    </div>
                    <button className='feed-create-button'>
                        <Plus size={22} /> Post event
                    </button>
                </section>

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
                    {activeFilter === 'Saved' && shownEvents.length === 0 && (
                        <p className='feed-message'>nothing saved yet</p>
                    )}

                    {shownEvents.map((event) => {
                        const isJoined = joined.includes(event.id);
                        const goingCount = event.goingCount + (isJoined ? 1 : 0);
                        const extra = goingCount - event.going.length;

                        return (
                            <article className='feed-card' key={event.id}>
                                <div className='feed-card-top'>
                                    <div className='feed-host'>
                                        <div className='feed-avatar' style={{backgroundColor: event.hostColor}}>
                                            {event.host[0]}
                                        </div>
                                        <div>
                                            <strong>{event.host}</strong>
                                            <span>{goingCount} going</span>
                                        </div>
                                    </div>
                                    <span className='feed-day'>{dayLabel(event.start)}</span>
                                </div>

                                <h3>{event.title}</h3>
                                {event.description && <p className='feed-description'>{event.description}</p>}

                                <div className='feed-details'>
                                    <div className='feed-detail'>
                                        <span>When</span>
                                        <strong>{timeRange(event.start, event.end)}</strong>
                                    </div>
                                    <div className='feed-detail'>
                                        <span>Where</span>
                                        <strong>{event.location}</strong>
                                    </div>
                                </div>

                                <div className='feed-card-bottom'>
                                    <div className='feed-going'>
                                        {event.going.map((person, i) => (
                                            <div className={i === 0 ? 'feed-avatar tiny first' : 'feed-avatar tiny'} key={person}>
                                                {person}
                                            </div>
                                        ))}
                                        {extra > 0 && <div className='feed-avatar tiny'>+{extra}</div>}
                                    </div>

                                    <div className='feed-card-actions'>
                                        <button
                                            className={saved.includes(event.id) ? 'feed-save active' : 'feed-save'}
                                            onClick={() => toggle(saved, setSaved, event.id)}
                                        >
                                            {saved.includes(event.id) ? 'Saved' : 'Save'}
                                        </button>
                                        <button
                                            className={isJoined ? 'feed-join active' : 'feed-join'}
                                            onClick={() => toggle(joined, setJoined, event.id)}
                                        >
                                            {isJoined ? 'Going' : 'Join'}
                                        </button>
                                    </div>
                                </div>
                            </article>
                        );
                    })}

                    {shownEvents.length > 0 && <p className='feed-message'>you're all caught up</p>}
                </div>
            </main>
        </div>
    );
}

export default FeedPage;
