const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// JWT Token Storage in memory + sessionStorage
let authToken: string | null = sessionStorage.getItem('janseva_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    sessionStorage.setItem('janseva_token', token);
  } else {
    sessionStorage.removeItem('janseva_token');
  }
}

export function getAuthToken(): string | null {
  return authToken || sessionStorage.getItem('janseva_token');
}

// Authenticated fetch wrapper
export async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});
  const token = getAuthToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(url, { ...options, headers });
}

// Authentication Interfaces
export interface AuthUser {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export async function apiSignup(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || err.detail || 'Signup failed');
  }
  const data: AuthResponse = await response.json();
  setAuthToken(data.access_token);
  return data;
}

export async function apiLogin(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || err.detail || 'Login failed');
  }
  const data: AuthResponse = await response.json();
  setAuthToken(data.access_token);
  return data;
}

export async function apiGetMe(): Promise<AuthUser> {
  const response = await authFetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || err.detail || 'Failed to fetch authenticated user');
  }
  return await response.json();
}

export function apiLogout() {
  setAuthToken(null);
}

// Health Interface
export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
}

export interface CitizenProfileCreatePayload {
  name: string;
  age: number;
  gender: string;
  state: string;
  district: string;
}

export interface CitizenProfileResponse {
  profile_id: string;
  name: string;
  age: number;
  gender: string;
  state: string;
  district: string;
  user_id?: string;
  created_at: string;
}

export interface Scheme {
  scheme_id: string;
  name: string;
  sector: string;
  level: string;
  applicable_states: string[];
  issuing_authority: string;
  short_description: string;
  benefits: string;
  official_link: string;
}

export interface KnowledgeAskPayload {
  question: string;
  state?: string;
  sector?: string;
  scheme_id?: string;
}

export interface SchemeSource {
  scheme_id: string;
  scheme_name: string;
  level: string;
}

export interface KnowledgeAskResponse {
  answer: string;
  sources: SchemeSource[];
  grounded: boolean;
  scheme_id?: string | null;
  action?: string | null;
  action_url?: string | null;
  action_title?: string | null;
  requires_human_verification?: boolean;
}

// Phase 4 Interfaces
export interface RequiredInfoField {
  name: string;
  label: string;
  type: string;
  required: boolean;
  options?: string[];
  help_text?: string;
}

export interface RequiredDocumentItem {
  name: string;
  label: string;
  required: boolean;
  description?: string;
}

export interface SchemeInfoRequirementsResponse {
  scheme_id: string;
  scheme_name: string;
  required_info: RequiredInfoField[];
}

export interface SchemeInfoSubmissionPayload {
  profile_id?: string;
  data: Record<string, any>;
}

export interface SchemeInfoSubmissionResponse {
  status: string;
  scheme_id: string;
  profile_id?: string;
  submitted_information: Record<string, any>;
  missing_information: string[];
}

export interface SchemeRequiredDocumentsResponse {
  scheme_id: string;
  scheme_name: string;
  required_documents: RequiredDocumentItem[];
}

export interface DocumentUploadResponse {
  status: string;
  document_id: string;
  document_name: string;
  original_filename: string;
  verification_status: string;
  verification_message: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface DocumentStatusItem {
  name: string;
  label: string;
  required: boolean;
  status: 'VERIFIED' | 'PENDING' | 'MISSING' | 'UNCLEAR' | 'INVALID' | 'MANUAL_VERIFICATION_REQUIRED';
  verification_message: string;
  document_id?: string | null;
  uploaded_at?: string | null;
  original_filename?: string | null;
  size_bytes?: number | null;
}

export interface DocumentsStatusResponse {
  scheme_id: string;
  profile_id?: string;
  documents: DocumentStatusItem[];
}

export async function fetchHealthStatus(timeoutMs: number = 5000): Promise<HealthResponse> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      signal: controller.signal,
      headers: { 'Accept': 'application/json' },
    });
    clearTimeout(id);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error status: ${response.status}`);
    }
    return await response.json();
  } catch (error: any) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new Error('Backend request timed out. Please check if the server is running.');
    }
    throw new Error(error.message || 'Failed to connect to backend server.');
  }
}

export async function createProfile(
  payload: CitizenProfileCreatePayload
): Promise<CitizenProfileResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to create profile (Status ${response.status})`);
  }

  return await response.json();
}

