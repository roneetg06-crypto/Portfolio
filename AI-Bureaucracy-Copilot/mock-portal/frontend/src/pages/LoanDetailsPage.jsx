import React, { useState, useEffect } from 'react';

export const LoanDetailsPage = ({
  loanData,
  onSaveAndNext,
  onBack,
  username,
  sessionId,
}) => {
  const [formData, setFormData] = useState({
    course: loanData.course || '',
    college: loanData.college || '',
    loanAmount: loanData.loanAmount || loanData.loan_amount || '',
    tuitionFee: loanData.tuitionFee || loanData.tuition_fee || '',
    livingExpenses: loanData.livingExpenses || loanData.living_expenses || '',
    bankPreference: loanData.bankPreference || loanData.bank_preference || 'State Bank of India',
    loanTenure: loanData.loanTenure || loanData.loan_tenure || '10 Years',
  });

  useEffect(() => {
    if (loanData && Object.keys(loanData).length > 0) {
      setFormData((prev) => ({
        ...prev,
        course: loanData.course || prev.course,
        college: loanData.college || prev.college,
        loanAmount: loanData.loanAmount || loanData.loan_amount || prev.loanAmount,
        tuitionFee: loanData.tuitionFee || loanData.tuition_fee || prev.tuitionFee,
        livingExpenses: loanData.livingExpenses || loanData.living_expenses || prev.livingExpenses,
        bankPreference: loanData.bankPreference || loanData.bank_preference || prev.bankPreference,
        loanTenure: loanData.loanTenure || loanData.loan_tenure || prev.loanTenure,
      }));
    }
  }, [loanData]);

  const [error, setError] = useState(null);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.course.trim()) {
      setError('Course name is required.');
      return;
    }
    if (!formData.college.trim()) {
      setError('College or institution name is required.');
      return;
    }
    if (!formData.loanAmount || Number(formData.loanAmount) <= 0) {
      setError('Please provide a valid loan amount.');
      return;
    }
    setError(null);
    onSaveAndNext(formData);
  };

  return (
    <div className="portal-page-card">
      <div className="page-header">
        <span className="step-tag">Step 5 of 8</span>
        <h2>Education Loan & Sanction Schedule / उच्च शिक्षा ऋण विवरण</h2>
        <p className="page-desc">
          Academic Program, Institution Affiliation and Financial Sanction Requirements
        </p>
      </div>

      <div className="gov-section-header">
        <span>🏛️ भाग 2: शैक्षणिक कार्यक्रम एवं वित्तीय आवश्यकताएं / Section 2: Academic Program & Financial Sanction Schedule</span>
      </div>

      {error && <div className="portal-alert error">{error}</div>}

      <form onSubmit={handleSubmit} className="portal-form" id="loanDetailsForm">
        {/* Academic Program */}
        <h3 style={{ fontSize: '1.05rem', color: '#1e3a8a', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.4rem', marginTop: '0.5rem' }}>
          A. Academic Institution & Course
        </h3>

        <div className="portal-form-group">
          <label htmlFor="course">Course / Degree Program:</label>
          <input
            id="course"
            name="course"
            data-testid="course"
            type="text"
            value={formData.course}
            onChange={(e) => handleChange('course', e.target.value)}
            placeholder="e.g. B.Tech Computer Science and Engineering"
            required
          />
        </div>

        <div className="portal-form-group">
          <label htmlFor="college">College / University Name:</label>
          <input
            id="college"
            name="college"
            data-testid="college"
            type="text"
            value={formData.college}
            onChange={(e) => handleChange('college', e.target.value)}
            placeholder="e.g. National Institute of Technology"
            required
          />
        </div>

        {/* Loan Financial Breakdown */}
        <h3 style={{ fontSize: '1.05rem', color: '#1e3a8a', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.4rem', marginTop: '1rem' }}>
          B. Financial Breakdown & Bank Preference
        </h3>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="loanAmount">Total Loan Amount (INR):</label>
            <input
              id="loanAmount"
              name="loanAmount"
              data-testid="loanAmount"
              type="number"
              value={formData.loanAmount}
              onChange={(e) => handleChange('loanAmount', Number(e.target.value))}
              required
            />
          </div>

          <div className="portal-form-group">
            <label htmlFor="tuitionFee">Course Tuition Fee (INR):</label>
            <input
              id="tuitionFee"
              name="tuitionFee"
              data-testid="tuitionFee"
              type="number"
              value={formData.tuitionFee}
              onChange={(e) => handleChange('tuitionFee', Number(e.target.value))}
              required
            />
          </div>

          <div className="portal-form-group">
            <label htmlFor="livingExpenses">Living / Hostel Expenses (INR):</label>
            <input
              id="livingExpenses"
              name="livingExpenses"
              data-testid="livingExpenses"
              type="number"
              value={formData.livingExpenses}
              onChange={(e) => handleChange('livingExpenses', Number(e.target.value))}
              required
            />
          </div>
        </div>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="bankPreference">Preferred Lending Bank:</label>
            <select
              id="bankPreference"
              name="bankPreference"
              data-testid="bankPreference"
              value={formData.bankPreference}
              onChange={(e) => handleChange('bankPreference', e.target.value)}
            >
              <option value="State Bank of India">State Bank of India</option>
              <option value="Punjab National Bank">Punjab National Bank</option>
              <option value="Bank of Baroda">Bank of Baroda</option>
              <option value="Canara Bank">Canara Bank</option>
              <option value="Union Bank of India">Union Bank of India</option>
              <option value="HDFC Bank">HDFC Bank</option>
            </select>
          </div>

          <div className="portal-form-group">
            <label htmlFor="loanTenure">Repayment Tenure:</label>
            <select
              id="loanTenure"
              name="loanTenure"
              data-testid="loanTenure"
              value={formData.loanTenure}
              onChange={(e) => handleChange('loanTenure', e.target.value)}
            >
              <option value="5 Years">5 Years</option>
              <option value="7 Years">7 Years</option>
              <option value="10 Years">10 Years</option>
              <option value="15 Years">15 Years</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.2rem' }}>
          <button
            type="button"
            className="portal-secondary-btn"
            onClick={onBack}
          >
            ← Back to Student Info
          </button>
          <button
            id="nextToDocsBtn"
            type="submit"
            className="portal-primary-btn"
            style={{ flex: 1 }}
          >
            Save & Proceed to Document Upload →
          </button>
        </div>
      </form>
    </div>
  );
};
