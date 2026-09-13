import React, { useEffect, useState } from 'react';
import { CitizenProfileCreatePayload, CitizenProfileResponse } from '../api/client';

interface ProfileFormProps {
  onSubmit: (payload: CitizenProfileCreatePayload) => void;
  isLoading: boolean;
  serverError: string | null;
  initialData?: CitizenProfileResponse | null;
  isUpdateMode?: boolean;
  onCancel?: () => void;
}

const INDIAN_STATES = [
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
  'Delhi',
];

const ANDHRA_PRADESH_DISTRICTS = [
  'Alluri Sitharama Raju',
  'Anakapalli',
  'Ananthapuramu',
  'Annamayya',
  'Bapatla',
  'Chittoor',
  'Dr. B.R. Ambedkar Konaseema',
  'East Godavari',
  'Eluru',
  'Guntur',
  'Kakinada',
  'Krishna',
  'Kurnool',
  'Nandyal',
  'NTR',
  'Palnadu',
  'Parvathipuram Manyam',
  'Prakasam',
  'Sri Potti Sriramulu Nellore',
  'Sri Sathya Sai',
  'Srikakulam',
  'Tirupati',
  'Visakhapatnam',
  'Vizianagaram',
  'West Godavari',
  'YSR Kadapa',
];

const WEST_BENGAL_DISTRICTS = [
  'Alipurduar',
  'Bankura',
  'Birbhum',
  'Cooch Behar',
  'Dakshin Dinajpur',
  'Darjeeling',
  'Hooghly',
  'Howrah',
  'Jalpaiguri',
  'Jhargram',
  'Kalimpong',
  'Kolkata',
  'Malda',
  'Murshidabad',
  'Nadia',
  'North 24 Parganas',
  'Paschim Bardhaman',
  'Paschim Medinipur',
  'Purba Bardhaman',
  'Purba Medinipur',
  'Purulia',
  'South 24 Parganas',
  'Uttar Dinajpur',
];

const getDistrictsForState = (state: string): string[] | null => {
  if (state === 'Andhra Pradesh') return ANDHRA_PRADESH_DISTRICTS;
  if (state === 'West Bengal') return WEST_BENGAL_DISTRICTS;
  return null;
};

export const ProfileForm: React.FC<ProfileFormProps> = ({
  onSubmit,
  isLoading,
  serverError,
  initialData,
  isUpdateMode = false,
  onCancel,
}) => {
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    age: initialData?.age !== undefined ? String(initialData.age) : '',
    gender: initialData?.gender || '',
    state: initialData?.state || '',
    district: initialData?.district || '',
  });

  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        age: initialData.age !== undefined ? String(initialData.age) : '',
        gender: initialData.gender || '',
        state: initialData.state || '',
        district: initialData.district || '',
      });
    }
  }, [initialData]);

  const validate = () => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Full Name is required';
    }
    
    const ageNum = parseInt(formData.age, 10);
    if (!formData.age || isNaN(ageNum) || ageNum <= 0 || ageNum > 120) {
      newErrors.age = 'Age must be a valid positive integer between 1 and 120';
    }

    if (!formData.gender.trim()) {
      newErrors.gender = 'Gender selection is required';
    }

    if (!formData.state.trim()) {
      newErrors.state = 'State selection is required';
    }

    if (!formData.district.trim()) {
      newErrors.district = 'District is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit({
        name: formData.name.trim(),
        age: parseInt(formData.age, 10),
        gender: formData.gender.trim(),
        state: formData.state.trim(),
        district: formData.district.trim(),
      });
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const updated = { ...prev, [name]: value };
      if (name === 'state') {
        const districts = getDistrictsForState(value);
        if (districts && !districts.includes(prev.district)) {
          updated.district = '';
        }
      }
      return updated;
    });
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const availableDistricts = getDistrictsForState(formData.state);

  return (
    <form className="profile-form" onSubmit={handleSubmit} noValidate>
      <h2>{isUpdateMode ? 'Update Citizen Profile' : 'Citizen Profile Registration'}</h2>
      <p className="form-description">
        {isUpdateMode
          ? 'Update your demographic details to recalculate your eligible welfare schemes.'
          : 'Provide your basic profile details to discover applicable central and state schemes.'}
      </p>

      {serverError && (
        <div className="form-alert error-alert">
          <strong>Error:</strong> {serverError}
        </div>
      )}

      <div className="form-group">
        <label htmlFor="name">Full Name <span className="required">*</span></label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="e.g. Ramesh Kumar"
          className={errors.name ? 'input-error' : ''}
        />
        {errors.name && <span className="field-error">{errors.name}</span>}
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="age">Age <span className="required">*</span></label>
          <input
            type="number"
            id="age"
            name="age"
            value={formData.age}
            onChange={handleChange}
            placeholder="e.g. 45"
            min="1"
            max="120"
            className={errors.age ? 'input-error' : ''}
          />
          {errors.age && <span className="field-error">{errors.age}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="gender">Gender <span className="required">*</span></label>
          <select
            id="gender"
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            className={errors.gender ? 'input-error' : ''}
          >
            <option value="">Select Gender</option>
            <option value="Female">Female</option>
            <option value="Male">Male</option>
            <option value="Other">Other</option>
            <option value="Prefer not to say">Prefer not to say</option>
          </select>
          {errors.gender && <span className="field-error">{errors.gender}</span>}
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="state">State of Residence <span className="required">*</span></label>
          <select
            id="state"
            name="state"
            value={formData.state}
            onChange={handleChange}
            className={errors.state ? 'input-error' : ''}
          >
            <option value="">Select State</option>
            {INDIAN_STATES.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
          {errors.state && <span className="field-error">{errors.state}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="district">District <span className="required">*</span></label>
          {availableDistricts ? (
            <select
              id="district"
              name="district"
              value={formData.district}
              onChange={handleChange}
              className={errors.district ? 'input-error' : ''}
            >
              <option value="">Select Official District</option>
              {availableDistricts.map((dist) => (
                <option key={dist} value={dist}>
                  {dist}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              id="district"
              name="district"
              value={formData.district}
              onChange={handleChange}
              placeholder={formData.state ? 'Enter District Name' : 'Select State first'}
              className={errors.district ? 'input-error' : ''}
            />
          )}
          {errors.district && <span className="field-error">{errors.district}</span>}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', alignItems: 'center' }}>
        <button type="submit" className="submit-btn" disabled={isLoading} style={{ flex: 1 }}>
          {isLoading
            ? 'Processing Profile & Discovering Schemes...'
            : isUpdateMode
            ? 'Save & Refresh Schemes'
            : 'Find Applicable Schemes'}
        </button>
        {isUpdateMode && onCancel && (
          <button
            type="button"
            className="secondary-btn"
            onClick={onCancel}
            style={{ padding: '0.75rem 1.25rem' }}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
};
