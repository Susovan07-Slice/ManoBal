'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/AuthContext';
import { Shield, Lock, User, AlertCircle, Info, BadgeCheck, ChevronLeft, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { SearchableSelect } from '@/components/ui/SearchableSelect';

// Centralized canonical fallbacks matching backend
const DEFAULT_BATTALIONS = [
  '1st Battalion',
  '2nd Battalion',
  '3rd Battalion',
  '4th Battalion',
  '5th Battalion',
  '6th Battalion',
  '7th Battalion',
  '8th Battalion',
  '9th Battalion',
  '10th Battalion',
  'Rapid Action Force (RAF)',
  'Special Duty Group (SDG)',
  'Valley QAT',
  'CoBRA 201',
  'CoBRA 205',
];

const DEFAULT_LOCATIONS = [
  'Srinagar',
  'Jammu',
  'Dantewada',
  'Sukma',
  'Ranchi',
  'Jamshedpur',
  'Delhi',
  'Bhubaneswar',
  'Guwahati',
  'Imphal',
  'Raipur',
  'Bhopal',
];

export default function JawanSignupPage() {
  const router = useRouter();
  const { user, signup } = useAuth();

  const [formData, setFormData] = useState({
    name: '',
    username: '',
    password: '',
    confirmPassword: '',
    personnel_code: '',
    age: 28,
    gender: 'Male',
    department: 'Operations',
    job_role: 'Constable',
    battalion: '7th Battalion',
    location: 'Srinagar',
    experience_years: 4.0,
  });

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      router.push('/');
    }
  }, [user, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'age' || name === 'experience_years' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validations
    if (!formData.name.trim()) {
      setError('Please provide your full name.');
      return;
    }
    if (!formData.username.trim() || formData.username.trim().length < 3) {
      setError('Service username must be at least 3 characters.');
      return;
    }
    if (!formData.personnel_code.trim()) {
      setError('Please provide a unique Personnel / Service ID (e.g. TEST-001 or PF-0100).');
      return;
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }
    if (formData.age < 18 || formData.age > 70) {
      setError('Age must be between 18 and 70.');
      return;
    }
    if (formData.experience_years < 0) {
      setError('Service experience cannot be negative.');
      return;
    }
    if (!formData.battalion) {
      setError('Please select a valid canonical Battalion.');
      return;
    }
    if (!formData.location) {
      setError('Please select a valid canonical Posting Base / Location.');
      return;
    }

    setLoading(true);
    try {
      await signup({
        name: formData.name.trim(),
        username: formData.username.trim().toLowerCase(),
        password: formData.password,
        personnel_code: formData.personnel_code.trim().toUpperCase(),
        age: Number(formData.age),
        gender: formData.gender,
        department: formData.department.trim(),
        job_role: formData.job_role.trim(),
        battalion: formData.battalion.trim(),
        location: formData.location.trim(),
        experience_years: Number(formData.experience_years),
        duty_hours_per_week: 40.0,
      });
      router.push('/assessment?reason=initial');
    } catch (err: any) {
      console.error('Registration failed:', err);
      setError(err?.message || 'Registration failed. Please check the provided information.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-[100dvh] p-5 py-10 absolute inset-0 z-20 overflow-y-auto">
      <div className="max-w-md w-full mx-auto space-y-5">
        {/* Back to Login link */}
        <Link
          href="/login"
          className="inline-flex items-center space-x-1.5 text-[12px] text-ink-2 hover:text-ink font-semibold transition-colors bg-white/70 backdrop-blur-md px-3.5 py-2 rounded-full border border-sky-200 shadow-sm"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Sign In</span>
        </Link>

        {/* Header */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="w-24 h-24 mb-4 rounded-full bg-white shadow-[0_10px_30px_rgba(31,110,140,0.15)] border-2 border-white flex items-center justify-center p-2">
            <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-contain" />
          </div>
          <h1 className="text-[26px] font-bold text-ink tracking-tight">ManoBal</h1>
          <p className="eyebrow mt-2">
            Jawan Self-Registration
          </p>
          <p className="text-[13px] text-ink-2 mt-1 font-medium">
            Enroll in personal operational wellness and stress telemetry monitoring
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 bg-alert-bg border border-alert/30 rounded-2xl text-[13px] text-ink flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-alert shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Registration Form */}
        <div className="glass-card p-5 space-y-4 animate-fade-up">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div>
            <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
              Full Name *
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                <User className="w-4 h-4" />
              </span>
              <input
                id="jawan-fullname-input"
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g. Rajesh Verma"
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl pl-11 pr-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                required
              />
            </div>
          </div>

          {/* Grid: Username & Personnel Code */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Service Username (only lowercase) *
              </label>
              <input
                id="jawan-username-input"
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="e.g. jawan_rajesh"
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                required
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Personnel ID *
              </label>
              <input
                id="jawan-code-input"
                type="text"
                name="personnel_code"
                value={formData.personnel_code}
                onChange={handleChange}
                placeholder="e.g. TEST-001"
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3 font-mono uppercase"
                required
              />
            </div>
          </div>

          {/* Grid: Password & Confirm */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Password *
              </label>
              <input
                id="jawan-password-input"
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Min 6 chars"
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                required
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Confirm Password *
              </label>
              <input
                id="jawan-confirm-password-input"
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Repeat password"
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                required
              />
            </div>
          </div>

          {/* Grid: Age & Gender */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Age *
              </label>
              <input
                id="jawan-age-input"
                type="number"
                name="age"
                min={18}
                max={70}
                value={formData.age}
                onChange={handleChange}
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                required
              />
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Gender *
              </label>
              <select
                id="jawan-gender-select"
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
              >
                <option value="Male" className="bg-white text-ink">Male</option>
                <option value="Female" className="bg-white text-ink">Female</option>
                <option value="Other" className="bg-white text-ink">Other</option>
              </select>
            </div>
          </div>

          {/* Grid: Department & Job Role */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Department *
              </label>
              <select
                id="jawan-department-select"
                name="department"
                value={formData.department}
                onChange={handleChange}
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
              >
                <option value="Operations" className="bg-white text-ink">Operations</option>
                <option value="Engineering" className="bg-white text-ink">Engineering</option>
                <option value="HR" className="bg-white text-ink">HR</option>
                <option value="Marketing" className="bg-white text-ink">Marketing</option>
                <option value="General Duty" className="bg-white text-ink">General Duty</option>
                <option value="Signals" className="bg-white text-ink">Signals</option>
                <option value="Logistics" className="bg-white text-ink">Logistics</option>
              </select>
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                Duty Role / Rank *
              </label>
              <select
                id="jawan-role-select"
                name="job_role"
                value={formData.job_role}
                onChange={handleChange}
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
              >
                <option value="Constable" className="bg-white text-ink">Constable</option>
                <option value="Head Constable" className="bg-white text-ink">Head Constable</option>
                <option value="Assistant Sub-Inspector" className="bg-white text-ink">Assistant Sub-Inspector</option>
                <option value="Sub-Inspector" className="bg-white text-ink">Sub-Inspector</option>
                <option value="Inspector" className="bg-white text-ink">Inspector</option>
                <option value="Field Operative" className="bg-white text-ink">Field Operative</option>
              </select>
            </div>
          </div>

          {/* Organizational Scope Section */}
          <div className="pt-2 border-t border-sky-200/50 space-y-3">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-brand-600 uppercase tracking-wider">
              <Building2 className="w-3.5 h-3.5 text-brand-500" />
              <span>Unit & Posting Assignment</span>
            </div>

            {/* Battalion Combobox */}
            <SearchableSelect
              id="jawan-battalion-select"
              label="Assigned Battalion"
              value={formData.battalion}
              onChange={(val) => setFormData((prev) => ({ ...prev, battalion: val }))}
              options={DEFAULT_BATTALIONS}
              endpoint="/organizations/battalions"
              placeholder="Search / Select Battalion"
              disabled={loading}
              required
            />

            {/* Grid: Location & Experience */}
            <div className="grid grid-cols-2 gap-3">
              <SearchableSelect
                id="jawan-location-select"
                label="Posting Location"
                value={formData.location}
                onChange={(val) => setFormData((prev) => ({ ...prev, location: val }))}
                options={DEFAULT_LOCATIONS}
                endpoint="/organizations/locations"
                placeholder="Search / Select Location"
                disabled={loading}
                required
              />

              <div>
                <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
                  Experience (Yrs) *
                </label>
                <input
                  id="jawan-exp-input"
                  type="number"
                  step="0.5"
                  min="0"
                  max="50"
                  name="experience_years"
                  value={formData.experience_years}
                  onChange={handleChange}
                  disabled={loading}
                  className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl px-4 h-[48px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                  required
                />
              </div>
            </div>
          </div>

          {/* Role Policy Notice */}
          <div className="p-3 bg-brand-100 rounded-2xl border border-brand-500/20 text-[12px] text-ink-2 flex items-center space-x-2.5">
            <BadgeCheck className="w-4 h-4 text-brand-500 shrink-0" />
            <span>
              Enrolled automatically in the <strong className="text-brand-600">Personnel</strong> tier with self-reporting access. Scope is permanent and verified by unit commanders.
            </span>
          </div>

          {/* Submit Button */}
          <Button
            id="jawan-signup-button"
            type="submit"
            disabled={loading}
            className="w-full mt-2"
          >
            {loading ? 'Creating Account & Enrolling...' : 'Sign Up for ManoBal'}
          </Button>
        </form>
        </div>

        {/* Existing account link */}
        <div className="text-center pb-6">
          <p className="text-[13px] text-ink-2">
            Already have an active service account?{' '}
            <Link href="/login" className="text-brand-500 hover:text-brand-600 underline font-bold">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}




