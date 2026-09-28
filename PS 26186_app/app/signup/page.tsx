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
    <div 
      className="flex flex-col min-h-screen text-mb-text-primary p-5 py-10 bg-cover bg-center bg-no-repeat absolute inset-0 z-20 overflow-y-auto"
      style={{ backgroundImage: "url('/login-bg.png')" }}
    >
      <div className="max-w-md w-full mx-auto space-y-6">
        {/* Back to Login link */}
        <Link
          href="/login"
          className="inline-flex items-center space-x-1.5 text-xs text-mb-text-secondary hover:text-mb-text-primary font-semibold transition-colors bg-white/30 px-3 py-1.5 rounded-lg border border-gray-300 backdrop-blur-md"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Sign In</span>
        </Link>

        {/* Header */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="w-32 h-32 mb-4 drop-shadow-xl flex items-center justify-center">
            <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-contain" />
          </div>
          <h1 className="text-2xl font-bold text-mb-text-primary tracking-wider">ManoBal</h1>
          <p className="text-xs text-mb-text-primary uppercase tracking-widest font-mono mt-1 font-semibold">
            Jawan Self-Registration
          </p>
          <p className="text-xs text-mb-text-primary mt-1 font-medium">
            Enroll in personal operational wellness and stress telemetry monitoring
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-red-950/80 border border-red-800/80 rounded-lg text-xs text-red-200 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-mb-danger shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
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
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg pl-10 pr-3 py-2.5 outline-none transition-colors shadow-sm placeholder:text-gray-400"
                required
              />
            </div>
          </div>

          {/* Grid: Username & Personnel Code */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
                Service Username *
              </label>
              <input
                id="jawan-username-input"
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="e.g. jawan_rajesh"
                disabled={loading}
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm placeholder:text-gray-400"
                required
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
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
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm placeholder:text-gray-400 font-mono uppercase font-medium"
                required
              />
            </div>
          </div>

          {/* Grid: Password & Confirm */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
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
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm placeholder:text-gray-400"
                required
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
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
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm placeholder:text-gray-400"
                required
              />
            </div>
          </div>

          {/* Grid: Age & Gender */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
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
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm"
                required
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
                Gender *
              </label>
              <select
                id="jawan-gender-select"
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                disabled={loading}
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm"
              >
                <option value="Male" className="bg-white text-gray-900">Male</option>
                <option value="Female" className="bg-white text-gray-900">Female</option>
                <option value="Other" className="bg-white text-gray-900">Other</option>
              </select>
            </div>
          </div>

          {/* Grid: Department & Job Role */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
                Department *
              </label>
              <select
                id="jawan-department-select"
                name="department"
                value={formData.department}
                onChange={handleChange}
                disabled={loading}
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm"
              >
                <option value="Operations" className="bg-white text-gray-900">Operations</option>
                <option value="Engineering" className="bg-white text-gray-900">Engineering</option>
                <option value="HR" className="bg-white text-gray-900">HR</option>
                <option value="Marketing" className="bg-white text-gray-900">Marketing</option>
                <option value="General Duty" className="bg-white text-gray-900">General Duty</option>
                <option value="Signals" className="bg-white text-gray-900">Signals</option>
                <option value="Logistics" className="bg-white text-gray-900">Logistics</option>
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
                Duty Role / Rank *
              </label>
              <select
                id="jawan-role-select"
                name="job_role"
                value={formData.job_role}
                onChange={handleChange}
                disabled={loading}
                className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm"
              >
                <option value="Constable" className="bg-white text-gray-900">Constable</option>
                <option value="Head Constable" className="bg-white text-gray-900">Head Constable</option>
                <option value="Assistant Sub-Inspector" className="bg-white text-gray-900">Assistant Sub-Inspector</option>
                <option value="Sub-Inspector" className="bg-white text-gray-900">Sub-Inspector</option>
                <option value="Inspector" className="bg-white text-gray-900">Inspector</option>
                <option value="Field Operative" className="bg-white text-gray-900">Field Operative</option>
              </select>
            </div>
          </div>

          {/* Organizational Scope Section */}
          <div className="pt-2 border-t border-gray-300 space-y-3">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-teal-300 uppercase tracking-wider ">
              <Building2 className="w-3.5 h-3.5" />
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
                <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1 ">
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
                  className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg px-3 py-2.5 outline-none transition-colors shadow-sm"
                  required
                />
              </div>
            </div>
          </div>

          {/* Role Policy Notice */}
          <div className="p-2.5 bg-white/40 rounded-lg border border-gray-300 text-[11px] text-mb-text-secondary flex items-center space-x-2">
            <BadgeCheck className="w-4 h-4 text-teal-400 shrink-0" />
            <span>
              Enrolled automatically in the <strong className="text-teal-300">Personnel</strong> tier with self-reporting access. Scope is permanent and verified by unit commanders.
            </span>
          </div>

          {/* Submit Button */}
          <Button
            id="jawan-signup-button"
            type="submit"
            disabled={loading}
            className="w-full bg-mb-accent hover:bg-mb-accent/90 text-mb-text-dark font-bold py-3 rounded-lg shadow-lg shadow-teal-500/20 transition-all mt-2 text-sm"
          >
            {loading ? 'Creating Account & Enrolling...' : 'Sign Up for ManoBal'}
          </Button>
        </form>

        {/* Existing account link */}
        <div className="text-center pb-6">
          <p className="text-xs text-mb-text-secondary font-medium ">
            Already have an active service account?{' '}
            <Link href="/login" className="text-teal-300 hover:text-teal-200 underline font-bold">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}




