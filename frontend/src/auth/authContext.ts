import { createContext } from 'react';
import type { Session } from '@supabase/supabase-js';

export interface AuthState {
    session: Session | null;
    // true until we know whether there is a valid session (first load only)
    loading: boolean;
}

export const AuthContext = createContext<AuthState | undefined>(undefined);