export async function getMyProfile(): Promise<CitizenProfileResponse | null> {
  const response = await authFetch(`${API_BASE_URL}/api/profile/me`, {
    headers: { 'Accept': 'application/json' },
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to fetch user profile');
  }
  return await response.json();
}

export async function discoverSchemes(
  state: string,
  sector?: string
): Promise<Scheme[]> {
  const params = new URLSearchParams({ state });
  if (sector && sector !== 'all') {
    params.append('sector', sector);
  }
  const response = await authFetch(`${API_BASE_URL}/api/schemes/discover?${params.toString()}`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to discover schemes (Status ${response.status})`);
  }

  return await response.json();
}

export async function evaluateEligibility(
  schemeId: string,
  profileId?: string,
  data?: Record<string, any>
): Promise<any> {
  const response = await authFetch(`${API_BASE_URL}/api/schemes/${encodeURIComponent(schemeId)}/evaluate-eligibility`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ profile_id: profileId, data: data || {} }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.detail || 'Eligibility evaluation failed.');
  }

  return await response.json();
}

export async function askKnowledgeAgent(
  payload: KnowledgeAskPayload
): Promise<KnowledgeAskResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/knowledge/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error || `Failed to get answer from Knowledge Agent (Status ${response.status})`
    );
  }

  return await response.json();
}

// Phase 4 API Functions

export async function getInformationRequirements(
  schemeId: string
): Promise<SchemeInfoRequirementsResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/schemes/${encodeURIComponent(schemeId)}/information-requirements`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch scheme requirements (Status ${response.status})`);
  }

  return await response.json();
}

export async function submitInformation(
  schemeId: string,
  payload: SchemeInfoSubmissionPayload
): Promise<SchemeInfoSubmissionResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/schemes/${encodeURIComponent(schemeId)}/information`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to submit information (Status ${response.status})`);
  }

  return await response.json();
}

export async function getRequiredDocuments(
  schemeId: string,
  profileId?: string
): Promise<SchemeRequiredDocumentsResponse> {
  const params = new URLSearchParams();
  if (profileId) params.append('profile_id', profileId);

  const url = `${API_BASE_URL}/api/schemes/${encodeURIComponent(schemeId)}/documents/required${params.toString() ? `?${params}` : ''}`;
  const response = await authFetch(url, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch required documents (Status ${response.status})`);
  }

  return await response.json();
}

export async function uploadDocument(
  file: File,
  documentName: string,
  schemeId: string,
  profileId?: string
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_name', documentName);
  formData.append('scheme_id', schemeId);
  if (profileId) formData.append('profile_id', profileId);

  const response = await authFetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Document upload failed (Status ${response.status})`);
  }

  return await response.json();
}

export async function getDocumentsStatus(
  schemeId: string,
  profileId?: string
): Promise<DocumentsStatusResponse> {
  const params = new URLSearchParams({ scheme_id: schemeId });
  if (profileId) params.append('profile_id', profileId);

  const response = await authFetch(`${API_BASE_URL}/api/documents/status?${params.toString()}`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch document status (Status ${response.status})`);
  }

  return await response.json();
}

// Phase 5B Interfaces
export interface PlannedStepItem {
  step_id: string;
  name: string;
  type: 'human_action' | 'auto';
  action_type?: string;
  status: 'pending' | 'completed';
  description?: string;
}

export interface HumanActionRequiredDetail {
  action_type: string;
  step_id: string;
  step_name?: string;
  message: string;
  portal_url?: string;
}

