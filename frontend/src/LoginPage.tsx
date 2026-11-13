import './LoginPage.css';
import {supabase} from './supabaseClient';
import { useState } from "react";
import { Navigate, useLocation } from 'react-router';
import { useAuth } from './auth/useAuth';

type AuthMode = "login" | "signup";


function LoginForm() {
  const [isSelected, setIsSelected] = useState<boolean>(false);
  const [mode, setMode] = useState<AuthMode>("login");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.SubmitEvent<HTMLFormElement>) {
    //prevent browser from reloading the page
    e.preventDefault();

    //read form data (FormData.get can return null or a File, so only accept strings)
    const formData = new FormData(e.currentTarget);
    const email = formData.get('email');
    const password = formData.get('password');
    if (typeof email !== 'string' || typeof password !== 'string') return;

    setError(null);
    setNotice(null);
    setSubmitting(true);

    // We don't navigate here. When login succeeds Supabase announces it, AuthProvider updates,
    // and LoginPage (below) redirects to the dashboard. A failed login can never get past this page.
    if (mode === "login") {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) setError(error.message);
    } else {
      const { data, error } = await supabase.auth.signUp({ email, password });
      if (error) {
        setError(error.message);
      } else if (!data.session) {
        // email confirmation is on: no session until they click the link we just emailed
        setNotice("Check your email to confirm your account, then log in.");
        setMode("login");
      }
    }
    setSubmitting(false);
  }

  return (
    <div>
      {isSelected ? (
        <section>
          <p className="login-subtitle">Welcome!</p>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                name="email"
                type="email"
                placeholder="Enter your email"
                autoComplete="email"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                placeholder="Enter your password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
              />
            </div>

            {error && <p role="alert">{error}</p>}
            {notice && <p role="status">{notice}</p>}

            <button type="submit" className="signup-button" disabled={submitting}>
              {mode === "login" ? "Log In" : "Create Account"}
            </button>
          </form>
        </section>
      ) : ( 
      <section>
        <p className="login-subtitle">Please login or create account</p>

        <div className="login-buttons">
          <button type="button" className="login-button" onClick={() => {setMode("login"); setIsSelected(true);}}>
            Login
          </button>

          <button type="button" className="signup-button" onClick={() => {setMode("signup"); setIsSelected(true);}}>
            Sign-Up
          </button>
        </div>
      </section>   
      )}
    </div>
  )
}

function LoginPage() {
  const { session, loading } = useAuth();
  const location = useLocation();

  if (loading) return <p role="status">Loading…</p>;
  if (session) {
    // send them where they were headed before being asked to log in (set by RequireAuth)
    const from = location.state?.from;
    const to = from ? `${from.pathname}${from.search ?? ''}${from.hash ?? ''}` : '/Dash';
    return <Navigate to={to} replace />;
  }

  return (
    <main className="login-page">
      <div className = "logo-container">
        <img
          src="/logo.svg"
          className="human-logo"
          />
          <div className = "green-logo-wrapper">
            <img
              src="/green_logo.svg"
              className="green-logo"
            />
            <img
              src="/social calendar.svg"
              className="logo-text"
            />
          </div>

      </div>

      <section className="login-container">
        <LoginForm/>
      </section>
    </main>
  );
}


//TODO: show text to user that confirms button clicked/signup/login

export default LoginPage;
