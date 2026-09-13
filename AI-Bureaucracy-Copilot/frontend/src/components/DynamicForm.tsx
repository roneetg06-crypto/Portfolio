import React, { useState } from 'react';
import { CitizenProfileResponse, RequiredInfoField } from '../api/client';

interface DynamicFormProps {
  fields: RequiredInfoField[];
  profile?: CitizenProfileResponse;
  onSubmit: (values: Record<string, any>) => void;
  isLoading: boolean;
  serverError?: string | null;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({
  fields,
  profile,
  onSubmit,
  isLoading,
  serverError,
}) => {
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {};
    fields.forEach((f) => {
      if (f.type === 'checkbox' || f.type === 'boolean') {
        initial[f.name] = false;
      } else {
        initial[f.name] = '';
      }
    });

    // Auto-prefill matching fields from citizen profile if available
    if (profile) {
      if ('student_name' in initial && profile.name) initial['student_name'] = profile.name;
      if ('gender' in initial && profile.gender) initial['gender'] = profile.gender;
      if ('state' in initial && profile.state) initial['state'] = profile.state;
      if ('district' in initial && profile.district) initial['district'] = profile.district;
      if ('date_of_birth' in initial && profile.age) {
        const estYear = new Date().getFullYear() - Number(profile.age);
        initial['date_of_birth'] = `${estYear}-05-15`;
      }
    }

    return initial;
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handlePreFillDemo = () => {
    const estYear = profile?.age ? new Date().getFullYear() - Number(profile.age) : 2003;
    const demoData: Record<string, any> = {
      student_name: profile?.name || 'Priya Sharma',
      date_of_birth: `${estYear}-05-15`,
      gender: profile?.gender || 'Female',
      state: profile?.state || 'Andhra Pradesh',
      district: profile?.district || 'Visakhapatnam',
      category: 'OBC',
      parent_name: 'Ramesh Sharma',
      parent_occupation: 'Salaried / Private',
      annual_family_income: 350000,
      aadhaar_last_four: '5821',
      course: 'B.Tech Computer Science and Engineering',
      college: 'National Institute of Technology',
      loan_amount: 750000,
      tuition_fee: 500000,
      living_expenses: 250000,
      bank_preference: 'State Bank of India',
      loan_tenure: '10 Years',
    };

    setFormData((prev) => {
      const updated = { ...prev };
      fields.forEach((f) => {
        if (demoData[f.name] !== undefined) {
          updated[f.name] = demoData[f.name];
        }
      });
      return updated;
    });
    setErrors({});
  };

  const handleChange = (name: string, value: any) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    fields.forEach((field) => {
      const val = formData[field.name];

      if (field.required) {
        if (field.type === 'checkbox') {
          if (!val) {
            newErrors[field.name] = 'You must accept / confirm this requirement.';
          }
        } else if (field.type === 'boolean') {
          if (val === undefined || val === null) {
            newErrors[field.name] = `${field.label} is required.`;
          }
        } else if (val === undefined || val === null || String(val).trim() === '') {
          newErrors[field.name] = `${field.label} is required.`;
        }
      }

      if (val !== undefined && val !== null && String(val).trim() !== '') {
        if (field.type === 'number') {
          const num = Number(val);
          if (isNaN(num)) {
            newErrors[field.name] = 'Must be a valid number.';
          }
        } else if (field.type === 'date') {
          if (!/^\d{4}-\d{2}-\d{2}$/.test(String(val).trim())) {
            newErrors[field.name] = 'Date must be in YYYY-MM-DD format.';
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  if (fields.length === 0) {
    return (
      <div className="dynamic-form-empty">
        <p>No additional information required for this scheme.</p>
      </div>
    );
  }

  return (
    <form className="dynamic-form" onSubmit={handleSubmit} noValidate>
      {serverError && (
        <div className="form-alert error-alert">
          <strong>Error:</strong> {serverError}
        </div>
      )}

      {/* 1-Click Pre-fill Demo Data Helper */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.75rem 1rem',
        background: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: '6px',
        marginBottom: '1.25rem',
        gap: '0.6rem',
        flexWrap: 'wrap',
      }}>
        <div style={{ fontSize: '0.86rem', color: '#1e40af' }}>
          ⚡ <strong>1-Click Pre-fill:</strong> Populate mapped student & demo loan details for fast testing.
        </div>
        <button
          type="button"
          onClick={handlePreFillDemo}
          style={{
            background: '#2563eb',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            padding: '0.45rem 0.9rem',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'background 0.2s ease',
          }}
          title="Auto-fills valid student, parent, and loan test data"
        >
          ⚡ Pre-fill Demo Details
        </button>
      </div>

      {fields.map((field) => {
        const hasError = !!errors[field.name];
        return (
          <div key={field.name} className={`form-group ${hasError ? 'group-error' : ''}`}>
            <label htmlFor={field.name}>
              {field.label} {field.required && <span className="required">*</span>}
            </label>

            {field.type === 'text' && (
              <input
                type="text"
                id={field.name}
                value={formData[field.name] || ''}
                onChange={(e) => handleChange(field.name, e.target.value)}
                placeholder={field.help_text || `Enter ${field.label}`}
                className={hasError ? 'input-error' : ''}
              />
            )}

            {field.type === 'number' && (
              <input
                type="number"
                id={field.name}
                value={formData[field.name] || ''}
                onChange={(e) => handleChange(field.name, e.target.value)}
                placeholder={field.help_text || `Enter ${field.label}`}
                className={hasError ? 'input-error' : ''}
              />
            )}

            {field.type === 'date' && (
              <input
                type="date"
                id={field.name}
                value={formData[field.name] || ''}
                onChange={(e) => handleChange(field.name, e.target.value)}
                className={hasError ? 'input-error' : ''}
              />
            )}

            {(field.type === 'dropdown' || field.type === 'select') && (
              <select
                id={field.name}
                value={formData[field.name] || ''}
                onChange={(e) => handleChange(field.name, e.target.value)}
                className={hasError ? 'input-error' : ''}
              >
                <option value="">Select option...</option>
                {field.options?.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            )}

            {field.type === 'radio' && (
              <div className="radio-group">
                {field.options?.map((opt) => (
                  <label key={opt} className="radio-label">
                    <input
                      type="radio"
                      name={field.name}
                      value={opt}
                      checked={formData[field.name] === opt}
                      onChange={(e) => handleChange(field.name, e.target.value)}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}

            {(field.type === 'checkbox' || field.type === 'boolean') && (
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={!!formData[field.name]}
                  onChange={(e) => handleChange(field.name, e.target.checked)}
                />
                <span>{field.help_text || field.label}</span>
              </label>
            )}

            {field.help_text && field.type !== 'checkbox' && field.type !== 'boolean' && (
              <span className="field-help">{field.help_text}</span>
            )}

            {errors[field.name] && <span className="field-error">{errors[field.name]}</span>}
          </div>
        );
      })}

      <button type="submit" className="submit-btn" disabled={isLoading}>
        {isLoading ? 'Saving Information...' : 'Submit Additional Information & Proceed'}
      </button>
    </form>
  );
};
