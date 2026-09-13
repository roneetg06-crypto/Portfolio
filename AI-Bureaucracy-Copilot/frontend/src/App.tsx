import React, { useEffect, useState } from 'react';
import {
  CitizenProfileCreatePayload,
  CitizenProfileResponse,
  createProfile,
  discoverSchemes,
  getMyProfile,
  Scheme,
} from './api/client';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { ProfilePage } from './pages/ProfilePage';
import { SchemeResultsPage } from './pages/SchemeResultsPage';
import { MainLayout } from './components/layout/MainLayout';
import './App.css';
import './styles/gov-theme.css';

const MainDashboard: React.FC = () => {
  const { user, logout } = useAuth();

  // Profile & Discovery state
  const [currentProfile, setCurrentProfile] = useState<CitizenProfileResponse | null>(null);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [discoveryLoading, setDiscoveryLoading] = useState<boolean>(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);

  // In-app view state: 'schemes' | 'profile_update' | 'profile_create'
  const [view, setView] = useState<'schemes' | 'profile_update' | 'profile_create'>('profile_create');

  // Auto-load user's existing profile if available
  useEffect(() => {
    const loadExistingProfile = async () => {
      try {
        const prof = await getMyProfile();
        if (prof) {
          setCurrentProfile(prof);
          setView('schemes');
          // Push schemes to history so back button stays within SPA
          window.history.replaceState({ view: 'schemes' }, '', '#schemes');
          const results = await discoverSchemes(prof.state);
          setSchemes(results);
        } else {
          setView('profile_create');
          window.history.replaceState({ view: 'profile_create' }, '', '#register-profile');
        }
      } catch (err) {
        setView('profile_create');
        window.history.replaceState({ view: 'profile_create' }, '', '#register-profile');
      }
    };
    loadExistingProfile();
  }, [user?.id]);

  // Handle browser Back / Forward buttons without exiting the SPA or logging out
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      if (event.state && event.state.view) {
        setView(event.state.view);
      } else if (currentProfile) {
        setView('schemes');
      } else {
        setView('profile_create');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [currentProfile]);

  const handleProfileSubmit = async (payload: CitizenProfileCreatePayload) => {
    setDiscoveryLoading(true);
    setDiscoveryError(null);
    try {
      // 1. Create/Update Citizen Profile linked to logged-in user
      const profile = await createProfile(payload);
      setCurrentProfile(profile);

      // 2. Discover Schemes for the selected state across all sectors (Health & Education)
      const results = await discoverSchemes(profile.state);
      setSchemes(results);

      // 3. Move to schemes view and push history state
      setView('schemes');
      window.history.pushState({ view: 'schemes' }, '', '#schemes');
    } catch (err: any) {
      setDiscoveryError(err.message || 'Failed to submit profile or discover schemes.');
    } finally {
      setDiscoveryLoading(false);
    }
  };

  const handleStartProfileUpdate = () => {
    // Preserve currentProfile so form pre-populates
    setView('profile_update');
    window.history.pushState({ view: 'profile_update' }, '', '#profile-update');
  };

  const handleCancelProfileUpdate = () => {
    if (currentProfile) {
      setView('schemes');
      window.history.pushState({ view: 'schemes' }, '', '#schemes');
    }
  };

  return (
    <MainLayout
      activeTab="discovery"
      userEmail={user?.email}
      profileId={currentProfile?.profile_id}
      onLogout={logout}
      onResetProfile={handleStartProfileUpdate}
      onUpdateProfile={handleStartProfileUpdate}
    >
      {view === 'schemes' && currentProfile ? (
        <SchemeResultsPage
          profile={currentProfile}
          schemes={schemes}
          isLoading={discoveryLoading}
          error={discoveryError}
          onReset={handleStartProfileUpdate}
        />
      ) : (
        <ProfilePage
          onSubmitProfile={handleProfileSubmit}
          isLoading={discoveryLoading}
          serverError={discoveryError}
          initialData={view === 'profile_update' ? currentProfile : null}
          isUpdateMode={view === 'profile_update'}
          onCancel={view === 'profile_update' ? handleCancelProfileUpdate : undefined}
        />
      )}
    </MainLayout>
  );
};

const AuthGate: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [showSignup, setShowSignup] = useState(false);

  if (isLoading) {
    return (
      <div className="gov-loading-screen">
        <div className="gov-spinner-large"></div>
        <p>Verifying Citizen Credentials...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return showSignup ? (
      <SignupPage onSwitchToLogin={() => setShowSignup(false)} />
    ) : (
      <LoginPage onSwitchToSignup={() => setShowSignup(true)} />
    );
  }

  return <MainDashboard />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  );
};

export default App;
