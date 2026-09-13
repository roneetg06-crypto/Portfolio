import React from 'react';
import { Navbar } from './Navbar';
import { Footer } from './Footer';

interface MainLayoutProps {
  children: React.ReactNode;
  activeTab?: 'discovery';
  onTabChange?: (tab: 'discovery') => void;
  userEmail?: string;
  profileId?: string;
  onLogout: () => void;
  onResetProfile?: () => void;
  onUpdateProfile?: () => void;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  activeTab = 'discovery',
  onTabChange,
  userEmail,
  profileId,
  onLogout,
  onResetProfile,
  onUpdateProfile,
}) => {
  return (
    <div className="gov-background">
      {/* Sticky Full-Width Navbar */}
      <Navbar
        activeTab={activeTab}
        onTabChange={onTabChange}
        userEmail={userEmail}
        profileId={profileId}
        onLogout={onLogout}
        onUpdateProfile={onUpdateProfile || onResetProfile}
      />

      {/* Main Content Area */}
      <main className="gov-main-wrapper" id="main-content">
        {children}
      </main>

      {/* Full-Width Footer */}
      <Footer onNavigateTab={onTabChange} onResetProfile={onResetProfile} />
    </div>
  );
};
