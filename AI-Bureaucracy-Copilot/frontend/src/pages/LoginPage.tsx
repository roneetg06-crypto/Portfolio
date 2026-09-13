import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';

interface AuthPageProps {
  onSwitchToSignup: () => void;
}

export const LoginPage: React.FC<AuthPageProps> = ({ onSwitchToSignup }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await login(email.trim(), password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="gov-auth-page">
      {/* Full-width sticky government navbar in auth mode */}
      <Navbar
        isAuthMode={true}
        authModeType="login"
        onSwitchAuthMode={onSwitchToSignup}
      />

      {/* Main Full-Screen Body */}
      <main className="gov-auth-main">
        <div className="gov-auth-banner-panel">
          <div className="gov-topline">भारत सरकार सार्वजनिक कल्याण | Government Digital Services</div>
          <h1>Unified Citizen Welfare Services Portal</h1>
          <p>Secure Single-Sign-On for Autonomous Bureaucracy, Dynamic Dossiers & Scheme Filings</p>
        </div>

        {/* Generous, responsive, elevated login card */}
        <div className="gov-auth-card">
          <div className="gov-card-header">
            <h2 className="gov-auth-heading">Unified Citizen Access / नागरिक सेवा प्रवेश</h2>
            <p className="gov-auth-subtext">Access your verified profile, eligible welfare schemes & automated filings</p>
          </div>

          {error && (
            <div className="gov-alert-error">
              <span className="alert-icon">⚠️</span>
              <div className="alert-text">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="gov-form">
            <div className="gov-field-group">
              <label htmlFor="login-email" className="gov-label">
                Registered Email / पंजीकृत ईमेल <span className="req-star">*</span>
              </label>
              <input
                id="login-email"
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
              <label htmlFor="login-password" className="gov-label">
                Password / पासवर्ड <span className="req-star">*</span>
              </label>
              <input
                id="login-password"
                type="password"
                required
                className="gov-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="gov-primary-btn"
            >
              {loading ? (
                <>
                  <span className="gov-spinner"></span> Authenticating Citizen...
                </>
              ) : (
                'Secure Login / सुरक्षित प्रवेश ➔'
              )}
            </button>
          </form>

          <div className="gov-auth-footer-prompt">
            <span>New citizen? / नया खाता बनाएं? </span>
            <button
              type="button"
              className="gov-link-btn"
              onClick={onSwitchToSignup}
            >
              Register New Citizen Account
            </button>
          </div>

          <div className="gov-security-notice">
            🔒 Protected by 256-bit JWT Encryption & Isolated Scheme Application Sandboxing.
          </div>
        </div>
      </main>

      {/* Full-width government footer with disclaimer, quick links, helpline & copyright */}
      <Footer
        isAuthPage={true}
        currentAuthMode="login"
        onSwitchAuth={() => onSwitchToSignup()}
      />
    </div>
  );
};
