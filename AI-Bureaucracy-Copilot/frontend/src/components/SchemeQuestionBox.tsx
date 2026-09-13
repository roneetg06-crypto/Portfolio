import React, { useState } from 'react';
import { askKnowledgeAgent, KnowledgeAskResponse } from '../api/client';

interface SchemeQuestionBoxProps {
  state: string;
  sector?: string;
}

export const SchemeQuestionBox: React.FC<SchemeQuestionBoxProps> = ({
  state,
  sector,
}) => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<KnowledgeAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await askKnowledgeAgent({
        question: question.trim(),
        state,
        ...(sector ? { sector } : {}),
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to answer question.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!loading && question.trim()) {
        handleAsk(e);
      }
    }
  };

  const sampleQueries = [
    'Am I eligible for PM-KISAN installment?',
    'What documents are needed for Student Education Loan?',
    'How do I check my Aadhaar DBT link status?',
  ];

  return (
    <div className="question-box-card">
      <div className="question-box-header">
        <div className="question-box-badge-row">
          <span className="ai-agent-chip">
            <span className="pulse-dot"></span> AI Copilot Knowledge Agent
          </span>
          <span className="agent-state-pill">📍 {state} Schemes & Rules</span>
        </div>
        <h3>Ask JanSevaAI Knowledge Assistant</h3>
        <p>
          Ask questions in plain English or Hindi regarding scheme eligibility, financial assistance, required certificates, or DBT bank seeding.
        </p>
      </div>

      <div className="sample-prompts-row">
        <span className="sample-prompt-label">Try asking:</span>
        {sampleQueries.map((query, idx) => (
          <button
            key={idx}
            type="button"
            className="sample-prompt-btn"
            onClick={() => setQuestion(query)}
            disabled={loading}
          >
            "{query}"
          </button>
        ))}
      </div>

      <form onSubmit={handleAsk} className="question-form">
        <div className="input-row">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your welfare scheme question here... (e.g., 'What is the maximum loan amount under National Education Loan?' or press Ctrl+Enter to submit)"
            className="question-input"
            rows={3}
            disabled={loading}
          />
          <button type="submit" className="ask-btn" disabled={loading || !question.trim()}>
            {loading ? (
              <span className="btn-loading-flex">
                <span className="spinner-sm"></span> Searching...
              </span>
            ) : (
              <span>Ask AI Copilot →</span>
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="form-alert error-alert" style={{ marginTop: '1rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className={`answer-card ${result.grounded ? 'answer-grounded' : 'answer-ungrounded'}`}>
          <div className="answer-header">
            <span className={`grounded-tag ${result.grounded ? 'tag-grounded' : 'tag-unverified'}`}>
              {result.grounded ? 'Grounded AI Answer' : 'No Direct Matching Knowledge'}
            </span>
          </div>

          <p className="answer-text">{result.answer}</p>

          {/* Action Route to Official Government Portal */}
          {result.action && result.action_url && (
            <div
              className="action-route-card"
              style={{
                marginTop: '1rem',
                padding: '1rem',
                backgroundColor: '#f8fafc',
                border: '1.5px solid #2563eb',
                borderRadius: '8px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '0.5rem',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: '#1e40af',
                    letterSpacing: '0.05em',
                  }}
                >
                  🏛️ Official Portal Action Available
                </span>
                {result.requires_human_verification && (
                  <span
                    style={{
                      fontSize: '0.78rem',
                      backgroundColor: '#fef3c7',
                      color: '#92400e',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontWeight: 600,
                    }}
                  >
                    ⚠️ Requires Human Verification (CAPTCHA / OTP)
                  </span>
                )}
              </div>
              <h4 style={{ margin: '0.2rem 0 0.4rem 0', color: '#0f172a', fontSize: '1.05rem' }}>
                {result.action_title || 'Proceed to Official Portal'}
              </h4>
              <p style={{ margin: '0 0 0.8rem 0', fontSize: '0.88rem', color: '#475569' }}>
                Complete this task directly on the official Government of India portal:
              </p>
              <a
                href={result.action_url}
                target="_blank"
                rel="noopener noreferrer"
                className="action-external-btn"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '6px',
                  fontWeight: 600,
                  textDecoration: 'none',
                  fontSize: '0.9rem',
                }}
              >
                Open {result.action_title || 'Official Portal'} Page ↗
              </a>
            </div>
          )}

          {result.sources && result.sources.length > 0 && (
            <div className="answer-sources" style={{ marginTop: '1rem' }}>
              <strong>Retrieved Sources:</strong>
              <div className="source-badges-container">
                {result.sources.map((src) => (
                  <span key={src.scheme_id} className="source-badge">
                    {src.scheme_name} ({src.level})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
