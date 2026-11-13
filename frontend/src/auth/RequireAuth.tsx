import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router';
import { useAuth } from './useAuth';

// Wrap any page that needs a logged-in user. No session -> back to the login page, and the login
// page sends them to where they were headed once they're in (e.g. a friend request email link).
function RequireAuth({ children }: { children: ReactNode }) {
    const { session, loading } = useAuth();
    const location = useLocation();

    if (loading) return <p role="status">Loading…</p>;
    if (!session) return <Navigate to="/" replace state={{ from: location }} />;
    return <>{children}</>;
}

export default RequireAuth;
