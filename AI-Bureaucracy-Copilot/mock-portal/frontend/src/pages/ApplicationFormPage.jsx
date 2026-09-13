import React, { useEffect, useState } from 'react';

export const ApplicationFormPage = ({
  sessionId,
  username,
  runId,
  schemeId,
  profileId,
  onApplicationSuccess,
  apiBaseUrl,
}) => {
  const [formData, setFormData] = useState({
    scheme_id: schemeId || 'SCH-HLT-001',
    applicant_name: 'Priya Sharma',
    age: 34,
    gender: 'Female',
    state: 'Andhra Pradesh',
    district: 'Visakhapatnam',
    annual_income: 180000,
    aadhaar_last_four: '5821',
    declaration_agreed: false,
  });

  const [loadingPrefill, setLoadingPrefill] = useState(false);
  const [prefillSource, setPrefillSource] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadPrefill = async () => {
      setLoadingPrefill(true);
      try {
        const params = new URLSearchParams();
        if (runId) params.append('run_id', runId);
        if (profileId) params.append('profile_id', profileId);
        if (schemeId) params.append('scheme_id', schemeId);

        const res = await fetch(`${apiBaseUrl}/api/application/prefill?${params.toString()}`);
        if (res.ok) {
          const prefill = await res.json();
          setFormData((prev) => ({
            ...prev,
            scheme_id: prefill.scheme_id || prev.scheme_id,
            applicant_name: prefill.applicant_name || prev.applicant_name,
            age: prefill.age || prev.age,
            gender: prefill.gender || prev.gender,
            state: prefill.state || prev.state,
            district: prefill.district || prev.district,
            annual_income: prefill.annual_income || prev.annual_income,
            aadhaar_last_four: prefill.aadhaar_last_four || prev.aadhaar_last_four,
          }));
          if (prefill.source && prefill.source !== 'mock_default') {
            setPrefillSource(prefill.source);
          }
        }
      } catch (err) {
        console.warn('Could not load prefill data:', err);
      } finally {
        setLoadingPrefill(false);
      }
    };

    loadPrefill();
  }, [runId, profileId, schemeId, apiBaseUrl]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.declaration_agreed) {
      setError('You must check and agree to the statutory declaration.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/application/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          scheme_id: formData.scheme_id,
          applicant_name: formData.applicant_name,
          age: Number(formData.age),
          gender: formData.gender,
          state: formData.state,
          district: formData.district,
          annual_income: Number(formData.annual_income),
          aadhaar_last_four: formData.aadhaar_last_four,
          declaration_agreed: formData.declaration_agreed,
          run_id: runId || null,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Submission failed.');
      }

      onApplicationSuccess(data);
    } catch (err) {
      setError(err.message || 'Application submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="portal-page-card">
      <div className="page-header">
        <span className="step-tag">Step 4 of 5</span>
        <h2>Scheme Benefit Application Form</h2>
        <p className="page-desc">
          Authenticated Session: <strong>{username}</strong> (ID: {sessionId.slice(0, 8)}...)
        </p>
      </div>

      <div className="security-barrier-badge">
        ✍️ Human-In-The-Loop Security Gate: Final Citizen Review & Consent
      </div>

      {prefillSource && (
        <div className="portal-prefill-banner">
          ✓ Form data pre-filled from Copilot Citizen Dossier ({formData.applicant_name}, {formData.state})
        </div>
      )}

      {error && <div className="portal-alert error">{error}</div>}

      <form onSubmit={handleSubmit} className="portal-form">
        <div className="portal-form-group">
          <label htmlFor="scheme_id">Selected Government Scheme:</label>
          <select
            id="scheme_id"
            name="scheme_id"
            value={formData.scheme_id}
            onChange={(e) => handleChange('scheme_id', e.target.value)}
          >
            <option value="SCH-HLT-001">Ayushman Bharat - PM-JAY (Central)</option>
            <option value="SCH-HLT-002">National Health Mission - NHM (Central)</option>
            <option value="SCH-HLT-003">PM-ABHIM Health Infrastructure Mission (Central)</option>
            <option value="SCH-HLT-004">Dr. YSR Aarogyasri Scheme (Andhra Pradesh)</option>
            <option value="SCH-HLT-005">Karunya Arogya Suraksha Padhathi - KASP (Kerala)</option>
            <option value="SCH-HLT-006">Chief Minister's Comprehensive Health Insurance (Tamil Nadu)</option>
          </select>
        </div>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="applicant_name">Applicant Full Name:</label>
            <input
              id="applicant_name"
              name="applicant_name"
              type="text"
              value={formData.applicant_name}
              onChange={(e) => handleChange('applicant_name', e.target.value)}
              required
            />
          </div>
          <div className="portal-form-group" style={{ maxWidth: '120px' }}>
            <label htmlFor="age">Age:</label>
            <input
              id="age"
              name="age"
              type="number"
              value={formData.age}
              onChange={(e) => handleChange('age', e.target.value)}
              required
            />
          </div>
          <div className="portal-form-group">
            <label htmlFor="gender">Gender:</label>
            <select
              id="gender"
              name="gender"
              value={formData.gender}
              onChange={(e) => handleChange('gender', e.target.value)}
            >
              <option value="Female">Female</option>
              <option value="Male">Male</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="state">State of Residence:</label>
            <input
              id="state"
              name="state"
              type="text"
              value={formData.state}
              onChange={(e) => handleChange('state', e.target.value)}
              required
            />
          </div>
          <div className="portal-form-group">
            <label htmlFor="district">District:</label>
            <input
              id="district"
              name="district"
              type="text"
              value={formData.district}
              onChange={(e) => handleChange('district', e.target.value)}
              required
            />
          </div>
        </div>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="annual_income">Annual Family Income (INR):</label>
            <input
              id="annual_income"
              name="annual_income"
              type="number"
              value={formData.annual_income}
              onChange={(e) => handleChange('annual_income', e.target.value)}
              required
            />
          </div>
          <div className="portal-form-group">
            <label htmlFor="aadhaar_last_four">Aadhaar Number (Last 4 digits):</label>
            <input
              id="aadhaar_last_four"
              name="aadhaar_last_four"
              type="text"
              value={formData.aadhaar_last_four}
              onChange={(e) => handleChange('aadhaar_last_four', e.target.value)}
              maxLength={4}
              required
            />
          </div>
        </div>

        <div className="portal-declaration-box">
          <label className="checkbox-label" htmlFor="declaration_agreed">
            <input
              id="declaration_agreed"
              name="declaration_agreed"
              type="checkbox"
              checked={formData.declaration_agreed}
              onChange={(e) => handleChange('declaration_agreed', e.target.checked)}
            />
            <span>
              I hereby solemnly affirm that all particulars entered above are true and complete.
              I authorize verification against relevant government databases.
            </span>
          </label>
        </div>

        <button
          id="submitApplicationBtn"
          type="submit"
          className="portal-primary-btn"
          disabled={submitting || !formData.declaration_agreed}
        >
          {submitting ? 'Submitting Application...' : 'Confirm & Submit Application →'}
        </button>

      </form>
    </div>
  );
};
