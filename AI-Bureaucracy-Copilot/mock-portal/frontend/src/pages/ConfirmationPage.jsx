import React from 'react';

export const ConfirmationPage = ({ submissionData, runId, onReset }) => {
  return (
    <div className="portal-page-card confirmation-card">
      <div className="confirmation-header">
        <span className="success-check-icon">✓</span>
        <span className="step-tag">Step 8 of 8</span>
        <h2>Education Loan Application Submitted Successfully / आवेदन सफलतापूर्वक जमा हुआ</h2>
        <p className="page-desc">
          Your application has been received and registered under the National Student Financial Aid & Education Loan Framework (Vidya Lakshmi Central Gateway).
        </p>
      </div>

      <div className="ack-receipt-box">
        <div className="ack-row">
          <span className="ack-label">Official Application Reference / पावती संख्या:</span>
          <span className="ack-value highlight">{submissionData.acknowledgment_number}</span>
        </div>
        <div className="ack-row">
          <span className="ack-label">Applicant / Student Name:</span>
          <span className="ack-value">{submissionData.student_name || submissionData.applicant_name}</span>
        </div>
        <div className="ack-row">
          <span className="ack-label">Ministry Scheme Code:</span>
          <span className="ack-value">{submissionData.scheme_id || 'SCH-EDU-001'}</span>
        </div>
        {runId && (
          <div className="ack-row">
            <span className="ack-label">NSWS Digital Transaction Reference:</span>
            <span className="ack-value code-font">{runId}</span>
          </div>
        )}
        <div className="ack-row">
          <span className="ack-label">Submission Timestamp:</span>
          <span className="ack-value">{submissionData.submitted_at}</span>
        </div>
        <div className="ack-row">
          <span className="ack-label">Central Registry Session Ref:</span>
          <span className="ack-value code-font">{submissionData.session_id}</span>
        </div>
      </div>

      <div className="portal-notice-box">
        <strong>🏛️ Central Ministry & Bank Notification / केंद्रीय सूचना:</strong>
        <p>
          Your educational loan dossier and acknowledgment reference (<strong>{submissionData.acknowledgment_number}</strong>)
          have been dispatched to the designated sanctioning bank and automatically synchronized with the Citizen Portal.
          Status is now recorded as <strong>SANCTION UNDERWAY</strong>.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        <a
          href="http://localhost:5173"
          className="portal-primary-btn"
          style={{ textDecoration: 'none', display: 'inline-block' }}
        >
          Return to Citizen Portal (Port 5173) ➔
        </a>
        <button type="button" className="portal-secondary-btn" onClick={onReset}>
          Submit Another Application / नया आवेदन
        </button>
      </div>
    </div>
  );
};
