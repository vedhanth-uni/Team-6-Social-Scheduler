//your own events are not wired up to the backend yet, so both calendar views use this fake data
//TODO(misha): replace with events fetched from the API

//weekday is 1-7 (Sun-Sat) and doubles as the weekly grid column
//timeStartPixels / timeLengthPixels are minutes (1px = 1 min in the weekly view)
export interface OwnEvent {
    id: number;
    weekday: number;
    timeStartPixels: number;
    timeLengthPixels: number;
    title: string;
    privacyTag: string;
    location: string;
    date: string;
    allDay: boolean;
    startTime: string;
    endTime: string;
    description: string;
}

export const initialOwnEvents: OwnEvent[] = [
    {id: 1, weekday: 2, timeStartPixels: 30, timeLengthPixels: 90, title: "Gym Sesh", privacyTag: "Private", location: "Lederle", date: "2026-11-18", allDay: true, startTime:"", endTime:"", description:"Gym Sesh at Lederle!"},
    {id: 2, weekday: 1, timeStartPixels: 1140, timeLengthPixels: 180, title: "Partyyy", privacyTag: "Close", location: "At My House", date: "2026-11-18", allDay: true, startTime:"", endTime:"", description:"Party at my house!"},
    {id: 3, weekday: 4, timeStartPixels: 885, timeLengthPixels: 50, title: "Class", privacyTag: "Professional", location: "White House", date: "2026-11-18", allDay: true, startTime:"", endTime:"", description:"Class time :)"},
];
