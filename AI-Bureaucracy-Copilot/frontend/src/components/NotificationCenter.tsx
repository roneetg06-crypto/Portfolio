import React, { useEffect, useState } from 'react';
import {
  fetchNotifications,
  getNotificationStreamUrl,
  NotificationItem,
  resolveNotification,
  triggerTestNotification,
} from '../api/client';

interface NotificationCenterProps {
  profileId?: string;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  profileId = 'default',
}) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [permission, setPermission] = useState<NotificationPermission>(
    typeof window !== 'undefined' && 'Notification' in window
      ? Notification.permission
      : 'default'
  );
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');

  // Load existing notifications
  const loadExisting = async () => {
    try {
      const res = await fetchNotifications(profileId);
      const active = (res.notifications || []).filter((n) => n.status === 'ACTION_REQUIRED');
      setNotifications(active);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    }
  };

  useEffect(() => {
    loadExisting();
  }, [profileId]);

  // Connect to SSE stream
  useEffect(() => {
    const streamUrl = getNotificationStreamUrl(profileId);
    let eventSource: EventSource | null = null;

    try {
      eventSource = new EventSource(streamUrl);

      eventSource.addEventListener('connected', () => {
        setConnectionStatus('connected');
      });

      eventSource.addEventListener('notification', (event: MessageEvent) => {
        try {
          const notif: NotificationItem = JSON.parse(event.data);
          if (notif.status === 'ACTION_REQUIRED') {
            setNotifications((prev) => {
              // Avoid duplicates
              if (prev.some((n) => n.notification_id === notif.notification_id)) return prev;
              return [notif, ...prev];
            });
            setIsExpanded(true);

            // OS-level notification if permitted and document is hidden / backgrounded
            if ('Notification' in window && Notification.permission === 'granted') {
              try {
                new Notification(`⚠️ Citizen Action Required: ${notif.action_type}`, {
                  body: notif.message,
                  tag: notif.notification_id,
                });
              } catch (e) {
                console.warn('Browser notification error:', e);
              }
            }
          }
        } catch (e) {
          console.error('Failed to parse SSE notification message:', e);
        }
      });

      eventSource.onerror = () => {
        setConnectionStatus('error');
        // Fallback polling every 5s if SSE disconnects
      };
    } catch (err) {
      console.warn('SSE not supported or failed to connect:', err);
      setConnectionStatus('error');
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [profileId]);

  const requestPermission = async () => {
    if ('Notification' in window) {
      try {
        const result = await Notification.requestPermission();
        setPermission(result);
      } catch (err) {
        console.warn('Notification permission error:', err);
      }
    }
  };

  const handleResolve = async (notifId: string) => {
    try {
      await resolveNotification(notifId, profileId);
      setNotifications((prev) => prev.filter((n) => n.notification_id !== notifId));
    } catch (err) {
      console.error('Failed to resolve notification:', err);
    }
  };

  const handleSimulateAlert = async () => {
    setTriggering(true);
    try {
      const actions = ['LOGIN', 'CAPTCHA', 'OTP', 'FINAL_SUBMIT'];
      const randomAction = actions[Math.floor(Math.random() * actions.length)];
      await triggerTestNotification({
        profile_id: profileId,
        action_type: randomAction,
        message: `Action Required: Please complete ${randomAction} verification on the mock government portal.`,
        portal_url: 'http://localhost:5174',
      });
    } catch (err) {
      console.error('Failed to trigger simulation:', err);
    } finally {
      setTriggering(false);
    }
  };

  const activeCount = notifications.length;
  const hasUrgent = notifications.some((n) =>
    ['OTP', 'CAPTCHA', 'LOGIN', 'FINAL_SUBMIT'].includes(n.action_type)
  );

  return (
    <div className="gov-user-menu-container" style={{ position: 'relative' }}>
      {/* High-visibility Alarm Bell Button */}
      <button
        className={`notif-alarm-btn ${hasUrgent ? 'has-urgent' : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        title={activeCount > 0 ? `${activeCount} urgent action(s) required` : 'Notification Center (No alerts)'}
      >
        <span aria-hidden="true">🔔</span>
        {activeCount > 0 && (
          <span className="notif-alarm-badge" aria-label={`${activeCount} unread alerts`}>
            {activeCount > 9 ? '9+' : activeCount}
          </span>
        )}
      </button>

      {/* Priority Action Drawer */}
      {isExpanded && (
        <div className="notif-priority-drawer" role="dialog" aria-label="Urgent Citizen Actions">
          <div className="notif-priority-header">
            <h4>
              <span>⚠️ Action Required</span>
              {activeCount > 0 && <span className="notif-priority-badge">{activeCount} Pending</span>}
            </h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <button
                className="notif-sim-btn"
                onClick={handleSimulateAlert}
                disabled={triggering}
                title="Simulate action-required alert for testing"
                style={{ fontSize: '0.7rem', padding: '0.15rem 0.45rem' }}
              >
                {triggering ? '...' : '+ Test'}
              </button>
              <button
                className="notif-close-btn"
                onClick={() => setIsExpanded(false)}
                title="Close Alerts"
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.2rem',
                  cursor: 'pointer',
                  color: '#9f1239',
                  lineHeight: 1,
                  padding: '0.1rem 0.3rem',
                }}
              >
                &times;
              </button>
            </div>
          </div>

          <div style={{ padding: '0.5rem 1rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem', color: '#64748b' }}>
            <span>Stream: <strong style={{ color: connectionStatus === 'connected' ? '#16a34a' : '#eab308' }}>{connectionStatus}</strong></span>
            {permission !== 'granted' && (
              <button
                onClick={requestPermission}
                style={{ background: 'none', border: 'none', color: '#0369a1', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontSize: '0.72rem' }}
              >
                Enable Desktop Alerts
              </button>
            )}
          </div>

          {activeCount === 0 ? (
            <div style={{ padding: '1.5rem 1rem', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
              <p style={{ margin: '0 0 0.4rem 0' }}>✅ No pending citizen actions.</p>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                All automated background processes are up to date.
              </span>
            </div>
          ) : (
            <div style={{ maxHeight: '360px', overflowY: 'auto', padding: '0.75rem' }}>
              {notifications.map((notif) => {
                const isUrgent = ['OTP', 'CAPTCHA', 'LOGIN', 'FINAL_SUBMIT'].includes(notif.action_type);
                return (
                  <div
                    key={notif.notification_id}
                    className={`notif-card notif-card-priority ${isUrgent ? 'urgent-otp' : ''}`}
                    style={{
                      padding: '0.85rem',
                      marginBottom: '0.65rem',
                      borderRadius: '6px',
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                      <span
                        style={{
                          backgroundColor: isUrgent ? '#dc2626' : '#f59e0b',
                          color: '#ffffff',
                          fontWeight: 700,
                          fontSize: '0.72rem',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          letterSpacing: '0.04em',
                        }}
                      >
                        {notif.action_type}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                        {new Date(notif.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    <p style={{ margin: '0 0 0.6rem 0', fontSize: '0.84rem', color: '#1e293b', lineHeight: 1.4 }}>
                      {notif.message}
                    </p>

                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', alignItems: 'center' }}>
                      {notif.portal_url && (
                        <a
                          href={notif.portal_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            fontSize: '0.78rem',
                            color: '#0369a1',
                            fontWeight: 600,
                            textDecoration: 'none',
                            border: '1px solid #bae6fd',
                            padding: '0.25rem 0.55rem',
                            borderRadius: '4px',
                            background: '#f0f9ff',
                          }}
                        >
                          Open Portal ↗
                        </a>
                      )}
                      <button
                        onClick={() => handleResolve(notif.notification_id)}
                        style={{
                          fontSize: '0.78rem',
                          background: '#16a34a',
                          color: '#ffffff',
                          border: 'none',
                          padding: '0.25rem 0.55rem',
                          borderRadius: '4px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
