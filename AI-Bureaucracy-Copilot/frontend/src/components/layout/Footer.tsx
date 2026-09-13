import React from 'react';

interface FooterProps {
  onNavigateTab?: (tab: 'discovery') => void;
  onResetProfile?: () => void;
  isAuthPage?: boolean;
  onSwitchAuth?: (mode: 'login' | 'signup') => void;
  currentAuthMode?: 'login' | 'signup';
}

export const Footer: React.FC<FooterProps> = ({
  onNavigateTab,
  onResetProfile,
  isAuthPage = false,
  onSwitchAuth,
  currentAuthMode = 'login',
}) => {
  return (
    <footer className="gov-footer" role="contentinfo">
      {/* Tricolor Accent Stripe at top of footer */}
      <div className="gov-tricolor-accent" aria-hidden="true">
        <div className="accent-saffron" />
        <div className="accent-white" />
        <div className="accent-green" />
      </div>

      <div className="gov-footer-inner">
        {/* Prominent Disclaimer Card as required by hackathon guardrails */}
        <div className="gov-disclaimer-card" role="note">
          <p>
            ⚠️ <strong>DISCLAIMER:</strong> JanSeva is a prototype built for VEDA 2K26 Hackathon.
            Not an official Government of India portal. All scheme criteria, RAG vector embeddings,
            and autonomous Playwright submissions run in local sandbox test environments.
          </p>
        </div>

        <div className="gov-footer-columns">
          {/* Column 1: About JanSeva */}
          <div className="gov-footer-col">
            <h4>About JanSevaAI / परिचय</h4>
            <p>
              JanSevaAI (जनसेवा एआई) is an agentic AI bureaucracy copilot that automates welfare discovery,
              eligibility verification, dynamic document generation, and direct browser-level filing for Indian citizens.
            </p>
            <p>
              Built with FastAPI, PostgreSQL, LangGraph multi-agent orchestration, and Playwright autonomous browser automation.
            </p>
          </div>

          {/* Column 2: Quick Links */}
          <div className="gov-footer-col">
            <h4>Quick Links / त्वरित लिंक</h4>
            <ul className="gov-footer-links">
              {isAuthPage ? (
                <>
                  {currentAuthMode === 'login' ? (
                    <li>
                      <button
                        type="button"
                        onClick={() => onSwitchAuth && onSwitchAuth('signup')}
                      >
                        Register New Citizen Account
                      </button>
                    </li>
                  ) : (
                    <li>
                      <button
                        type="button"
                        onClick={() => onSwitchAuth && onSwitchAuth('login')}
                      >
                        Citizen Login Portal
                      </button>
                    </li>
                  )}
                  <li>
                    <a
                      href="http://localhost:5174"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Mock Government Portal (5174) ↗
                    </a>
                  </li>
                  <li>
                    <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                      Secure PostgreSQL Authentication
                    </span>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <button
                      type="button"
                      onClick={() => onNavigateTab && onNavigateTab('discovery')}
                    >
                      Scheme Discovery
                    </button>
                  </li>
                  {onResetProfile && (
                    <li>
                      <button type="button" onClick={onResetProfile}>
                        Update Citizen Profile
                      </button>
                    </li>
                  )}
                  <li>
                    <a
                      href="http://localhost:5174"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Online Application Portal (5174) ↗
                    </a>
                  </li>
                </>
              )}
            </ul>
          </div>

          {/* Column 3: Citizen Grievance & Helpdesk */}
          <div className="gov-footer-col">
            <h4>Public Helpdesk & Grievance / सहायता</h4>
            <div className="gov-contact-item">
              <span className="icon">📞</span>
              <span>
                <strong>Toll-Free Helpline:</strong><br />
                1800-JANSEVA (Prototype Support)
              </span>
            </div>
            <div className="gov-contact-item">
              <span className="icon">✉️</span>
              <span>
                <strong>Grievance Email:</strong><br />
                helpdesk@janseva.veda2k26.org
              </span>
            </div>
            <div className="gov-contact-item">
              <span className="icon">🕒</span>
              <span>
                <strong>Operating Hours:</strong><br />
                Monday – Saturday: 09:00 AM – 06:00 PM IST
              </span>
            </div>
          </div>
        </div>

        {/* Footer Bottom Bar */}
        <div className="gov-footer-bottom">
          <span>&copy; 2026 JanSevaAI Team. All rights reserved.</span>
          <span>Designed for Transparent & Autonomous Citizen Service Delivery</span>
          <span>VEDA 2K26 Hackathon Edition</span>
        </div>
      </div>
    </footer>
  );
};
