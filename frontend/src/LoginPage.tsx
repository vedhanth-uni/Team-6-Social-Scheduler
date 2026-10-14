import './login.css';

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
        <p className="login-subtitle">Please login or create account</p>

        <form className="login-form">
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

          <div className="login-buttons">
            <button type="button" className="login-button">
              Login
            </button>

            <button type="button" className="signup-button">
              Sign-Up
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

export default LoginPage;
