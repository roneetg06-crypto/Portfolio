import React, { useEffect, useState } from 'react';
import {
  DocumentStatusItem,
  getDocumentsStatus,
  getInformationRequirements,
  RequiredInfoField,
  Scheme,
  submitInformation,
} from '../api/client';
import { DocumentUploadSection } from './DocumentUploadSection';
import { DynamicForm } from './DynamicForm';
import { WorkflowStatusIndicator } from './WorkflowStatusIndicator';
import { AutomationProgressPanel } from './AutomationProgressPanel';
import { AutomationStatusResponse } from '../api/client';

import { CitizenProfileResponse } from '../api/client';

interface SchemeApplicationModalProps {
  scheme: Scheme;
  profileId?: string;
  profile?: CitizenProfileResponse;
  onClose: () => void;
}

export const SchemeApplicationModal: React.FC<SchemeApplicationModalProps> = ({
  scheme,
  profileId,
  profile,
  onClose,
}) => {
  const [loading, setLoading] = useState(true);
  const [submittingInfo, setSubmittingInfo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [requiredFields, setRequiredFields] = useState<RequiredInfoField[]>([]);
  const [infoSubmitted, setInfoSubmitted] = useState(false);
  const [documents, setDocuments] = useState<DocumentStatusItem[]>([]);
  const [activeStep, setActiveStep] = useState<'info' | 'documents' | 'automation'>('info');
  const [automationState, setAutomationState] = useState<AutomationStatusResponse | null>(null);

  const loadSchemeData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch info requirements
      const infoRes = await getInformationRequirements(scheme.scheme_id);
      setRequiredFields(infoRes.required_info || []);

      // If no info required, jump straight to infoSubmitted = true & documents step
      if (!infoRes.required_info || infoRes.required_info.length === 0) {
        setInfoSubmitted(true);
        setActiveStep('documents');
      }

      // 2. Fetch document statuses
      const docRes = await getDocumentsStatus(scheme.scheme_id, profileId);
      setDocuments(docRes.documents || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load application requirements.');
    } finally {
      setLoading(false);
    }
  };

  // Lock background scrolling while modal is open
  useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  useEffect(() => {
    loadSchemeData();
  }, [scheme.scheme_id, profileId]);

  const handleInfoSubmit = async (values: Record<string, any>) => {
    setSubmittingInfo(true);
    setError(null);
    try {
      await submitInformation(scheme.scheme_id, {
        profile_id: profileId,
        data: values,
      });
      setInfoSubmitted(true);
      setActiveStep('documents');
      // Refresh documents status after info submission (Document Agent may update required docs)
      const docRes = await getDocumentsStatus(scheme.scheme_id, profileId);
      setDocuments(docRes.documents || []);
    } catch (err: any) {
      setError(err.message || 'Failed to save information.');
    } finally {
      setSubmittingInfo(false);
    }
  };

  const handleRefreshDocuments = async () => {
    try {
      const docRes = await getDocumentsStatus(scheme.scheme_id, profileId);
      setDocuments(docRes.documents || []);
    } catch (err: any) {
      console.error('Failed to refresh document status:', err);
    }
  };

  const hasMissingDocs = documents.some((d) => d.status === 'MISSING' && d.required);
  const documentsVerified =
    documents.length > 0 &&
    documents.every((d) => d.status === 'VERIFIED' || d.status === 'MANUAL_VERIFICATION_REQUIRED');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="modal-badge">{scheme.level.toUpperCase()} SCHEME</span>
            <h2>Apply / Requirements for {scheme.name}</h2>
            <p className="issuing-auth">Issued by: {scheme.issuing_authority}</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {/* Workflow Status Indicator */}
          <WorkflowStatusIndicator
            currentStep={activeStep}
            infoSubmitted={infoSubmitted}
            documentsVerified={documentsVerified}
            hasMissingDocs={hasMissingDocs}
            automationStatus={automationState?.automation_status}
          />

          {loading && (
            <div className="state-box loading" style={{ margin: '2rem 0' }}>
              <span className="spinner"></span>
              <p>Fetching scheme requirements & document checklist...</p>
            </div>
          )}

          {!loading && error && (
            <div className="form-alert error-alert" style={{ margin: '1rem 0' }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {!loading && (
            <>
              {/* Step Navigation Tabs */}
              <div className="step-tabs">
                {requiredFields.length > 0 && (
                  <button
                    className={`step-tab ${activeStep === 'info' ? 'active' : ''}`}
                    onClick={() => setActiveStep('info')}
                  >
                    1. Additional Information {infoSubmitted && '✓'}
                  </button>
                )}
                <button
                  className={`step-tab ${activeStep === 'documents' ? 'active' : ''}`}
                  onClick={() => setActiveStep('documents')}
                  disabled={!infoSubmitted && requiredFields.length > 0}
                >
                  2. Document Verification {!hasMissingDocs && documents.length > 0 && '✓'}
                </button>
                <button
                  className={`step-tab ${activeStep === 'automation' ? 'active' : ''}`}
                  onClick={() => setActiveStep('automation')}
                >
                  3. Application Automation {automationState?.automation_status === 'COMPLETED' ? '✓' : ''}
                </button>
              </div>

              {/* Step 1: Dynamic Form */}
              {activeStep === 'info' && requiredFields.length > 0 && (
                <div className="step-content">
                  <div className="step-intro">
                    <h3>Step 1: Required Information</h3>
                    <p>
                      Please complete the scheme-specific required fields below to proceed with your application.
                    </p>
                    {scheme.scheme_id === 'SCH-EDU-001' && (
                      <div style={{
                        marginTop: '0.8rem',
                        padding: '0.8rem 1rem',
                        background: '#f0fdf4',
                        border: '1px solid #86efac',
                        borderRadius: '6px',
                        fontSize: '0.88rem',
                        color: '#166534',
                      }}>
                        <strong>📋 Mandatory Eligibility Criteria:</strong>
                        <ul style={{ margin: '0.3rem 0 0 1.2rem', padding: 0 }}>
                          <li><strong>Nationality:</strong> Indian Citizen (All Indian States & UTs)</li>
                          <li><strong>Age Requirement:</strong> 16 to 35 years at application time</li>
                          <li><strong>Admission:</strong> Confirmed seat in recognized higher education (B.Tech, MBBS, MBA, etc.)</li>
                          <li><strong>Family Income:</strong> Up to ₹8,00,000 for credit guarantee / full interest subsidy</li>
                        </ul>
                      </div>
                    )}
                  </div>
                  <DynamicForm
                    fields={requiredFields}
                    profile={profile}
                    onSubmit={handleInfoSubmit}
                    isLoading={submittingInfo}
                    serverError={error}
                  />
                </div>
              )}

              {/* Step 2: Document Verification Section */}
              {activeStep === 'documents' && (
                <div className="step-content">
                  <DocumentUploadSection
                    schemeId={scheme.scheme_id}
                    profileId={profileId}
                    profile={profile}
                    documents={documents}
                    onUploadSuccess={handleRefreshDocuments}
                  />
                  <div style={{ marginTop: '1.5rem', textAlign: 'right' }}>
                    <button
                      className="primary-action-btn"
                      onClick={() => setActiveStep('automation')}
                    >
                      Proceed to Application Automation →
                    </button>
                  </div>
                </div>
              )}

              {/* Step 3: Application Automation Section */}
              {activeStep === 'automation' && (
                <div className="step-content">
                  <AutomationProgressPanel
                    schemeId={scheme.scheme_id}
                    profileId={profileId}
                    onStatusChange={(status) => setAutomationState(status)}
                  />
                </div>
              )}
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="secondary-btn" onClick={onClose}>
            Close Window
          </button>
        </div>
      </div>
    </div>
  );
};
