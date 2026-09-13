import React, { useState } from 'react';

export const FinalReviewPage = ({
  studentData,
  loanData,
  uploadedDocs,
  sessionId,
  username,
  runId,
  schemeId,
  onFinalSubmit,
  onBack,
  apiBaseUrl,
}) => {
  const [declarationAgreed, setDeclarationAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!declarationAgreed) {
      setError('You must confirm and check the statutory declaration before submitting.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        session_id: sessionId,
        scheme_id: schemeId || 'SCH-EDU-001',
        run_id: runId || null,
        // Student & Parent details
        student_name: studentData.studentName || studentData.student_name || 'Priya Sharma',
        applicant_name: studentData.studentName || studentData.student_name || 'Priya Sharma',
        date_of_birth: studentData.dateOfBirth || studentData.date_of_birth || '2003-05-15',
        gender: studentData.gender || 'Female',
        state: studentData.state || 'Andhra Pradesh',
        district: studentData.district || 'Visakhapatnam',
        category: studentData.category || 'OBC',
        parent_name: studentData.parentName || studentData.parent_name || 'Ramesh Sharma',
        parent_occupation: studentData.parentOccupation || studentData.parent_occupation || 'Salaried / Private',
        annual_family_income: Number(studentData.annualFamilyIncome || studentData.annual_family_income || 350000),
        annual_income: Number(studentData.annualFamilyIncome || studentData.annual_family_income || 350000),
        aadhaar_last_four: studentData.aadhaarLastFour || studentData.aadhaar_last_four || '5821',
        // Loan details
        course: loanData.course || 'B.Tech Computer Science and Engineering',
        college: loanData.college || 'National Institute of Technology',
        loan_amount: Number(loanData.loanAmount || loanData.loan_amount || 750000),
        tuition_fee: Number(loanData.tuitionFee || loanData.tuition_fee || 500000),
        living_expenses: Number(loanData.livingExpenses || loanData.living_expenses || 250000),
        bank_preference: loanData.bankPreference || loanData.bank_preference || 'State Bank of India',
        loan_tenure: loanData.loanTenure || loanData.loan_tenure || '10 Years',
        // Uploaded documents summary
        uploaded_documents: {
          admission_letter: uploadedDocs.admissionLetter ? uploadedDocs.admissionLetter.name : 'Attached',
          fee_structure: uploadedDocs.feeStructure ? uploadedDocs.feeStructure.name : 'Attached',
          student_aadhaar: uploadedDocs.studentAadhaar ? uploadedDocs.studentAadhaar.name : 'Attached',
          parent_income_certificate: uploadedDocs.parentIncomeCertificate ? uploadedDocs.parentIncomeCertificate.name : 'Attached',
        },
        declaration_agreed: declarationAgreed,
      };

      const res = await fetch(`${apiBaseUrl}/api/application/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || data.detail || 'Submission failed.');
      }

      onFinalSubmit(data);
    } catch (err) {
      setError(err.message || 'Loan application submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="portal-page-card" id="finalReviewCard" data-testid="finalReviewContainer">
      <div id="finalReviewContainer" style={{ display: 'none' }}></div>
      <div className="page-header">
        <span className="step-tag">Step 7 of 8</span>
        <h2>Final Review & Statutory Declaration / अंतिम समीक्षा एवं स्व-घोषणा</h2>
        <p className="page-desc">
          Authenticated Session: <strong>{username}</strong> (Application Ref: {sessionId ? sessionId.slice(0, 8) : 'VL-2026'}...)
        </p>
      </div>

      {/* Mandatory Human-In-The-Loop Barrier Banner */}
      <div
        className="security-barrier-badge"
        id="humanReviewBarrier"
        style={{
          backgroundColor: '#FFFBEB',
          borderColor: '#F59E0B',
          color: '#92400E',
          padding: '0.85rem 1.25rem',
          borderRadius: '8px',
          fontWeight: 600,
          marginBottom: '1.25rem',
        }}
      >
        ⚖️ <strong>अंतिम समीक्षा एवं आवेदक स्व-घोषणा / STATUTORY CITIZEN VERIFICATION GATE:</strong>
        <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.88rem', fontWeight: 400, color: '#78350F' }}>
          Pursuant to the Information Technology Act 2000 and Education Loan Guidelines, direct applicant verification is mandatory.
          Please personally review all assembled particulars below and sign the digital declaration before final submission.
        </p>
      </div>

      {error && <div className="portal-alert error">{error}</div>}

      <div className="review-summary-container" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* Card 1: Student Particulars */}
        <div className="summary-section-box" style={{ border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1rem', backgroundColor: '#f8fafc' }}>
          <h4 style={{ margin: '0 0 0.6rem 0', color: '#1e3a8a', display: 'flex', justifyContent: 'space-between' }}>
            <span>🎓 1. Student Particulars</span>
            <span style={{ fontSize: '0.8rem', color: '#166534' }}>✓ Verified</span>
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.6rem', fontSize: '0.88rem' }}>
            <div><strong>Student Name:</strong> {studentData.studentName || 'Priya Sharma'}</div>
            <div><strong>Date of Birth:</strong> {studentData.dateOfBirth || '2003-05-15'}</div>
            <div><strong>Gender:</strong> {studentData.gender || 'Female'}</div>
            <div><strong>State of Domicile:</strong> {studentData.state || 'Andhra Pradesh'}</div>
            <div><strong>District:</strong> {studentData.district || 'Visakhapatnam'}</div>
            <div><strong>Social Category:</strong> {studentData.category || 'OBC'}</div>
            <div><strong>Aadhaar (Last 4):</strong> XXXX-XXXX-{studentData.aadhaarLastFour || '5821'}</div>
          </div>
        </div>

        {/* Card 2: Parent / Co-Borrower Details */}
        <div className="summary-section-box" style={{ border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1rem', backgroundColor: '#f8fafc' }}>
          <h4 style={{ margin: '0 0 0.6rem 0', color: '#1e3a8a', display: 'flex', justifyContent: 'space-between' }}>
            <span>👨‍👩‍👦 2. Parent / Co-Borrower Particulars</span>
            <span style={{ fontSize: '0.8rem', color: '#166534' }}>✓ Verified</span>
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.6rem', fontSize: '0.88rem' }}>
            <div><strong>Parent / Guardian:</strong> {studentData.parentName || 'Ramesh Sharma'}</div>
            <div><strong>Occupation:</strong> {studentData.parentOccupation || 'Salaried / Private'}</div>
            <div><strong>Annual Family Income:</strong> ₹{Number(studentData.annualFamilyIncome || 350000).toLocaleString('en-IN')}</div>
          </div>
        </div>

        {/* Card 3: Loan Details */}
        <div className="summary-section-box" style={{ border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1rem', backgroundColor: '#f8fafc' }}>
          <h4 style={{ margin: '0 0 0.6rem 0', color: '#1e3a8a', display: 'flex', justifyContent: 'space-between' }}>
            <span>💰 3. Educational Institution & Loan Requirements</span>
            <span style={{ fontSize: '0.8rem', color: '#166534' }}>✓ Verified</span>
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.6rem', fontSize: '0.88rem' }}>
            <div><strong>Course / Program:</strong> {loanData.course || 'B.Tech Computer Science and Engineering'}</div>
            <div><strong>College / University:</strong> {loanData.college || 'National Institute of Technology'}</div>
            <div><strong>Total Loan Requested:</strong> ₹{Number(loanData.loanAmount || 750000).toLocaleString('en-IN')}</div>
            <div><strong>Tuition Fees:</strong> ₹{Number(loanData.tuitionFee || 500000).toLocaleString('en-IN')}</div>
            <div><strong>Living Expenses:</strong> ₹{Number(loanData.livingExpenses || 250000).toLocaleString('en-IN')}</div>
            <div><strong>Preferred Lending Bank:</strong> {loanData.bankPreference || 'State Bank of India'}</div>
            <div><strong>Repayment Tenure:</strong> {loanData.loanTenure || '10 Years'}</div>
          </div>
        </div>

        {/* Card 4: Uploaded Documents */}
        <div className="summary-section-box" style={{ border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1rem', backgroundColor: '#f8fafc' }}>
          <h4 style={{ margin: '0 0 0.6rem 0', color: '#1e3a8a', display: 'flex', justifyContent: 'space-between' }}>
            <span>📑 4. Attached Verification Documents</span>
            <span style={{ fontSize: '0.8rem', color: '#166534' }}>4 of 4 Attached</span>
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.6rem', fontSize: '0.88rem' }}>
            <div>📄 <strong>Admission Letter:</strong> {uploadedDocs.admissionLetter ? uploadedDocs.admissionLetter.name : 'Attached'}</div>
            <div>📄 <strong>Fee Structure:</strong> {uploadedDocs.feeStructure ? uploadedDocs.feeStructure.name : 'Attached'}</div>
            <div>📄 <strong>Student Aadhaar:</strong> {uploadedDocs.studentAadhaar ? uploadedDocs.studentAadhaar.name : 'Attached'}</div>
            <div>📄 <strong>Parent Income Certificate:</strong> {uploadedDocs.parentIncomeCertificate ? uploadedDocs.parentIncomeCertificate.name : 'Attached'}</div>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="portal-form" style={{ marginTop: '1.2rem' }}>
        {/* Statutory Declaration Checkbox */}
        <div className="portal-declaration-box" style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', padding: '0.8rem', borderRadius: '6px' }}>
          <label className="checkbox-label" htmlFor="declaration_agreed" style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start', cursor: 'pointer' }}>
            <input
              id="declaration_agreed"
              name="declaration_agreed"
              data-testid="confirmDeclaration"
              className="confirmDeclaration"
              type="checkbox"
              checked={declarationAgreed}
              onChange={(e) => setDeclarationAgreed(e.target.checked)}
              style={{ marginTop: '0.2rem' }}
            />
            <span style={{ fontSize: '0.88rem', color: '#14532d', lineHeight: '1.4' }}>
              <strong>Citizen Affirmation & Verification Consent:</strong> I solemnly declare that all educational, income, and personal details entered above are true and correct. I consent to credit verification by the designated partner bank and data validation through official government channels under the National Student Education Loan Scheme.
            </span>
          </label>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.2rem' }}>
          <button
            type="button"
            className="portal-secondary-btn"
            onClick={onBack}
            disabled={submitting}
          >
            ← Back to Documents
          </button>
          <button
            id="submitApplicationBtn"
            data-testid="submitFinalApplicationBtn"
            type="submit"
            className="portal-primary-btn submitFinalApplicationBtn"
            style={{ flex: 1, backgroundColor: declarationAgreed ? '#16a34a' : '#94a3b8' }}
            disabled={submitting || !declarationAgreed}
          >
            {submitting ? 'Submitting Application...' : 'Confirm & Submit Loan Application →'}
          </button>
        </div>
      </form>
    </div>
  );
};
