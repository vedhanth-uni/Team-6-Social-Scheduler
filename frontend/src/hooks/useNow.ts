import { useEffect, useState } from 'react';

const MS_PER_MINUTE = 60_000;

//the client's current time from their system clock (not the server's), refreshed on every minute boundary
export function useNow(): Date {
    const [now, setNow] = useState(() => new Date());

    useEffect(() => {
        let timeoutId: number;

        //setTimeout to the next minute boundary instead of setInterval, so the time bar moves when the clock does
        const scheduleNextTick = () => {
            const msUntilNextMinute = MS_PER_MINUTE - (Date.now() % MS_PER_MINUTE);
            timeoutId = window.setTimeout(() => {
                setNow(new Date());
                scheduleNextTick();
            }, msUntilNextMinute);
        };

        //browsers slow down timers in background tabs, so catch up as soon as the tab is visible again
        const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible') {
                setNow(new Date());
            }
        };

        scheduleNextTick();
        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => {
            window.clearTimeout(timeoutId);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, []);

    return now;
}
