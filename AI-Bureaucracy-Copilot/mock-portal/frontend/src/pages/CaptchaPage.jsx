import React, { useEffect, useState } from 'react';

export const CaptchaPage = ({ sessionId, onCaptchaSuccess, apiBaseUrl }) => {
  const [captchaText, setCaptchaText] = useState('');
  const [userAnswer, setUserAnswer] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const fetchCaptcha = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/auth/captcha?session_id=${sessionId}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load CAPTCHA.');
      setCaptchaText(data.captcha_text);
      setUserAnswer('');
    } catch (err) {
      setError(err.message || 'Error loading CAPTCHA challenge.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCaptcha();
  }, [sessionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/auth/captcha/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          captcha_response: userAnswer,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Incorrect CAPTCHA entered.');
      }

      onCaptchaSuccess();
    } catch (err) {
      setError(err.message || 'CAPTCHA verification failed. Please try again.');
      // Reload on failure
      fetchCaptcha();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="portal-page-card">
      <div className="page-header">
        <span className="step-tag">Step 2 of 8</span>
        <h2>Security Verification Code / सुरक्षा कोड सत्यापन (CAPTCHA)</h2>
        <p className="page-desc">
          Please enter the security verification code displayed below to validate authentic citizen access.
        </p>
      </div>

      <div className="security-barrier-badge">
        🔒 पोर्टल सुरक्षा सत्यापन / Gateway Integrity Verification: Mandatory Human Perception Check
      </div>

      {error && <div className="portal-alert error">{error}</div>}

      <div className="captcha-display-container">
        {loading ? (
          <div className="captcha-loading" style={{ color: '#7A1C1C', fontWeight: 600 }}>
            Generating security challenge...
          </div>
        ) : (
          <div className="captcha-box">
            <span className="captcha-distorted-text">{captchaText}</span>
            <button
              type="button"
              className="captcha-refresh-btn"
              onClick={fetchCaptcha}
              title="Refresh CAPTCHA / कोड रीफ्रेश करें"
            >
              🔄 Refresh Code
            </button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="portal-form">
        <div className="portal-form-group">
          <label htmlFor="captchaAnswer">
            Type the 5 security characters exactly as displayed / सुरक्षा कोड दर्ज करें:
          </label>
          <input
            id="captchaAnswer"
            type="text"
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value.toUpperCase())}
            maxLength={6}
            placeholder="e.g. 7X9KQ"
            required
            disabled={loading || submitting}
            autoFocus
          />
        </div>

        <button
          type="submit"
          className="portal-primary-btn"
          disabled={loading || submitting || !userAnswer.trim()}
        >
          {submitting ? 'Verifying Code...' : 'Verify & Proceed / सत्यापित करें ➔'}
        </button>
      </form>
    </div>
  );
};
