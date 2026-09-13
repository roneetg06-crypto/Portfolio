import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';

interface AuthPageProps {
  onSwitchToLogin: () => void;
}

export const SignupPage: React.FC<AuthPageProps> = ({ onSwitchToLogin }) => {
  const { signup } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please fill in all mandatory fields.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters in length.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await signup(email.trim(), password);
    } catch (err: any) {
      setError(err.message || 'Signup failed. Please check your inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="gov-auth-page">
      {/* Full-width sticky government navbar in auth mode */}
      <Navbar
        isAuthMode={true}
        authModeType="signup"
        onSwitchAuthMode={onSwitchToLogin}
      />

      {/* Main Full-Screen Body */}
      <main className="gov-auth-main">
        <div className="gov-auth-banner-panel">
          <div className="gov-topline">भारत सरकार नागरिक पंजीकरण | Official Citizen Enrollment</div>
          <h1>Citizen Enrollment & Verification Portal</h1>
          <p>Create your verified Citizen ID to access automated welfare schemes and autonomous document filing</p>
        </div>

        {/* Generous, responsive, elevated registration card */}
        <div className="gov-auth-card">
          <div className="gov-card-header">
            <h2 className="gov-auth-heading">New User Registration / नया नागरिक पंजीकरण</h2>
            <p className="gov-auth-subtext">Register your profile to discover eligible welfare schemes and track applications</p>
          </div>

          {error && (
            <div className="gov-alert-error">
              <span className="alert-icon">⚠️</span>
              <div className="alert-text">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="gov-form">
            <div className="gov-field-group">
              <label htmlFor="signup-email" className="gov-label">
                Citizen Email / नागरिक ईमेल <span className="req-star">*</span>
              </label>
              <input
                id="signup-email"
                type="email"
                required
                className="gov-input"
                placeholder="citizen@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="gov-field-group">
              <label htmlFor="signup-password" className="gov-label">
                Create Password / पासवर्ड बनाएं <span className="req-star">*</span>
              </label>
              <input
                id="signup-password"
                type="password"
                required
                className="gov-input"
                placeholder="Minimum 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>

            <div className="gov-field-group">
              <label htmlFor="signup-confirm-password" className="gov-label">
                Confirm Password / पासवर्ड की पुष्टि करें <span className="req-star">*</span>
              </label>
              <input
                id="signup-confirm-password"
                type="password"
                required
                className="gov-input"
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="gov-primary-btn"
            >
              {loading ? (
                <>
                  <span className="gov-spinner"></span> Registering Citizen...
                </>
              ) : (
                'Complete Registration / पंजीकरण पूर्ण करें ➔'
              )}
            </button>
          </form>

          <div className="gov-auth-footer-prompt">
            <span>Already have an account? / पहले से खाता है? </span>
            <button
              type="button"
              className="gov-link-btn"
              onClick={onSwitchToLogin}
            >
              Log In to Portal
            </button>
          </div>

          <div className="gov-security-notice">
            🔒 By enrolling, your credentials are protected with salted bcrypt hashing and stored in a private PostgreSQL database.
          </div>
        </div>
      </main>

      {/* Full-width government footer with disclaimer, quick links, helpline & copyright */}
      <Footer
        isAuthPage={true}
        currentAuthMode="signup"
        onSwitchAuth={() => onSwitchToLogin()}
      />
    </div>
  );
};
