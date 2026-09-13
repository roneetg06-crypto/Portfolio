import React from 'react';

export interface WorkflowStatusIndicatorProps {
  currentStep: 'info' | 'documents' | 'automation' | 'complete';
  infoSubmitted: boolean;
  documentsVerified: boolean;
  hasMissingDocs: boolean;
  automationStatus?: string | null;
}

export const WorkflowStatusIndicator: React.FC<WorkflowStatusIndicatorProps> = ({
  currentStep,
  infoSubmitted,
  documentsVerified,
  hasMissingDocs,
  automationStatus,
}) => {
  const getStepStatus = (step: 'profile' | 'discovery' | 'info' | 'documents' | 'automation') => {
    switch (step) {
      case 'profile':
      case 'discovery':
        return { icon: '✓', state: 'done', label: 'Completed' };

      case 'info':
        if (infoSubmitted) return { icon: '✓', state: 'done', label: 'Submitted' };
        if (currentStep === 'info') return { icon: '→', state: 'active', label: 'In Progress' };
        return { icon: '!', state: 'action', label: 'Pending Info' };

      case 'documents':
        if (documentsVerified && !hasMissingDocs) return { icon: '✓', state: 'done', label: 'Verified' };
        if (hasMissingDocs) return { icon: '!', state: 'action', label: 'Action Required' };
        if (currentStep === 'documents') return { icon: '→', state: 'active', label: 'In Progress' };
        return { icon: ' ', state: 'pending', label: 'Pending Uploads' };

      case 'automation':
        if (automationStatus === 'COMPLETED') return { icon: '✓', state: 'done', label: 'Completed' };
        if (automationStatus === 'AWAITING_HUMAN_ACTION') return { icon: '!', state: 'action', label: 'Action Required' };
        if (automationStatus === 'IN_PROGRESS' || currentStep === 'automation') return { icon: '→', state: 'active', label: 'In Progress' };
        return { icon: ' ', state: 'pending', label: 'Pending Start' };

      default:
        return { icon: '•', state: 'pending', label: 'Pending' };
    }
  };

  const steps = [
    { key: 'profile', title: '1. Citizen Profile' },
    { key: 'discovery', title: '2. Scheme Discovery & Knowledge' },
    { key: 'info', title: '3. Additional Information' },
    { key: 'documents', title: '4. Document Verification' },
    { key: 'automation', title: '5. Application Automation (LangGraph Agent)' },
  ];

  return (
    <div className="workflow-status-indicator">
      <h4>Application Process Workflow Status</h4>
      <div className="checklist-grid">
        {steps.map((s) => {
          const status = getStepStatus(s.key as any);
          return (
            <div key={s.key} className={`checklist-item item-${status.state}`}>
              <span className={`status-badge-icon icon-${status.state}`}>{status.icon}</span>
              <div className="item-text">
                <span className="item-title">{s.title}</span>
                <span className="item-label">{status.label}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
