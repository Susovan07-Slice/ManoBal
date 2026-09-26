'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/AuthContext';
import { ShieldAlert, Lock, User, AlertCircle, Info, ChevronLeft, Building2, MapPin } from 'lucide-react';
import { SearchableSelect } from '@/components/ui/SearchableSelect';

// Centralized default options for fallbacks
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

export default function CommanderSignupPage() {
  const router = useRouter();
  const { user, signupCommander } = useAuth();

  const [formData, setFormData] = useState({
    name: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    battalion: '7th Battalion',
    location: 'Srinagar',
  });

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validations
    if (!formData.name.trim()) {
      setError('Please provide your full military name and title.');
      return;
    }
    if (!formData.username.trim() || formData.username.trim().length < 3) {
      setError('Service username must be at least 3 characters.');
      return;
    }
    if (!formData.password || formData.password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match. Please verify your entries.');
      return;
    }
    if (!formData.battalion) {
      setError('Please select a valid canonical Battalion.');
      return;
    }
    if (!formData.location) {
      setError('Please select a valid canonical Posting Location.');
      return;
    }

    setIsLoading(true);
    try {
      await signupCommander({
        name: formData.name.trim(),
        username: formData.username.trim().toLowerCase(),
        email: formData.email.trim() || undefined,
        password: formData.password,
        battalion: formData.battalion,
        location: formData.location,
      });
      router.push('/dashboard');
    } catch (err: any) {
      console.error('Commander registration error:', err);
      setError(err?.message || 'Registration failed. Please check your information and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4 py-8">
      {/* Back to Login */}
      <div className="max-w-lg w-full mb-3">
        <Link
          href="/login"
          className="inline-flex items-center space-x-1.5 text-xs text-textSecondary hover:text-accent transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Command Portal Sign In</span>
        </Link>
      </div>

      {/* Prototype Disclaimer Banner */}
      <div className="max-w-lg w-full mb-5 p-3 bg-surfaceHighlight/60 border border-military rounded text-xs text-textSecondary flex items-start space-x-2">
        <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
        <p>
          <strong className="text-textPrimary">Prototype Commander Registration:</strong> This registration flow is provided for research prototyping and access-control demonstration. Selecting a Battalion and Location associates your officer account with that organizational unit. In accordance with system security rules, you will strictly access personnel, assessments, telemetry, and welfare requests within your assigned unit.
        </p>
      </div>

      <div className="max-w-lg w-full bg-surface border border-surfaceHighlight rounded-lg shadow-card p-8">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 bg-accent/20 rounded-full flex items-center justify-center mb-3 border border-accent/40">
            <ShieldAlert className="w-6 h-6 text-accent" />
          </div>
          <h1 className="text-2xl font-bold text-textPrimary uppercase tracking-wider">ManoBal</h1>
          <p className="text-xs text-textSecondary uppercase tracking-widest font-mono mt-1">
            Officer & Commander Registration
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-900/30 border border-red-700/50 rounded flex items-center space-x-2 text-sm text-red-200">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
              Full Officer Name *
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-textSecondary">
                <User className="w-4 h-4" />
              </span>
              <input
                id="commander-name-input"
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g. Major R. K. Sharma"
                disabled={isLoading}
                className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-textPrimary text-sm rounded pl-10 pr-3 py-2.5 outline-none transition-colors"
                required
              />
            </div>
          </div>

          {/* Grid: Username & Email */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
                Service Username *
              </label>
              <input
                id="commander-username-input"
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="e.g. cmda_sharma"
                disabled={isLoading}
                className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-textPrimary text-sm rounded px-3 py-2.5 outline-none transition-colors font-mono"
                required
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
                Official Email (Optional)
              </label>
              <input
                id="commander-email-input"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="officer@crpf.gov.in"
                disabled={isLoading}
                className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-textPrimary text-sm rounded px-3 py-2.5 outline-none transition-colors"
              />
            </div>
          </div>

          {/* Grid: Password & Confirm */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
                Password *
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-textSecondary">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  id="commander-password-input"
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Min 6 characters"
                  disabled={isLoading}
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-textPrimary text-sm rounded pl-10 pr-3 py-2.5 outline-none transition-colors"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
                Confirm Password *
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-textSecondary">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  id="commander-confirm-password-input"
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Repeat password"
                  disabled={isLoading}
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-textPrimary text-sm rounded pl-10 pr-3 py-2.5 outline-none transition-colors"
                  required
                />
              </div>
            </div>
          </div>

          {/* Organizational Scope Section */}
          <div className="pt-2 border-t border-surfaceHighlight/60 space-y-3">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-accent uppercase tracking-wider">
              <Building2 className="w-3.5 h-3.5" />
              <span>Assigned Command Scope</span>
            </div>

            {/* Battalion Combobox */}
            <SearchableSelect
              id="battalion-select"
              label="Battalion Assignment"
              value={formData.battalion}
              onChange={(val) => setFormData((prev) => ({ ...prev, battalion: val }))}
              options={DEFAULT_BATTALIONS}
              endpoint="/organizations/battalions"
              placeholder="Search / Select Battalion"
              disabled={isLoading}
              required
            />

            {/* Location Combobox */}
            <SearchableSelect
              id="location-select"
              label="Command Location / Base"
              value={formData.location}
              onChange={(val) => setFormData((prev) => ({ ...prev, location: val }))}
              options={DEFAULT_LOCATIONS}
              endpoint="/organizations/locations"
              placeholder="Search / Select Location"
              disabled={isLoading}
              required
            />
          </div>

          {/* Security Notice */}
          <div className="p-2.5 bg-surfaceHighlight/40 rounded border border-surfaceHighlight text-[11px] text-textSecondary">
            <span>
              Role is automatically locked to <strong className="text-accent">Officer / Commander</strong>. Access to personnel, stress levels, and welfare alerts is permanently restricted to your selected Battalion & Location.
            </span>
          </div>

          <button
            id="commander-signup-button"
            type="submit"
            disabled={isLoading}
            className="w-full mt-4 bg-accent hover:bg-accent/80 text-white font-medium py-2.5 px-4 rounded text-sm transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Registering Command Authority...</span>
              </>
            ) : (
              <span>Register & Enter Command Center</span>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-surfaceHighlight text-center">
          <p className="text-xs text-textSecondary">
            Already have an officer account?{' '}
            <Link href="/login" className="text-accent hover:underline font-semibold">
              Sign In to Command Center
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
