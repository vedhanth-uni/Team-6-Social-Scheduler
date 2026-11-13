import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { isAuthApiError } from '@supabase/supabase-js';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '../supabaseClient';
import { AuthContext } from './authContext';

// Keeps the Supabase session in React state so any component can ask "am I logged in?".
//
// - getSession() reads the saved session and refreshes the token if it has expired.
// - getUser() then asks Supabase's server whether that session is still real. The saved session
//   alone isn't proof: it could have been revoked (signed out on another device, user deleted).
//   Only an explicit rejection (a 4xx answer) logs the person out. If we simply can't reach
//   Supabase, or it is rate limiting or down, we keep the session so a bad moment doesn't kick
//   people out.
// - onAuthStateChange keeps us in sync afterwards: login, logout, automatic token refresh,
//   and a logout in another browser tab.
function AuthProvider({ children }: { children: ReactNode }) {
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let active = true;

        async function init() {
            const first = await supabase.auth.getSession();
            if (first.data.session) {
                const { error } = await supabase.auth.getUser();
                const rejected = error && isAuthApiError(error) && error.status !== 429 && error.status < 500;
                if (rejected) await supabase.auth.signOut({ scope: 'local' });
            }
            // Read the session again instead of reusing `first`: validation may have just ended it,
            // and the listener below may already have reported that.
            const { data } = await supabase.auth.getSession();
            if (active) {
                setSession(data.session);
                setLoading(false);
            }
        }
        void init();

        // keep this callback synchronous: calling supabase methods inside it can deadlock
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, next) => {
            if (!active) return;
            setSession(next);
            setLoading(false);
        });

        return () => {
            active = false;
            subscription.unsubscribe();
        };
    }, []);

    const value = useMemo(() => ({ session, loading }), [session, loading]);
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthProvider;
