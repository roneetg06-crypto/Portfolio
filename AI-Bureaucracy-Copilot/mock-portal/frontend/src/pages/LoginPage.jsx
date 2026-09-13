import React, { useState } from 'react';

export const LoginPage = ({ onLoginSuccess, apiBaseUrl, runId }) => {
  const [username, setUsername] = useState('citizen_demo');
  const [password, setPassword] = useState('Password123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, run_id: runId || null }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Authentication failed.');
      }

      onLoginSuccess(data.session_id, data.username);
    } catch (err) {
      setError(err.message || 'Failed to connect to national authentication gateway.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="portal-page-card">
      <div className="page-header">
        <span className="step-tag">Step 1 of 8</span>
        <h2>Citizen Login & Identity Authentication / नागरिक लॉगिन</h2>
        <p className="page-desc">
          Please sign in with your registered National Citizen ID to access the Higher Education Credit Application Gateway.
        </p>
      </div>

      <div className="test-credentials-box">
        <strong>पंजीकृत नागरिक लॉगिन क्रेडेंशियल / Registered Portal Credentials (IBA Database):</strong>
        <code>Citizen ID: citizen_demo | Password: Password123!</code>
      </div>

      {error && <div className="portal-alert error">{error}</div>}

      <form onSubmit={handleSubmit} className="portal-form">
        <div className="portal-form-group">
          <label htmlFor="username">Citizen ID / पंजीकृत उपयोगकर्ता नाम:</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <div className="portal-form-group">
          <label htmlFor="password">Password / पासवर्ड:</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <button type="submit" className="portal-primary-btn" disabled={loading}>
          {loading ? 'Authenticating...' : 'Sign In to Portal / सुरक्षित प्रवेश ➔'}
        </button>
      </form>
    </div>
  );
};
