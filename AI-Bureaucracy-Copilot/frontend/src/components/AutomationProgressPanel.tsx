import React, { useEffect, useState } from 'react';
import {
  AutomationStatusResponse,
  authFetch,
  getAutomationStatus,
  resumeAutomation,
  startAutomation,
} from '../api/client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface AutomationProgressPanelProps {
  schemeId: string;
  profileId?: string;
  onStatusChange?: (status: AutomationStatusResponse) => void;
}

export const AutomationProgressPanel: React.FC<AutomationProgressPanelProps> = ({
  schemeId,
  profileId = 'default',
  onStatusChange,
}) => {
  const [automationState, setAutomationState] = useState<AutomationStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if there is an existing automation run
  const checkExistingRun = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);
      const res = await getAutomationStatus({ scheme_id: schemeId, profile_id: profileId });
      setAutomationState(res);
      if (onStatusChange) onStatusChange(res);
    } catch {
      // No existing run found, which is fine
      if (!silent) setAutomationState(null);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    checkExistingRun();
  }, [schemeId, profileId]);

  // Periodic polling & synchronization with backend/mock-portal
  useEffect(() => {
    if (!automationState?.run_id || automationState.automation_status === 'COMPLETED') {
      return;
    }

    const intervalId = setInterval(() => {
      getAutomationStatus({ run_id: automationState.run_id })
        .then((latest) => {
          const stepsChanged = JSON.stringify(latest.planned_steps) !== JSON.stringify(automationState.planned_steps);
          const humanActionChanged = JSON.stringify(latest.human_action_required) !== JSON.stringify(automationState.human_action_required);
          if (
            latest.current_step_index !== automationState.current_step_index ||
            latest.automation_status !== automationState.automation_status ||
            latest.acknowledgment_number !== automationState.acknowledgment_number ||
            stepsChanged ||
            humanActionChanged
          ) {
            setAutomationState(latest);
            if (onStatusChange) onStatusChange(latest);
          }
        })
        .catch(() => {
          // Ignore transient polling error
        });
    }, 1200);

    return () => clearInterval(intervalId);
  }, [
    automationState?.run_id,
    automationState?.current_step_index,
    automationState?.automation_status,
    automationState?.acknowledgment_number,
    automationState?.planned_steps,
    automationState?.human_action_required,
  ]);

  const [browserLaunching, setBrowserLaunching] = useState(false);

  const handleStartAutomation = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await startAutomation({ scheme_id: schemeId, profile_id: profileId });
      setAutomationState(res);
      if (onStatusChange) onStatusChange(res);

      // Automatically launch visible Playwright Chromium browser session
      if (res?.run_id) {
        try {
          authFetch(`${API_BASE_URL}/api/automation/${res.run_id}/browser/launch?headless=false`, {
            method: 'POST',
          }).catch((e) => console.warn('Browser launch notice:', e));
        } catch (e) {
          // ignore transient launch error
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to start automation workflow.');
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchBrowser = async () => {
    if (!automationState?.run_id) return;
    try {
      setBrowserLaunching(true);
      await authFetch(`${API_BASE_URL}/api/automation/${automationState.run_id}/browser/launch?headless=false`, {
        method: 'POST',
      });
    } catch (err: any) {
      console.warn('Could not launch browser:', err);
    } finally {
      setBrowserLaunching(false);
    }
  };

  const handleResumeStep = async (actionType: string) => {
    if (!automationState?.run_id) return;
    try {
      setActionLoading(true);
      setError(null);
      const res = await resumeAutomation({
        run_id: automationState.run_id,
        action_type: actionType,
        confirmation_data: { user_confirmed: true, timestamp: new Date().toISOString() },
      });
      setAutomationState(res);
      if (onStatusChange) onStatusChange(res);
    } catch (err: any) {
      setError(err.message || 'Failed to advance workflow step.');
    } finally {
      setActionLoading(false);
    }
  };


  const getStepIcon = (status: string, isCurrent: boolean) => {
    if (status === 'completed') return '✓';
    if (isCurrent) return '→';
    return '○';
  };

  const getStepClass = (status: string, isCurrent: boolean) => {
    if (status === 'completed') return 'step-done';
    if (isCurrent) return 'step-current';
    return 'step-pending';
  };

  return (
    <div className="automation-progress-panel">
      <div className="automation-header">
        <div>
          <h3>Phase 5B: Application Automation Agent</h3>
          <p className="automation-subtext">
            LangGraph Agent plans and tracks your scheme application, pausing for mandatory human verification steps (Login, CAPTCHA, OTP, Final Submit).
          </p>
        </div>
        {automationState && (
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {automationState.automation_status !== 'COMPLETED' && (
              <span style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#22c55e' }}></span>
                Live Sync Active
              </span>
            )}
            <span className={`status-pill pill-${automationState.automation_status.toLowerCase()}`}>
              {automationState.automation_status.replace(/_/g, ' ')}
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="form-alert error-alert" style={{ marginBottom: '1rem' }}>
          <strong>Notice:</strong> {error}
        </div>
      )}

      {!automationState && (
        <div className="automation-start-card">
          <p>
            The Automation Agent will coordinate your application using your saved profile data, submitted requirements, and uploaded documents.
          </p>
          <div className="agent-notice-box">
            <strong>Important:</strong> The agent pauses at every step requiring human action (Login, CAPTCHA, OTP, Final Submission). It will not bypass security controls.
          </div>
          <button
            className="primary-action-btn"
            onClick={handleStartAutomation}
            disabled={loading}
          >
            {loading ? 'Initializing Agent Workflow...' : 'Start Automation Workflow'}
          </button>
        </div>
      )}

      {automationState && (
        <div className="automation-body">
          {/* Human Action Required Callout */}
          {automationState.automation_status === 'AWAITING_HUMAN_ACTION' &&
            automationState.human_action_required && (
              <div className="human-action-callout">
                <div className="callout-header">
                  <span className="callout-alert-icon">⚠️</span>
                  <div>
                    <span className="callout-badge">ACTION REQUIRED BY CITIZEN</span>
                    <h4>{automationState.human_action_required.step_name || 'Human Verification Required'}</h4>
                  </div>
                </div>
                <p className="callout-message">
                  {automationState.human_action_required.message}
                </p>
                <div style={{ padding: '0.5rem 0.75rem', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', fontSize: '0.82rem', color: '#166534', marginTop: '0.5rem' }}>
                  🔄 <strong>Auto-Sync Enabled:</strong> When you complete this step on the Online Portal, this panel will automatically advance without requiring manual confirmation.
                </div>
                <div className="callout-link-box" style={{ marginTop: '0.6rem', backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '0.85rem' }}>
                  <p style={{ margin: '0 0 0.35rem 0', fontSize: '0.88rem', color: '#1e40af', fontWeight: 600 }}>
                    🤖 Playwright Automated Browser Control:
                  </p>
                  <p style={{ margin: '0 0 0.6rem 0', fontSize: '0.82rem', color: '#1e3a8a', lineHeight: 1.45 }}>
                    An automated Chromium window is running. Complete <strong>Login, CAPTCHA, and OTP</strong> directly inside that window. Once OTP is verified, the AI agent will automatically type all details, attach documents, and navigate the screens!
                  </p>
                  <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={handleLaunchBrowser}
                      className="portal-external-link-btn"
                      style={{ backgroundColor: '#2563eb', color: '#fff', border: 'none', cursor: 'pointer', padding: '0.45rem 0.9rem', borderRadius: '5px', fontWeight: 600 }}
                      disabled={browserLaunching}
                    >
                      {browserLaunching ? 'Launching Chromium...' : '🖥️ Launch / Show Automated Browser'}
                    </button>
                    {automationState.human_action_required.portal_url && (
                      <a
                        href={automationState.human_action_required.portal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="portal-external-link-btn"
                        style={{ backgroundColor: '#f1f5f9', color: '#334155', padding: '0.45rem 0.9rem', borderRadius: '5px' }}
                      >
                        🌐 Open Portal in Tab ↗
                      </a>
                    )}
                  </div>
                </div>

                <div className="callout-actions">
                  <button
                    className="confirm-action-btn"
                    onClick={() =>
                      handleResumeStep(automationState.human_action_required!.action_type)
                    }
                    disabled={actionLoading}
                  >
                    {actionLoading
                      ? 'Confirming...'
                      : `Confirm ${automationState.human_action_required.action_type.replace(/_/g, ' ')} Completed`}
                  </button>
                </div>
              </div>
            )}

          {/* Assembled Form Mapping Preview Card (Phase 5A & 5B Data Bridge) */}
          {automationState.mapped_form_data && (
            <div className="mapped-data-card">
              <div className="mapped-data-header">
                <span className="mapped-icon">📋</span>
                <div>
                  <h4>Assembled Citizen Application Dossier</h4>
                  <p>
                    Data mapped from your Profile & Submitted Requirements to match Online Portal Schema.
                  </p>
                </div>
              </div>
              <div className="mapped-grid">
                <div className="mapped-cell">
                  <span className="cell-label">Applicant Name:</span>
                  <span className="cell-value">{automationState.mapped_form_data.applicant_name}</span>
                </div>
                <div className="mapped-cell">
                  <span className="cell-label">Age / Gender:</span>
                  <span className="cell-value">{automationState.mapped_form_data.age} yrs / {automationState.mapped_form_data.gender}</span>
                </div>
                <div className="mapped-cell">
                  <span className="cell-label">State / District:</span>
                  <span className="cell-value">{automationState.mapped_form_data.state} / {automationState.mapped_form_data.district}</span>
                </div>
                <div className="mapped-cell">
                  <span className="cell-label">Annual Family Income:</span>
                  <span className="cell-value">₹{Number(automationState.mapped_form_data.annual_income).toLocaleString('en-IN')}</span>
                </div>
                <div className="mapped-cell">
                  <span className="cell-label">Aadhaar (Last 4):</span>
                  <span className="cell-value">XXXX-XXXX-{automationState.mapped_form_data.aadhaar_last_four}</span>
                </div>
                <div className="mapped-cell">
                  <span className="cell-label">Target Scheme:</span>
                  <span className="cell-value">{automationState.mapped_form_data.scheme_id}</span>
                </div>
              </div>
            </div>
          )}

          {/* Completed Workflow Banner */}
          {automationState.automation_status === 'COMPLETED' && (
            <div className="workflow-completed-banner">
              <span className="success-icon">🎉</span>
              <div>
                <h4>Application Workflow Completed!</h4>
                <p>
                  All planned steps have been successfully executed and citizen-confirmed.
                  Application status: <strong>{automationState.application_status}</strong>.
                </p>
                {automationState.acknowledgment_number && (
                  <p style={{ marginTop: '0.4rem', fontWeight: 600 }}>
                    Official Acknowledgment Reference: <code>{automationState.acknowledgment_number}</code>
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Planned Steps Progression */}
          <div className="steps-progress-list">
            <h4>Planned Execution Plan ({automationState.planned_steps.length} Steps)</h4>
            <div className="planned-steps-timeline">
              {automationState.planned_steps.map((step, idx) => {
                const isCurrent = idx === automationState.current_step_index;
                const stepCls = getStepClass(step.status, isCurrent);

                return (
                  <div key={step.step_id || idx} className={`timeline-item ${stepCls}`}>
                    <div className="timeline-marker">
                      <span className="marker-icon">{getStepIcon(step.status, isCurrent)}</span>
                    </div>
                    <div className="timeline-content">
                      <div className="timeline-title-row">
                        <span className="timeline-title">{step.name}</span>
                        <div className="timeline-tags">
                          <span className={`step-type-tag tag-${step.type}`}>
                            {step.type === 'human_action' ? 'Human Action' : 'Automated'}
                          </span>
                          <span className={`step-status-tag tag-${step.status}`}>
                            {step.status.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      {step.description && (
                        <p className="timeline-desc">{step.description}</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
