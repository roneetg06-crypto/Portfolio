import React from 'react';
import { Scheme } from '../api/client';

interface SchemeCardProps {
  scheme: Scheme;
  isFocused?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
  onApply?: (scheme: Scheme) => void;
}

export const SchemeCard: React.FC<SchemeCardProps> = ({
  scheme,
  isFocused = false,
  onFocus,
  onBlur,
  onApply,
}) => {
  const isCentral = scheme.level.toLowerCase() === 'central';

  const handleCardClick = (e: React.MouseEvent) => {
    // If click originated from interactive child elements (buttons, links), don't interfere
    const target = e.target as HTMLElement;
    if (target.closest('button') || target.closest('a')) {
      return;
    }

    if (!isFocused && onFocus) {
      onFocus();
    }
  };

  return (
    <div
      className={`scheme-card ${isFocused ? 'is-focused' : ''}`}
      onMouseEnter={onFocus}
      onMouseLeave={onBlur}
      onClick={handleCardClick}
      role="article"
      aria-label={`${scheme.name} card`}
      tabIndex={0}
      onFocus={onFocus}
      onBlur={onBlur}
    >
      <div className="scheme-card-header">
        {isFocused && (
          <div className="scheme-focus-indicator" aria-live="polite">
            <span>✨ Selected Scheme Focus</span>
          </div>
        )}
        <div className="scheme-badges">
          <span className={`badge ${isCentral ? 'badge-central' : 'badge-state'}`}>
            {isCentral ? 'Central Scheme' : `State Scheme (${scheme.applicable_states.join(', ')})`}
          </span>
          <span className="badge badge-sector">{scheme.sector.toUpperCase()}</span>
        </div>
        <h3 className="scheme-title">{scheme.name}</h3>
        <p className="scheme-authority">Issued by: {scheme.issuing_authority}</p>
      </div>

      <div className="scheme-card-body">
        <p className="scheme-description">{scheme.short_description}</p>

        <div className="scheme-benefits-box">
          <strong>Key Benefits:</strong>
          <p>{scheme.benefits}</p>
        </div>
      </div>

      <div
        className="scheme-card-footer"
        style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginTop: 'auto' }}
      >
        {onApply && (
          <button
            className="apply-btn"
            onClick={(e) => {
              e.stopPropagation();
              onApply(scheme);
            }}
            style={{ width: '100%', textAlign: 'center' }}
          >
            Apply / Check Requirements &rarr;
          </button>
        )}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.82rem',
            gap: '0.5rem',
            flexWrap: 'wrap',
          }}
        >
          <a
            href={`http://localhost:5174/?scheme_id=${encodeURIComponent(scheme.scheme_id)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="scheme-portal-link"
            onClick={(e) => e.stopPropagation()}
            title="Open Online Application Portal"
          >
            🏛️ Online Application Portal ↗
          </a>
          {scheme.official_link && (
            <a
              href={scheme.official_link}
              target="_blank"
              rel="noopener noreferrer"
              className="scheme-link-btn"
              onClick={(e) => e.stopPropagation()}
              title="Official external government portal"
            >
              Gov.in Official Site ↗
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
