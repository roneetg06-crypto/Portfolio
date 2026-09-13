import React, { useState } from 'react';
import { CitizenProfileResponse, DocumentStatusItem, uploadDocument } from '../api/client';

interface DocumentUploadSectionProps {
  schemeId: string;
  profileId?: string;
  profile?: CitizenProfileResponse;
  documents: DocumentStatusItem[];
  onUploadSuccess: () => void;
}

export const DocumentUploadSection: React.FC<DocumentUploadSectionProps> = ({
  schemeId,
  profileId,
  profile,
  documents,
  onUploadSuccess,
}) => {
  const [uploadingDocName, setUploadingDocName] = useState<string | null>(null);
  const [autoAttaching, setAutoAttaching] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleAutoAttachDemoDocs = async () => {
    setAutoAttaching(true);
    setUploadError(null);
    try {
      const studentName = profile?.name || 'Priya Sharma';
      for (const doc of documents) {
        // Generate valid mock PDF with candidate name for consistency check
        const dummyPdfHeader = `%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n% Student Name: ${studentName}\n% Document Type: ${doc.label}\n% Scheme: ${schemeId}`;
        const blob = new Blob([dummyPdfHeader], { type: 'application/pdf' });
        const file = new File([blob], `${doc.name}_verified.pdf`, { type: 'application/pdf' });
        await uploadDocument(file, doc.name, schemeId, profileId);
      }
      onUploadSuccess();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to auto-attach demo documents.');
    } finally {
      setAutoAttaching(false);
    }
  };

  const handleFileChange = async (
    docName: string,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];

    // File validation check (5MB limit, allowed extensions)
    const allowedExts = ['.pdf', '.png', '.jpg', '.jpeg'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExts.includes(ext)) {
      setUploadError(`Invalid file type '${ext}'. Please upload a PDF, PNG, or JPG file.`);
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setUploadError(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds 5 MB limit.`);
      return;
    }

    setUploadingDocName(docName);
    setUploadError(null);

    try {
      await uploadDocument(file, docName, schemeId, profileId);
      onUploadSuccess();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload document.');
    } finally {
      setUploadingDocName(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return <span className="status-badge badge-verified">✓ Verified (Extraction Match)</span>;
      case 'MANUAL_VERIFICATION_REQUIRED':
        return <span className="status-badge badge-manual">⏳ Manual Verification Required</span>;
      case 'INVALID':
      case 'UNCLEAR':
        return <span className="status-badge badge-invalid">✕ {status}</span>;
      case 'MISSING':
      default:
        return <span className="status-badge badge-missing">! Missing / Action Required</span>;
    }
  };

  return (
    <div className="document-upload-section">
      <div className="section-header">
        <h3>Required Verification Documents</h3>
        <p className="disclaimer-text">
          Upload required documents below. All files are checked locally for structural consistency.
          <strong> Disclaimer: Preliminary system check only; not official government verification.</strong>
        </p>
      </div>

      {/* 1-Click Auto-Attach Demo Documents */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.75rem 1rem',
        background: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: '6px',
        marginBottom: '1.25rem',
        gap: '0.6rem',
        flexWrap: 'wrap',
      }}>
        <div style={{ fontSize: '0.86rem', color: '#166534' }}>
          ⚡ <strong>1-Click Demo Attach:</strong> Auto-upload valid mock PDFs for all required documents to verify and advance immediately.
        </div>
        <button
          type="button"
          onClick={handleAutoAttachDemoDocs}
          disabled={autoAttaching}
          style={{
            background: '#16a34a',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            padding: '0.45rem 0.9rem',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: autoAttaching ? 'not-allowed' : 'pointer',
            opacity: autoAttaching ? 0.7 : 1,
            transition: 'background 0.2s ease',
          }}
          title="Creates and uploads verified sample PDFs for all required documents"
        >
          {autoAttaching ? '⏳ Attaching & Verifying...' : '⚡ Auto-Attach Demo Documents'}
        </button>
      </div>

      {uploadError && (
        <div className="form-alert error-alert" style={{ marginBottom: '1rem' }}>
          <strong>Upload Error:</strong> {uploadError}
        </div>
      )}

      <div className="documents-list">
        {documents.map((doc) => {
          const isUploading = uploadingDocName === doc.name;

          return (
            <div key={doc.name} className={`document-card doc-status-${doc.status.toLowerCase()}`}>
              <div className="doc-info">
                <div className="doc-title-row">
                  <h4>{doc.label} {doc.required && <span className="required">*</span>}</h4>
                  {getStatusBadge(doc.status)}
                </div>

                <p className="doc-verification-msg">{doc.verification_message}</p>

                {doc.original_filename && (
                  <div className="uploaded-meta">
                    <span>📄 {doc.original_filename}</span>
                    {doc.size_bytes && (
                      <span>({(doc.size_bytes / 1024).toFixed(1)} KB)</span>
                    )}
                  </div>
                )}
              </div>

              <div className="doc-action">
                <label className={`upload-btn ${isUploading ? 'disabled' : ''}`}>
                  {isUploading ? 'Uploading...' : doc.status === 'MISSING' ? 'Upload Document' : 'Re-upload File'}
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    disabled={isUploading}
                    onChange={(e) => handleFileChange(doc.name, e)}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
