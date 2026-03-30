// File: Login.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

// Icons
import worker from "../assets/icons/worker.png";
import logo from "../assets/icons/logo.png";

const Login = ({ setIsAuthenticated }) => {
  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  // Handle login submit
  const handleSubmit = (e) => {
    e.preventDefault();

    // Temporary hardcoded login check
    if (email === "admin@gmail.com" && password === "123") {
      setIsAuthenticated(true);

      // Persist login if "Remember Me" checked
      if (rememberMe) {
        localStorage.setItem("isAuthenticated", "true");
      }

      navigate("/"); // Redirect to home
    } else {
      setError("Invalid email or password");
    }
  };

  return (
    <div className="container-fluid login-container">
      <div className="row vh-100">
        
        {/* ───────────── Left Section (Image + Branding) ───────────── */}
        <div className="col-md-6 d-none d-md-flex flex-column align-items-center justify-content-center text-center login-left">
          <img src={worker} alt="Worker Icon" className="img-fluid w-75 mb-4" />
          <img src={logo} alt="AI COMS Logo" className="img-fluid w-25 mb-3" />
          <p className="px-4 fs-5 text-muted">
            Smart Manufacturing Safety Monitoring System
          </p>
        </div>

        {/* ───────────── Right Section (Login Form) ───────────── */}
        <div className="col-md-3 d-flex flex-column align-items-center justify-content-center text-center bg-white p-4">
          <h2 className="mb-4 fw-bold">Login Account</h2>

          <form className="login-form w-100" onSubmit={handleSubmit}>
            
            {/* Email Input */}
            <input
              type="email"
              className="form-control mb-3 py-2 px-3 rounded border-0 bg-light"
              placeholder="Email ID"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            {/* Password Input */}
            <input
              type="password"
              className="form-control mb-4 py-2 px-3 rounded border-0 bg-light"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {/* Remember Me + Support Link */}
            <div className="d-flex justify-content-between align-items-center mb-4">
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="rememberMe"
                  checked={rememberMe}
                  onChange={() => setRememberMe(!rememberMe)}
                />
                <label className="form-check-label ms-2" htmlFor="rememberMe">
                  Remember me
                </label>
              </div>
              <a href="/support" className="text-primary text-decoration-none support">
                Support
              </a>
            </div>

            {/* Error Message */}
            {error && (
              <div className="alert alert-danger w-100 text-center py-2">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button type="submit" className="btn btn-dark w-100 py-2 rounded-pill">
              Login
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
