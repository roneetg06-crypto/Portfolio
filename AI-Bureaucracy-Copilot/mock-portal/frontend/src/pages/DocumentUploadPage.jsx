import React, { useState } from 'react';

export const DocumentUploadPage = ({
  uploadedDocs,
  onSaveAndNext,
  onBack,
  username,
  sessionId,
}) => {
  const [docs, setDocs] = useState({
    admissionLetter: uploadedDocs.admissionLetter || null,
    feeStructure: uploadedDocs.feeStructure || null,
    studentAadhaar: uploadedDocs.studentAadhaar || null,
    parentIncomeCertificate: uploadedDocs.parentIncomeCertificate || null,
  });

  const [error, setError] = useState(null);

  const handleFileChange = (field, e) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      setDocs((prev) => ({
        ...prev,
        [field]: {
          name: file.name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
          uploadedAt: new Date().toISOString(),
        },
      }));
    }
  };

  const handleSimulateAllAttachments = () => {
    setDocs({
      admissionLetter: { name: 'NIT_Admission_Offer_Letter.pdf', size: 245000, uploadedAt: new Date().toISOString() },
      feeStructure: { name: 'Academic_Fee_Structure_2026.pdf', size: 180000, uploadedAt: new Date().toISOString() },
      studentAadhaar: { name: 'Student_Aadhaar_Card.pdf', size: 310000, uploadedAt: new Date().toISOString() },
      parentIncomeCertificate: { name: 'Revenue_Income_Certificate.pdf', size: 195000, uploadedAt: new Date().toISOString() },
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Validate that all 4 documents are selected or attached
    if (!docs.admissionLetter) {
      setError('Please upload or attach the Admission Letter.');
      return;
    }
    if (!docs.feeStructure) {
      setError('Please upload or attach the Fee Structure document.');
      return;
    }
    if (!docs.studentAadhaar) {
      setError('Please upload or attach the Student Aadhaar Card.');
      return;
    }
    if (!docs.parentIncomeCertificate) {
      setError('Please upload or attach the Parent Income Certificate.');
      return;
    }

    setError(null);
    onSaveAndNext(docs);
  };

  return (
    <div className="portal-page-card">
      <div className="page-header">
        <span className="step-tag">Step 6 of 8</span>
        <h2>Mandatory Supporting Documents / अनिवार्य दस्तावेज अपलोड</h2>
        <p className="page-desc">
          Upload verified academic, personal identification, and income records in PDF or JPG format (Max 2MB).
        </p>
      </div>

      <div className="gov-section-header">
        <span>📁 भाग 3: अनिवार्य दस्तावेज संलग्नक / Section 3: Mandatory Enclosures (National Academic Depository - NAD Integrated)</span>
      </div>

      {error && <div className="portal-alert error">{error}</div>}

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.8rem' }}>
        <button
          type="button"
          onClick={handleSimulateAllAttachments}
          className="portal-secondary-btn"
          style={{ fontSize: '0.84rem', fontWeight: 600 }}
          title="Auto-fetch verified certificates from National Depository"
        >
          ⚡ Auto-Attach Verified Records from DigiLocker / NAD
        </button>
      </div>

      <form onSubmit={handleSubmit} className="portal-form" id="documentUploadForm">
        {/* Document 1: Admission Letter */}
        <div className="portal-form-group" style={{ padding: '0.8rem', border: '1px solid #e2e8f0', borderRadius: '6px', marginBottom: '0.8rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label htmlFor="admissionLetter" style={{ fontWeight: 600, margin: 0 }}>
              1. Admission Letter <span style={{ color: '#dc2626' }}>*</span>
            </label>
            {docs.admissionLetter && (
              <span style={{ fontSize: '0.8rem', color: '#166534', backgroundColor: '#dcfce7', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                ✓ {docs.admissionLetter.name || 'Attached'}
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0.2rem 0 0.5rem 0' }}>
            Official college/university admission offer letter stating program enrollment.
          </p>
          <input
            id="admissionLetter"
            name="admissionLetter"
            data-testid="admissionLetter"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => handleFileChange('admissionLetter', e)}
          />
        </div>

        {/* Document 2: Fee Structure */}
        <div className="portal-form-group" style={{ padding: '0.8rem', border: '1px solid #e2e8f0', borderRadius: '6px', marginBottom: '0.8rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label htmlFor="feeStructure" style={{ fontWeight: 600, margin: 0 }}>
              2. Fee Structure <span style={{ color: '#dc2626' }}>*</span>
            </label>
            {docs.feeStructure && (
              <span style={{ fontSize: '0.8rem', color: '#166534', backgroundColor: '#dcfce7', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                ✓ {docs.feeStructure.name || 'Attached'}
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0.2rem 0 0.5rem 0' }}>
            Detailed institutional breakdown of tuition, examination, and hostel fees.
          </p>
          <input
            id="feeStructure"
            name="feeStructure"
            data-testid="feeStructure"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => handleFileChange('feeStructure', e)}
          />
        </div>

        {/* Document 3: Student Aadhaar */}
        <div className="portal-form-group" style={{ padding: '0.8rem', border: '1px solid #e2e8f0', borderRadius: '6px', marginBottom: '0.8rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label htmlFor="studentAadhaar" style={{ fontWeight: 600, margin: 0 }}>
              3. Student Aadhaar <span style={{ color: '#dc2626' }}>*</span>
            </label>
            {docs.studentAadhaar && (
              <span style={{ fontSize: '0.8rem', color: '#166534', backgroundColor: '#dcfce7', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                ✓ {docs.studentAadhaar.name || 'Attached'}
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0.2rem 0 0.5rem 0' }}>
            Clear front and back copy of the student's Aadhaar identification card.
          </p>
          <input
            id="studentAadhaar"
            name="studentAadhaar"
            data-testid="studentAadhaar"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => handleFileChange('studentAadhaar', e)}
          />
        </div>

        {/* Document 4: Parent Income Certificate */}
        <div className="portal-form-group" style={{ padding: '0.8rem', border: '1px solid #e2e8f0', borderRadius: '6px', marginBottom: '0.8rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label htmlFor="parentIncomeCertificate" style={{ fontWeight: 600, margin: 0 }}>
              4. Parent Income Certificate <span style={{ color: '#dc2626' }}>*</span>
            </label>
            {docs.parentIncomeCertificate && (
              <span style={{ fontSize: '0.8rem', color: '#166534', backgroundColor: '#dcfce7', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                ✓ {docs.parentIncomeCertificate.name || 'Attached'}
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0.2rem 0 0.5rem 0' }}>
            Government income certificate or employer salary certificate for interest subsidy eligibility.
          </p>
          <input
            id="parentIncomeCertificate"
            name="parentIncomeCertificate"
            data-testid="parentIncomeCertificate"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => handleFileChange('parentIncomeCertificate', e)}
          />
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.2rem' }}>
          <button
            type="button"
            className="portal-secondary-btn"
            onClick={onBack}
          >
            ← Back to Loan Details
          </button>
          <button
            id="nextToReviewBtn"
            type="submit"
            className="portal-primary-btn"
            style={{ flex: 1 }}
          >
            Save & Proceed to Final Review →
          </button>
        </div>
      </form>
    </div>
  );
};
