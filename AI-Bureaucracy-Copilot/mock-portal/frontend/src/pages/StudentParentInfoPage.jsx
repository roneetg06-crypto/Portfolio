import React, { useState, useEffect } from 'react';

export const StudentParentInfoPage = ({
  studentData,
  onSaveAndNext,
  username,
  sessionId,
}) => {
  const [formData, setFormData] = useState({
    studentName: studentData.studentName || studentData.student_name || studentData.applicant_name || '',
    dateOfBirth: studentData.dateOfBirth || studentData.date_of_birth || '',
    gender: studentData.gender || 'Female',
    state: studentData.state || '',
    district: studentData.district || '',
    category: studentData.category || 'General',
    parentName: studentData.parentName || studentData.parent_name || '',
    parentOccupation: studentData.parentOccupation || studentData.parent_occupation || 'Salaried / Private',
    annualFamilyIncome: studentData.annualFamilyIncome || studentData.annual_family_income || studentData.annual_income || '',
    aadhaarLastFour: studentData.aadhaarLastFour || studentData.aadhaar_last_four || '',
  });

  useEffect(() => {
    if (studentData && Object.keys(studentData).length > 0) {
      setFormData((prev) => ({
        ...prev,
        studentName: studentData.studentName || studentData.student_name || studentData.applicant_name || prev.studentName,
        dateOfBirth: studentData.dateOfBirth || studentData.date_of_birth || prev.dateOfBirth,
        gender: studentData.gender || prev.gender,
        state: studentData.state || prev.state,
        district: studentData.district || prev.district,
        category: studentData.category || prev.category,
        parentName: studentData.parentName || studentData.parent_name || prev.parentName,
        parentOccupation: studentData.parentOccupation || studentData.parent_occupation || prev.parentOccupation,
        annualFamilyIncome: studentData.annualFamilyIncome || studentData.annual_family_income || studentData.annual_income || prev.annualFamilyIncome,
        aadhaarLastFour: studentData.aadhaarLastFour || studentData.aadhaar_last_four || prev.aadhaarLastFour,
      }));
    }
  }, [studentData]);

  const [error, setError] = useState(null);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.studentName.trim()) {
      setError('Student name is required.');
      return;
    }
    if (!formData.parentName.trim()) {
      setError('Parent / Guardian name is required.');
      return;
    }
    if (!formData.aadhaarLastFour || String(formData.aadhaarLastFour).length < 4) {
      setError('Please provide the last 4 digits of Aadhaar.');
      return;
    }
    setError(null);
    onSaveAndNext(formData);
  };

  return (
    <div className="portal-page-card">
      <div className="page-header">
        <span className="step-tag">Step 4 of 8</span>
        <h2>Student & Parent Information / छात्र एवं अभिभावक विवरण</h2>
        <p className="page-desc">
          Authenticated Session: <strong>{username}</strong> (Ref: {sessionId ? sessionId.slice(0, 8) : 'central'}...)
        </p>
      </div>

      <div className="gov-section-header">
        <span>📋 भाग 1: आवेदक एवं अभिभावक विवरण / Section 1: Applicant & Guardian Particulars (DigiLocker & Central Registry Verified)</span>
      </div>

      {error && <div className="portal-alert error">{error}</div>}

      <form onSubmit={handleSubmit} className="portal-form" id="studentParentForm">
        {/* Student Personal Details */}
        <h3 style={{ fontSize: '1.05rem', color: '#1e3a8a', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.4rem', marginTop: '0.5rem' }}>
          A. Student Particulars
        </h3>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="studentName">Student Full Name:</label>
            <input
              id="studentName"
              name="studentName"
              data-testid="studentName"
              type="text"
              value={formData.studentName}
              onChange={(e) => handleChange('studentName', e.target.value)}
              placeholder="e.g. Priya Sharma"
              required
            />
          </div>

          <div className="portal-form-group" style={{ maxWidth: '170px' }}>
            <label htmlFor="dateOfBirth">Date of Birth:</label>
            <input
              id="dateOfBirth"
              name="dateOfBirth"
              data-testid="dateOfBirth"
              type="date"
              value={formData.dateOfBirth}
              onChange={(e) => handleChange('dateOfBirth', e.target.value)}
              required
            />
          </div>

          <div className="portal-form-group" style={{ maxWidth: '140px' }}>
            <label htmlFor="gender">Gender:</label>
            <select
              id="gender"
              name="gender"
              data-testid="gender"
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
            <label htmlFor="state">State of Domicile:</label>
            <input
              id="state"
              name="state"
              data-testid="state"
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
              data-testid="district"
              type="text"
              value={formData.district}
              onChange={(e) => handleChange('district', e.target.value)}
              required
            />
          </div>

          <div className="portal-form-group" style={{ maxWidth: '140px' }}>
            <label htmlFor="category">Social Category:</label>
            <select
              id="category"
              name="category"
              data-testid="category"
              value={formData.category}
              onChange={(e) => handleChange('category', e.target.value)}
            >
              <option value="General">General</option>
              <option value="OBC">OBC</option>
              <option value="SC">SC</option>
              <option value="ST">ST</option>
              <option value="EWS">EWS</option>
            </select>
          </div>
        </div>

        {/* Parent / Guardian Details */}
        <h3 style={{ fontSize: '1.05rem', color: '#1e3a8a', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.4rem', marginTop: '1rem' }}>
          B. Parent / Co-Borrower Details
        </h3>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="parentName">Parent / Guardian Full Name:</label>
            <input
              id="parentName"
              name="parentName"
              data-testid="parentName"
              type="text"
              value={formData.parentName}
              onChange={(e) => handleChange('parentName', e.target.value)}
              placeholder="e.g. Ramesh Sharma"
              required
            />
          </div>

          <div className="portal-form-group">
            <label htmlFor="parentOccupation">Parent Occupation:</label>
            <select
              id="parentOccupation"
              name="parentOccupation"
              data-testid="parentOccupation"
              value={formData.parentOccupation}
              onChange={(e) => handleChange('parentOccupation', e.target.value)}
            >
              <option value="Salaried / Government">Salaried / Government</option>
              <option value="Salaried / Private">Salaried / Private</option>
              <option value="Business / Self-Employed">Business / Self-Employed</option>
              <option value="Agriculture / Farmer">Agriculture / Farmer</option>
              <option value="Retired / Other">Retired / Other</option>
            </select>
          </div>
        </div>

        <div className="portal-form-row">
          <div className="portal-form-group">
            <label htmlFor="annualFamilyIncome">Annual Family Income (INR):</label>
            <input
              id="annualFamilyIncome"
              name="annualFamilyIncome"
              data-testid="annualFamilyIncome"
              type="number"
              value={formData.annualFamilyIncome}
              onChange={(e) => handleChange('annualFamilyIncome', Number(e.target.value))}
              required
            />
          </div>

          <div className="portal-form-group">
            <label htmlFor="aadhaarLastFour">Student Aadhaar (Last 4 Digits):</label>
            <input
              id="aadhaarLastFour"
              name="aadhaarLastFour"
              data-testid="aadhaarLastFour"
              type="text"
              value={formData.aadhaarLastFour}
              onChange={(e) => handleChange('aadhaarLastFour', e.target.value.replace(/\D/g, '').slice(0, 4))}
              maxLength={4}
              placeholder="5821"
              required
            />
          </div>
        </div>

        <button
          id="nextToLoanBtn"
          type="submit"
          className="portal-primary-btn"
          style={{ marginTop: '1.2rem' }}
        >
          Save & Proceed to Loan Information →
        </button>
      </form>
    </div>
  );
};
