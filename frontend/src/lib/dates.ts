//date helpers for the calendar views; everything works in the browser's local timezone
//always build dates with new Date(y, m, d + n) instead of adding 86400000 ms,
//because adding ms lands on the wrong day across daylight saving changes

const DAYS_PER_WEEK = 7;

export function isSameDay(a: Date, b: Date): boolean {
    return a.getFullYear() === b.getFullYear()
        && a.getMonth() === b.getMonth()
        && a.getDate() === b.getDate();
}

export function addDays(date: Date, days: number): Date {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

//sunday at midnight of the week containing date
export function startOfWeek(date: Date): Date {
    return addDays(date, -date.getDay());
}

export function buildWeekDates(date: Date): Date[] {
    const weekStart = startOfWeek(date);
    return Array.from({ length: DAYS_PER_WEEK }, (_, i) => addDays(weekStart, i));
}

//every cell of a month grid: starts on the sunday on/before the 1st and fills whole weeks (4-6 rows)
export function buildMonthGrid(date: Date): Date[] {
    const year = date.getFullYear();
    const month = date.getMonth();
    const leadingDays = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cellCount = Math.ceil((leadingDays + daysInMonth) / DAYS_PER_WEEK) * DAYS_PER_WEEK;
    return Array.from({ length: cellCount }, (_, i) => new Date(year, month, 1 - leadingDays + i));
}

export function minutesSinceMidnight(date: Date): number {
    return date.getHours() * 60 + date.getMinutes();
}

//"YYYY-MM-DD" in local time, used as a key for grouping events by day
export function formatDateKey(date: Date): string {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${date.getFullYear()}-${month}-${day}`;
}

//minutes since midnight -> "9:05 AM"
export function formatMinutes(minutes: number): string {
    const hours24 = Math.floor(minutes / 60);
    const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
    const period = hours24 < 12 ? 'AM' : 'PM';
    return `${hours12}:${String(minutes % 60).padStart(2, '0')} ${period}`;
}
