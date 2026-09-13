import React from 'react';
import { ProfileForm } from '../components/ProfileForm';
import { CitizenProfileCreatePayload, CitizenProfileResponse } from '../api/client';

interface ProfilePageProps {
  onSubmitProfile: (payload: CitizenProfileCreatePayload) => void;
  isLoading: boolean;
  serverError: string | null;
  initialData?: CitizenProfileResponse | null;
  isUpdateMode?: boolean;
  onCancel?: () => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({
  onSubmitProfile,
  isLoading,
  serverError,
  initialData,
  isUpdateMode = false,
  onCancel,
}) => {
  return (
    <div className="page-container">
      <ProfileForm
        onSubmit={onSubmitProfile}
        isLoading={isLoading}
        serverError={serverError}
        initialData={initialData}
        isUpdateMode={isUpdateMode}
        onCancel={onCancel}
      />
    </div>
  );
};
