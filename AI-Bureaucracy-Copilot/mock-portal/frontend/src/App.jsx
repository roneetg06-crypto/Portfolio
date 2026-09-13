import React, { useEffect, useState } from 'react';
import { LoginPage } from './pages/LoginPage.jsx';
import { CaptchaPage } from './pages/CaptchaPage.jsx';
import { OtpPage } from './pages/OtpPage.jsx';
import { StudentParentInfoPage } from './pages/StudentParentInfoPage.jsx';
import { LoanDetailsPage } from './pages/LoanDetailsPage.jsx';
import { DocumentUploadPage } from './pages/DocumentUploadPage.jsx';
import { FinalReviewPage } from './pages/FinalReviewPage.jsx';
import { ConfirmationPage } from './pages/ConfirmationPage.jsx';

const API_BASE_URL =
  typeof window !== 'undefined' && window.location.hostname
    ? `http://${window.location.hostname}:8001`
    : 'http://localhost:8001';

export const App = () => {
  // 8-step workflow
  const [currentStep, setCurrentStep] = useState('LOGIN');
  const [sessionId, setSessionId] = useState(null);
  const [username, setUsername] = useState('');
  const [submissionData, setSubmissionData] = useState(null);

  // Application Data Stores
  const [studentData, setStudentData] = useState({
    studentName: 'Priya Sharma',
    dateOfBirth: '2003-05-15',
    gender: 'Female',
    state: 'Andhra Pradesh',
    district: 'Visakhapatnam',
    category: 'OBC',
    parentName: 'Ramesh Sharma',
    parentOccupation: 'Salaried / Private',
    annualFamilyIncome: 350000,
    aadhaarLastFour: '5821',
  });

  const [loanData, setLoanData] = useState({
    course: 'B.Tech Computer Science and Engineering',
    college: 'National Institute of Technology',
    loanAmount: 750000,
    tuitionFee: 500000,
    livingExpenses: 250000,
    bankPreference: 'State Bank of India',
    loanTenure: '10 Years',
  });

  const [uploadedDocs, setUploadedDocs] = useState({
    admissionLetter: null,
    feeStructure: null,
    studentAadhaar: null,
    parentIncomeCertificate: null,
  });

  // Read query params linking to Copilot run
  const queryParams =
    typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search)
      : new URLSearchParams();
  const runId = queryParams.get('run_id') || null;
  const schemeId = queryParams.get('scheme_id') || 'SCH-EDU-001';

  const notifyMilestone = async (milestone, stepData) => {
    if (!sessionId) return;
    try {
      await fetch(`${API_BASE_URL}/api/application/milestone`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          run_id: runId,
          milestone: milestone,
          data: stepData || {},
        }),
      });
    } catch (err) {
      console.warn(`Could not report milestone ${milestone}:`, err);
    }
  };

  // Step Navigations
  const handleLoginSuccess = (sid, uname) => {
    setSessionId(sid);
    setUsername(uname);
    setCurrentStep('CAPTCHA');
  };

  const handleCaptchaSuccess = () => {
    setCurrentStep('OTP');
  };

  const handleOtpSuccess = () => {
    notifyMilestone('OTP_COMPLETED');
    setCurrentStep('STUDENT_PARENT_INFO');
  };

  const handleStudentParentNext = (data) => {
    setStudentData(data);
    notifyMilestone('STUDENT_INFO_COMPLETED', data);
    setCurrentStep('LOAN_INFO');
  };

  const handleLoanInfoNext = (data) => {
    setLoanData(data);
    notifyMilestone('LOAN_INFO_COMPLETED', data);
    setCurrentStep('DOC_UPLOAD');
  };

  const handleDocUploadNext = (data) => {
    setUploadedDocs(data);
    notifyMilestone('DOCUMENTS_UPLOADED', data);
    notifyMilestone('FINAL_REVIEW_REQUIRED');
    setCurrentStep('FINAL_REVIEW');
  };

  const handleFinalSubmitSuccess = (data) => {
    setSubmissionData(data);
    setCurrentStep('CONFIRMATION');
  };

  const handleReset = () => {
    setSessionId(null);
    setUsername('');
    setSubmissionData(null);
    setCurrentStep('LOGIN');
  };

  const stepsList = [
    { key: 'LOGIN', label: '1. Applicant Login' },
    { key: 'CAPTCHA', label: '2. Security CAPTCHA' },
    { key: 'OTP', label: '3. Aadhaar 2FA OTP' },
    { key: 'STUDENT_PARENT_INFO', label: '4. Student & Guardian' },
    { key: 'LOAN_INFO', label: '5. Academic & Loan' },
    { key: 'DOC_UPLOAD', label: '6. Supporting Documents' },
    { key: 'FINAL_REVIEW', label: '7. Final Declaration' },
    { key: 'CONFIRMATION', label: '8. Acknowledgment' },
  ];

  return (
    <div className="portal-container">
      {/* Top Official Government Utility Bar */}
      <div className="gov-utility-bar">
        <div className="gov-utility-left">
          <span>भारत सरकार | Government of India</span>
          <span>शिक्षा मंत्रालय | Ministry of Education</span>
        </div>
        <div className="gov-utility-right">
          <a href="#main-content">मुख्य सामग्री पर जाएं (Skip to Main Content)</a>
          <span>|</span>
          <span title="Screen Reader Access">स्क्रीन रीडर (Screen Reader)</span>
          <span>|</span>
          <span>A- A A+</span>
          <span>|</span>
          <span style={{ fontWeight: 700, color: '#FEF3C7' }}>हिन्दी / English</span>
        </div>
      </div>

      {/* Main Government Portal Header */}
      <header className="portal-header">
        <div className="header-brand">
          <div className="emblem-badge-wrapper" title="Ministry of Education National Portal Emblem">
            {/* Government Education Seal SVG motif */}
            <svg width="42" height="42" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="50" cy="50" r="46" stroke="#7A1C1C" strokeWidth="4" fill="#FFFDF8"/>
              <circle cx="50" cy="50" r="38" stroke="#D97706" strokeWidth="2" strokeDasharray="4 2"/>
              {/* Central open book & torch emblem */}
              <path d="M30 62 C40 58 50 62 50 62 C50 62 60 58 70 62 L70 42 C60 38 50 42 50 42 C50 42 40 38 30 42 Z" fill="#7A1C1C" stroke="#7A1C1C" strokeWidth="2"/>
              <path d="M50 42 L50 62" stroke="#FFFDF8" strokeWidth="2"/>
              <circle cx="50" cy="30" r="5" fill="#D97706"/>
              <path d="M47 30 L53 30 L51 22 L49 22 Z" fill="#B45309"/>
              <path d="M26 68 Q50 78 74 68" stroke="#D97706" strokeWidth="3" strokeLinecap="round" fill="none"/>
            </svg>
          </div>
          <div>
            <h1>विद्या लक्ष्मी | Vidya Lakshmi</h1>
            <p className="portal-tagline">
              राष्ट्रीय छात्र शिक्षा ऋण एवं छात्रवृत्ति पोर्टल | National Student Financial Aid & Education Loan Portal
            </p>
          </div>
        </div>

        {/* Right Section: User Badge */}
        {username && (
          <div className="user-badge">
            <span>
              👤 प्रमाणित आवेदक / Applicant: <strong>{username}</strong>
            </span>
            <button className="portal-text-btn" onClick={handleReset}>
              Sign Out / लॉग आउट ⎋
            </button>
          </div>
        )}
      </header>

      {/* National Single Window System Integrated Gateway Banner */}
      {runId && (
        <div className="portal-copilot-link-banner">
          <span>
            🏛️ <strong>National Single Window System (NSWS) Integrated Digital Services Gateway</strong>
          </span>
          <span>
            Scheme Code: <strong>{schemeId || 'SCH-EDU-001'}</strong>
          </span>
          <span>
            Transaction Reference: <code>{runId.slice(0, 8)}...</code>
          </span>
        </div>
      )}

      {/* Sequential Progress Bar (8 Steps) */}
      <nav className="portal-stepper" aria-label="Application Progress Tracker">
        {stepsList.map((st, index) => {
          const isDone = stepsList.findIndex((s) => s.key === currentStep) > index;
          const isCurrent = st.key === currentStep;

          let stepClass = 'stepper-step';
          if (isDone) stepClass += ' done';
          if (isCurrent) stepClass += ' active';

          return (
            <div key={st.key} className={stepClass}>
              <span className="step-circle">{isDone ? '✓' : index + 1}</span>
              <span className="step-label">{st.label}</span>
            </div>
          );
        })}
      </nav>

      {/* Main Page Routing */}
      <main className="portal-main-content" id="main-content">
        {/* Step 1: Login (Human) */}
        {currentStep === 'LOGIN' && (
          <LoginPage onLoginSuccess={handleLoginSuccess} apiBaseUrl={API_BASE_URL} runId={runId} />
        )}

        {/* Step 2: CAPTCHA (Human) */}
        {currentStep === 'CAPTCHA' && sessionId && (
          <CaptchaPage
            sessionId={sessionId}
            onCaptchaSuccess={handleCaptchaSuccess}
            apiBaseUrl={API_BASE_URL}
          />
        )}

        {/* Step 3: Mobile OTP (Human) */}
        {currentStep === 'OTP' && sessionId && (
          <OtpPage
            sessionId={sessionId}
            onOtpSuccess={handleOtpSuccess}
            apiBaseUrl={API_BASE_URL}
          />
        )}

        {/* Step 4: Student & Parent Information (Automated) */}
        {currentStep === 'STUDENT_PARENT_INFO' && (
          <StudentParentInfoPage
            studentData={studentData}
            onSaveAndNext={handleStudentParentNext}
            username={username}
            sessionId={sessionId}
          />
        )}

        {/* Step 5: Loan Information (Automated) */}
        {currentStep === 'LOAN_INFO' && (
          <LoanDetailsPage
            loanData={loanData}
            onSaveAndNext={handleLoanInfoNext}
            onBack={() => setCurrentStep('STUDENT_PARENT_INFO')}
            username={username}
            sessionId={sessionId}
          />
        )}

        {/* Step 6: Document Upload (Automated) */}
        {currentStep === 'DOC_UPLOAD' && (
          <DocumentUploadPage
            uploadedDocs={uploadedDocs}
            onSaveAndNext={handleDocUploadNext}
            onBack={() => setCurrentStep('LOAN_INFO')}
            username={username}
            sessionId={sessionId}
          />
        )}

        {/* Step 7: Final Review & Human Sign-off (Human) */}
        {currentStep === 'FINAL_REVIEW' && (
          <FinalReviewPage
            studentData={studentData}
            loanData={loanData}
            uploadedDocs={uploadedDocs}
            sessionId={sessionId}
            username={username}
            runId={runId}
            schemeId={schemeId}
            onFinalSubmit={handleFinalSubmitSuccess}
            onBack={() => setCurrentStep('DOC_UPLOAD')}
            apiBaseUrl={API_BASE_URL}
          />
        )}

        {/* Step 8: Submission Confirmation (Receipt) */}
        {currentStep === 'CONFIRMATION' && submissionData && (
          <ConfirmationPage
            submissionData={submissionData}
            runId={runId}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Multi-Column Official Government Footer */}
      <footer className="gov-portal-footer" role="contentinfo">
        <div className="gov-footer-container">
          <div className="gov-footer-grid">
            <div className="gov-footer-col">
              <h3>About Vidya Lakshmi / पोर्टल का परिचय</h3>
              <p>
                Vidya Lakshmi is a single window electronic platform for students seeking Education Loans,
                developed under the guidance of Department of Financial Services (Ministry of Finance),
                Department of Higher Education (Ministry of Education), and Indian Banks' Association (IBA).
              </p>
              <p>
                The portal connects student applicants directly with public and private scheduled commercial
                banks across India for hassle-free educational credit sanction.
              </p>
            </div>

            <div className="gov-footer-col">
              <h3>National Portals / राष्ट्रीय लिंक</h3>
              <ul className="gov-footer-links-list">
                <li>
                  <a href="https://scholarships.gov.in" target="_blank" rel="noopener noreferrer">
                    🏛️ National Scholarship Portal (NSP) ↗
                  </a>
                </li>
                <li>
                  <a href="https://www.digilocker.gov.in" target="_blank" rel="noopener noreferrer">
                    📁 DigiLocker National Depository ↗
                  </a>
                </li>
                <li>
                  <a href="https://pgportal.gov.in" target="_blank" rel="noopener noreferrer">
                    ⚖️ CPGRAMS Public Grievance Portal ↗
                  </a>
                </li>
                <li>
                  <a href="https://www.iba.org.in" target="_blank" rel="noopener noreferrer">
                    🏦 Indian Banks' Association (IBA) ↗
                  </a>
                </li>
              </ul>
            </div>

            <div className="gov-footer-col">
              <h3>Citizen Helpdesk & Grievance / सहायता</h3>
              <div className="gov-helpline-box">
                <div className="help-item">
                  <span>📞</span>
                  <div>
                    <strong>National Toll-Free Helpline:</strong><br />
                    1800-180-1111 / 1800-599-0019
                  </div>
                </div>
                <div className="help-item">
                  <span>✉️</span>
                  <div>
                    <strong>Helpdesk Inquiries:</strong><br />
                    support-vidyalakshmi@gov.in
                  </div>
                </div>
                <div className="help-item">
                  <span>🕒</span>
                  <div>
                    <strong>Helpdesk Working Hours:</strong><br />
                    Monday – Saturday: 09:30 AM – 06:00 PM IST
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="gov-footer-legal-bar">
            <div>
              Website Policies | Hyperlink Policy | Terms & Conditions | Privacy Policy
            </div>
            <div className="nic-stamp">
              <span>Designed, Developed & Hosted by <strong>National Informatics Centre (NIC)</strong></span>
            </div>
            <div>
              Copyright © 2026 Ministry of Education, Government of India. All Rights Reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
