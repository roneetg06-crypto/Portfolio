import React, { useState } from 'react';
import { CitizenProfileResponse, Scheme } from '../api/client';
import { SchemeCard } from '../components/SchemeCard';
import { SchemeQuestionBox } from '../components/SchemeQuestionBox';
import { SchemeApplicationModal } from '../components/SchemeApplicationModal';

interface SchemeResultsPageProps {
  profile: CitizenProfileResponse;
  schemes: Scheme[];
  isLoading: boolean;
  error: string | null;
  onReset: () => void;
}

export const SchemeResultsPage: React.FC<SchemeResultsPageProps> = ({
  profile,
  schemes,
  isLoading,
  error,
  onReset,
}) => {
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [focusedCardId, setFocusedCardId] = useState<string | null>(null);

  return (
    <div className="page-container" onClick={() => setFocusedCardId(null)}>
      <div className="results-header-card" onClick={(e) => e.stopPropagation()}>
        <div className="profile-summary">
          <h2>Discovered Schemes for {profile.name}</h2>
          <div className="profile-meta">
            <span><strong>State:</strong> {profile.state}</span>
            <span><strong>District:</strong> {profile.district}</span>
            <span><strong>Age:</strong> {profile.age}</span>
            <span><strong>Gender:</strong> {profile.gender}</span>
          </div>
        </div>
        <button className="secondary-btn" onClick={onReset}>
          &larr; Update Profile / Change State
        </button>
      </div>

      {/* RAG Knowledge Agent Question Box */}
      <div onClick={(e) => e.stopPropagation()}>
        <SchemeQuestionBox state={profile.state} />
      </div>

      {isLoading && (
        <div className="state-box loading">
          <span className="spinner"></span>
          <p>Discovering schemes for {profile.state}...</p>
        </div>
      )}

      {!isLoading && error && (
        <div className="state-box error">
          <div className="status-badge error-badge">Discovery Error</div>
          <p className="error-message">{error}</p>
          <button className="retry-btn" onClick={onReset}>
            Back to Profile Registration
          </button>
        </div>
      )}

      {!isLoading && !error && schemes.length === 0 && (
        <div className="state-box info">
          <p>No schemes were found matching state "{profile.state}".</p>
        </div>
      )}

      {!isLoading && !error && schemes.length > 0 && (
        <div
          className="schemes-grid"
          onMouseLeave={() => setFocusedCardId(null)}
          onClick={(e) => e.stopPropagation()}
        >
          {schemes.map((scheme) => (
            <SchemeCard
              key={scheme.scheme_id}
              scheme={scheme}
              isFocused={focusedCardId === scheme.scheme_id}
              onFocus={() => setFocusedCardId(scheme.scheme_id)}
              onBlur={() => {
                // Allow mouse leave or tapping sibling
              }}
              onApply={(s) => setSelectedScheme(s)}
            />
          ))}
        </div>
      )}

      {/* Phase 4 Scheme Application Modal */}
      {selectedScheme && (
        <SchemeApplicationModal
          scheme={selectedScheme}
          profileId={profile.profile_id}
          profile={profile}
          onClose={() => setSelectedScheme(null)}
        />
      )}
    </div>
  );
};