export interface AutomationStatusResponse {
  run_id: string;
  scheme_id: string;
  profile_id: string;
  automation_status: 'PLANNING' | 'IN_PROGRESS' | 'AWAITING_HUMAN_ACTION' | 'COMPLETED' | 'FAILED';
  application_status: 'DRAFT' | 'PENDING_CITIZEN_ACTION' | 'SUBMITTED';
  current_step_index: number;
  planned_steps: PlannedStepItem[];
  human_action_required?: HumanActionRequiredDetail | null;
  mapped_form_data?: Record<string, any> | null;
  portal_session_id?: string | null;
  acknowledgment_number?: string | null;
}

export interface AutomationStartPayload {
  scheme_id: string;
  profile_id: string;
}

export interface AutomationResumePayload {
  run_id: string;
  action_type: string;
  confirmation_data?: Record<string, any>;
}

export interface NotificationItem {
  notification_id: string;
  profile_id: string;
  scheme_id: string;
  run_id?: string;
  action_type: string;
  message: string;
  portal_url?: string;
  status: 'ACTION_REQUIRED' | 'RESOLVED';
  created_at: string;
}

export interface NotificationListResponse {
  notifications: NotificationItem[];
}

// Phase 5B API Functions

export async function startAutomation(
  payload: AutomationStartPayload
): Promise<AutomationStatusResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/automation/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to start automation (Status ${response.status})`);
  }

  return await response.json();
}

export async function getAutomationStatus(
  params: { run_id?: string; scheme_id?: string; profile_id?: string }
): Promise<AutomationStatusResponse> {
  const query = new URLSearchParams();
  if (params.run_id) query.append('run_id', params.run_id);
  if (params.scheme_id) query.append('scheme_id', params.scheme_id);
  if (params.profile_id) query.append('profile_id', params.profile_id);

  const response = await authFetch(`${API_BASE_URL}/api/automation/status?${query.toString()}`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to get automation status (Status ${response.status})`);
  }

  return await response.json();
}

export async function resumeAutomation(
  payload: AutomationResumePayload
): Promise<AutomationStatusResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/automation/resume`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to resume automation (Status ${response.status})`);
  }

  return await response.json();
}

export async function fetchNotifications(
  profileId: string
): Promise<NotificationListResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/notifications?profile_id=${encodeURIComponent(profileId)}`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch notifications (Status ${response.status})`);
  }

  return await response.json();
}

export function getNotificationStreamUrl(profileId: string): string {
  return `${API_BASE_URL}/api/notifications/stream?profile_id=${encodeURIComponent(profileId || 'default')}`;
}

export async function triggerTestNotification(payload: {
  profile_id?: string;
  scheme_id?: string;
  action_type?: string;
  message?: string;
  portal_url?: string;
}): Promise<{ status: string; notification: NotificationItem }> {
  const response = await authFetch(`${API_BASE_URL}/api/notifications/test-trigger`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to trigger test notification (Status ${response.status})`);
  }

  return await response.json();
}

export async function resolveNotification(
  notificationId: string,
  profileId: string = 'default'
): Promise<{ status: string; notification_id: string }> {
  const response = await authFetch(
    `${API_BASE_URL}/api/notifications/${encodeURIComponent(notificationId)}/resolve?profile_id=${encodeURIComponent(profileId)}`,
    {
      method: 'POST',
      headers: { 'Accept': 'application/json' },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to resolve notification (Status ${response.status})`);
  }

  return await response.json();
}

export interface ApplicationStateResponse {
  run_id: string;
  scheme_id: string;
  profile_id: string;
  automation_status: string;
  application_status: string;
  current_step_index: number;
  portal_session_id?: string | null;
  acknowledgment_number?: string | null;
  last_completed_action?: string | null;
  last_updated: string;
}

export async function getApplicationState(
  applicationId: string
): Promise<ApplicationStateResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/application/${encodeURIComponent(applicationId)}/status`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to get application state (Status ${response.status})`);
  }

  return await response.json();
}

export async function updateApplicationStatus(
  applicationId: string,
  payload: {
    action_type: string;
    status: string;
    portal_session_id?: string | null;
    acknowledgment_number?: string | null;
    metadata?: Record<string, any>;
  }
): Promise<ApplicationStateResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/application/${encodeURIComponent(applicationId)}/status`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to update application status (Status ${response.status})`);
  }

  return await response.json();
}
