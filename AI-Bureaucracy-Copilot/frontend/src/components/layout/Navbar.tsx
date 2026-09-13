import React, { useEffect, useRef, useState } from 'react';
import { NotificationCenter } from '../NotificationCenter';

interface NavbarProps {
  activeTab?: 'discovery';
  onTabChange?: (tab: 'discovery') => void;
  userEmail?: string;
  profileId?: string;
  onLogout?: () => void;
  onUpdateProfile?: () => void;
  isAuthMode?: boolean;
  authModeType?: 'login' | 'signup';
  onSwitchAuthMode?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab = 'discovery',
  onTabChange,
  userEmail,
  profileId,
  onLogout,
  onUpdateProfile,
  isAuthMode = false,
  authModeType = 'login',
  onSwitchAuthMode,
}) => {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="gov-navbar-sticky">
      {/* Tricolor Accent Strip: Saffron / White / Green */}
      <div className="gov-tricolor-accent" aria-hidden="true">
        <div className="accent-saffron" />
        <div className="accent-white" />
        <div className="accent-green" />
      </div>

      {/* Main Navy Bar */}
      <nav className="gov-navbar" aria-label="Main Citizen Navigation">
        <div className="gov-navbar-inner">
          {/* Brand Logo & Wordmark */}
          <div
            className="gov-brand"
            onClick={() => onTabChange && onTabChange('discovery')}
          >
            <div className="gov-brand-icon" title="JanSevaAI Welfare Emblem">
              {/* Generic geometric 12-spoke welfare wheel motif */}
              <svg
                width="30"
                height="30"
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle cx="50" cy="50" r="44" stroke="#FF9933" strokeWidth="5" />
                <circle cx="50" cy="50" r="28" stroke="#ffffff" strokeWidth="2.5" />
                <circle cx="50" cy="50" r="12" fill="#FF9933" />
                {[...Array(12)].map((_, i) => {
                  const angle = (i * 30 * Math.PI) / 180;
                  const x1 = 50 + 14 * Math.cos(angle);
                  const y1 = 50 + 14 * Math.sin(angle);
                  const x2 = 50 + 28 * Math.cos(angle);
                  const y2 = 50 + 28 * Math.sin(angle);
                  return (
                    <line
                      key={i}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="#ffffff"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    />
                  );
                })}
              </svg>
            </div>
            <div className="gov-brand-titles">
              <span className="gov-brand-super">भारत डिजिटल सेवा | Digital Public Welfare</span>
              <span className="gov-brand-main">
                <span className="brand-jan">Jan</span>
                <span className="brand-seva">Seva</span>
                <span className="brand-ai">AI</span>
              </span>
              <span className="gov-brand-sub">AI Bureaucracy Copilot & Autonomous Filing</span>
            </div>
          </div>

          {/* Navigation Links / Tabs */}
          <div className="gov-nav-links">
            {!isAuthMode ? (
              <>
                <button
                  className={`gov-nav-btn ${activeTab === 'discovery' ? 'active' : ''}`}
                  onClick={() => onTabChange && onTabChange('discovery')}
                >
                  🏛️ Schemes Discovery
                </button>
                <a
                  href="http://localhost:5174"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="gov-nav-portal-icon"
                  title="Open Portal in separate window"
                >
                  🏛️ Portal ↗
                </a>
              </>
            ) : (
              <div className="gov-auth-badge" title="National Citizen Entitlement Gateway">
                🏛️ Unified Citizen Services Gateway
              </div>
            )}
          </div>

          {/* Right Action Group */}
          <div className="gov-nav-right">
            {!isAuthMode ? (
              <>
                <NotificationCenter profileId={profileId || 'default'} />

                {/* Professional User Profile Menu Dropdown */}
                <div className="gov-user-menu-container" ref={userMenuRef}>
                  <button
                    className="gov-user-avatar-btn"
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    aria-expanded={isUserMenuOpen}
                    aria-haspopup="true"
                    title="Citizen Account Menu"
                  >
                    <span className="gov-user-avatar-icon">👤</span>
                    <span style={{ fontSize: '0.75rem' }}>{isUserMenuOpen ? '▴' : '▾'}</span>
                  </button>

                  {isUserMenuOpen && (
                    <div className="gov-user-dropdown" role="menu">
                      <div className="gov-user-dropdown-header">
                        <span className="gov-user-dropdown-label">Citizen Account</span>
                        <div className="gov-user-dropdown-email">
                          {userEmail || 'Authenticated User'}
                        </div>
                      </div>

                      <div className="gov-user-dropdown-items">
                        {onUpdateProfile && (
                          <button
                            className="gov-user-dropdown-item"
                            onClick={() => {
                              setIsUserMenuOpen(false);
                              onUpdateProfile();
                            }}
                            role="menuitem"
                          >
                            <span>👤</span> Update Profile
                          </button>
                        )}
                        {onLogout && (
                          <button
                            className="gov-user-dropdown-item logout-item"
                            onClick={() => {
                              setIsUserMenuOpen(false);
                              onLogout();
                            }}
                            role="menuitem"
                          >
                            <span>⎋</span> Sign Out
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <a
                  href="http://localhost:5174"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="gov-nav-portal-icon"
                  title="Open Portal in separate window"
                >
                  🏛️ Portal ↗
                </a>
                {onSwitchAuthMode && (
                  <button
                    className="gov-nav-btn gov-nav-btn-highlight"
                    onClick={onSwitchAuthMode}
                  >
                    {authModeType === 'login' ? '📝 New User? Register' : '🔐 Existing User? Sign In'}
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
};
