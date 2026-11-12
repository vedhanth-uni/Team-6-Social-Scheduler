import './LoginPage.css';
import {supabase} from './supabaseClient';
import { useState } from "react";
import { Link } from 'react-router';

type AuthMode = "login" | "signup";


function LoginForm() {
  const [isSelected, setIsSelected] = useState<Boolean>(false);
  const [mode, setMode] = useState<AuthMode>("login");

  //recall that this type for event might be wrong
  async function handleSubmit(e: React.SubmitEvent) {
    //prevent browser from reloading the page
    e.preventDefault();

    //read form data
    const form = e.target;
    const formData = new FormData(form);
    
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;

    if (mode === "login") {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if(error) {
        console.error('login failed:', error.message);
        return;
      }

      console.log('Logged in user:', data.user);
    } else {
      const {data, error} = await supabase.auth.signUp({
        email,
        password
      });

      if(error) {
        console.error('signup failed:', error.message);
        return;
      } else {
        //tell them to check email for confirmation email
      }

      console.log('Signed up user:', data.user);
    }
    
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
                autoComplete="current-password"
                required
              />
            </div>

            <button type="submit" className="signup-button">
              <Link className='link' to='/Dash'> {mode === "login" ? "Log In" : "Create Account"} </Link>
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


//TODO: validate if form data is string, since FormData is a built-in browser api st .get can return null
//TODO: show text to user that confirms button clicked/signup/login

export default LoginPage;
