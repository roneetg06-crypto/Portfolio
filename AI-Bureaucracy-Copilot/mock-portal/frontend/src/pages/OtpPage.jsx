import React, { useState } from 'react';

export const OtpPage = ({ sessionId, onOtpSuccess, apiBaseUrl }) => {
  const [otpCode, setOtpCode] = useState('');
  const [otpHint, setOtpHint] = useState(null);
  const [loadingHint, setLoadingHint] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const fetchOtpHint = async () => {
    setLoadingHint(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/auth/otp/hint?session_id=${sessionId}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to fetch OTP token.');
      setOtpHint(data.otp_hint);
      setOtpCode(data.otp_hint); // convenient auto-fill for quick testing
    } catch (err) {
      setError(err.message || 'Error retrieving authentication token.');
    } finally {
      setLoadingHint(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/auth/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          otp_code: otpCode.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Invalid OTP code.');
      }

      onOtpSuccess();
    } catch (err) {
      setError(err.message || 'Aadhaar OTP verification failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="portal-page-card">
      <div className="page-header">
        <span className="step-tag">Step 3 of 8</span>
        <h2>Aadhaar Two-Factor Authentication / आधार द्वि-चरणीय प्रमाणीकरण (OTP)</h2>
        <p className="page-desc">
          Enter the 6-digit One-Time Password sent to your Aadhaar-registered mobile number (+91 ******4321).
        </p>
      </div>

      <div className="security-barrier-badge">
        📱 आधार सुरक्षा द्वार / Aadhaar e-KYC Verification: Mandatory Two-Factor Authentication (2FA)
      </div>

      <div className="simulated-otp-box">
        <strong>📲 राष्ट्रीय प्रमाणीकरण सेवा / National Authentication Service (Aadhaar e-KYC):</strong>
        <p>
          A high-priority OTP has been dispatched to your linked mobile number.
          In case of network delay, you may retrieve the official gateway authentication token below:
        </p>
        <button
          type="button"
          className="portal-secondary-btn"
          onClick={fetchOtpHint}
          disabled={loadingHint}
        >
          {loadingHint ? 'Connecting to Gateway...' : otpHint ? `Gateway Token: ${otpHint}` : '🔑 Retrieve Gateway Authentication Token'}
        </button>
      </div>

      {error && <div className="portal-alert error">{error}</div>}

      <form onSubmit={handleSubmit} className="portal-form">
        <div className="portal-form-group">
          <label htmlFor="otpInput">Enter 6-Digit Aadhaar Verification Code / 6-अंकीय ओटीपी दर्ज करें:</label>
          <input
            id="otpInput"
            type="text"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            maxLength={6}
            placeholder="e.g. 583921"
            required
            disabled={submitting}
            autoFocus
          />
        </div>

        <button
          type="submit"
          className="portal-primary-btn"
          disabled={submitting || otpCode.length < 6}
        >
          {submitting ? 'Verifying with UIDAI...' : 'Verify OTP & Proceed / ओटीपी सत्यापित करें ➔'}
        </button>
      </form>
    </div>
  );
};
