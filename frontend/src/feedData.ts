//fake feed for now, replace with GET /feed once the backend has it

export type FeedEvent = {
    id: number;
    host: string;
    hostColor: string;
    title: string;
    description: string;
    location: string;
    start: Date;
    end: Date;
    going: string[];
    goingCount: number;
};

const hosts = [
    {name: 'Vedhanth', color: '#A6D9D1'},
    {name: 'Manasi', color: '#D2B5E8'},
    {name: 'Daniela', color: '#F4A6A6'},
    {name: 'Misha', color: '#A6C8F4'},
    {name: 'Sahasra', color: '#B5D6A7'},
    {name: 'Naysa', color: '#E9B949'},
    {name: 'Priya Shah', color: '#F4A6A6'},
    {name: 'Jordan Lee', color: '#A6C8F4'},
    {name: 'Alex Kim', color: '#D2B5E8'},
    {name: 'Maya Torres', color: '#A6D9D1'},
];

const templates = [
    {title: 'Rooftop concert & sunset drinks', description: 'Yurrrr come and get drunkkkkkk', location: 'Du Bois Library', hour: 18.5, minutes: 150},
    {title: 'Late night frank run', description: 'im starving pls someone come w me', location: 'Franklin Dining Commons', hour: 22, minutes: 60},
    {title: "puffers sunset", description: '', location: "Puffer's Pond", hour: 17, minutes: 120},
    {title: '320 lock in', description: 'sprint due friday we are cooked. bring snacks', location: 'ILC S331', hour: 19, minutes: 120},
    {title: 'Thrifting in Noho', description: 'taking the bus from haigis, 2 spots in my friends car tho', location: 'Northampton', hour: 12, minutes: 180},
    {title: 'Open mic night!!', description: 'my roommate is performing pls come so she doesnt bomb', location: 'Blue Wall', hour: 20, minutes: 150},
    {title: 'Outdoor movie night in the park', description: 'Come hangout fire event yadi yadi yada', location: 'Campus Pond', hour: 20.5, minutes: 150},
    {title: 'morning run', description: 'slow pace i promise', location: 'Boyden Gym', hour: 7.5, minutes: 45},
    {title: 'Catan night', description: 'loser buys pizza', location: 'Grayson Hall lounge', hour: 19, minutes: 180},
    {title: 'Pickup bball', description: 'need 3 more for 5s', location: 'Rec Center', hour: 18, minutes: 120},
    {title: 'Farmers market', description: 'apple cider donuts thats it thats the event', location: 'Amherst Town Common', hour: 10, minutes: 90},
    {title: 'UMass vs BC hockey', description: 'WEAR BLACK!!! student section goes crazy', location: 'Mullins Center', hour: 19, minutes: 150},
    {title: 'Photo walk', description: 'need new pics for my insta lol', location: 'Orchard Hill Bowl', hour: 15, minutes: 90},
    {title: 'Pho night', description: 'making a huge pot, u bring the toppings', location: 'Baker Hall kitchen', hour: 18.5, minutes: 120},
    {title: 'sand volleyball', description: 'we have a ball and like 3 ppl', location: 'Southwest courts', hour: 16.5, minutes: 90},
    {title: 'Study sesh @ amherst coffee', description: 'silent study, no yapping', location: 'Amherst Coffee', hour: 14, minutes: 120},
];

const initials = ['AL', 'MK', 'JP', 'DR', 'SA', 'VR', 'JN', 'NP', 'TC', 'EW'];

function makeEvent(n: number): FeedEvent {
    const host = hosts[(n * 7) % hosts.length];
    const template = templates[(n * 5) % templates.length];

    //3 events a day, each at a normal time for that kind of thing
    const start = new Date();
    start.setDate(start.getDate() + Math.floor(n / 3));
    start.setHours(Math.floor(template.hour), (template.hour % 1) * 60, 0, 0);
    if (start.getTime() < Date.now() + 60 * 60 * 1000) start.setDate(start.getDate() + 1);

    const end = new Date(start);
    end.setMinutes(end.getMinutes() + template.minutes);

    const goingCount = (n * 37) % 23 + 2;
    const going = [0, 1, 2]
        .map((i) => initials[(n + i * 3) % initials.length])
        .slice(0, Math.min(3, goingCount));

    return {id: n + 1, host: host.name, hostColor: host.color, ...template, start, end, going, goingCount};
}

export const feedEvents = Array.from({length: 12}, (_, n) => makeEvent(n))
    .sort((a, b) => a.start.getTime() - b.start.getTime());
