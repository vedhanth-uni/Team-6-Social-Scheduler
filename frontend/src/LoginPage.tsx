function LoginPage() {
  return (
    <main className="login-page">
      <h1 className="login-title">Social Calendar</h1>

      <section className="login-container">
        <h2>Hello</h2>
        <p>Please login or create account</p>

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
