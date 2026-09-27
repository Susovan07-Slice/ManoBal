'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/lib/AuthContext';
import { ShieldAlert, Lock, User, AlertCircle, Info, ChevronDown, Building2, ShieldCheck, Mail } from 'lucide-react';
import { SearchableSelect } from '@/components/ui/SearchableSelect';
import armyInsignia from '@/public/army_insignia.jpg';

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

  const [roleType, setRoleType] = useState<'commander' | 'welfare'>('commander');
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
    <div className="min-h-screen bg-[#070b09] flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 relative selection:bg-emerald-800 selection:text-white">
      {/* Ambient background glow */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-950/40 rounded-full blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-950/30 rounded-full blur-3xl pointer-events-none translate-x-1/2 translate-y-1/2" />

      {/* Main Split Container */}
      <div className="relative z-10 max-w-4xl w-full bg-white rounded-3xl shadow-2xl overflow-hidden grid grid-cols-1 md:grid-cols-2 border border-emerald-950/20 my-6">
        
        {/* Left Side: Indian Army Insignia Hero Panel (matching Image 1 layout with Image 2) */}
        <div className="relative bg-black p-6 sm:p-8 md:p-10 flex flex-col justify-between overflow-hidden border-b md:border-b-0 md:border-r border-black">
          {/* Top Brand Watermark */}
          <div className="relative z-10 flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-700/40 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-widest font-bold text-emerald-400">ManoBal</span>
              <span className="text-[10px] text-gray-400 block tracking-wider uppercase font-mono">Command Enlistment</span>
            </div>
          </div>

          {/* Center: Image 2 (Indian Army Insignia on seamless pure black) */}
          <div className="relative z-10 my-auto py-6 flex flex-col items-center justify-center">
            <div
              className="relative w-48 h-60 sm:w-56 sm:h-72 transition-transform duration-500 hover:scale-105"
              style={{ position: 'relative', width: '220px', height: '280px', maxWidth: '100%' }}
            >
              <Image
                src={armyInsignia}
                alt="Indian Army Insignia - भारतीय सेना"
                fill
                priority
                sizes="(max-width: 768px) 192px, 224px"
                className="object-contain mix-blend-screen"
                style={{ objectFit: 'contain' }}
              />
            </div>
          </div>

          {/* Bottom Heading & Subtext (matching typography of "Create your Free Account" in Image 1) */}
          <div className="relative z-10 mt-auto">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Create your <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-200 via-white to-teal-200">
                Officer Account
              </span>
            </h1>
            <p className="text-gray-300 text-xs sm:text-sm mt-3 font-normal leading-relaxed">
              Register unit authority to access personnel psychological assessment telemetry, predictive risk monitoring, and welfare pipelines.
            </p>
          </div>
        </div>

        {/* Right Side: Clean Form Panel (matching Image 1 right column) */}
        <div className="bg-white p-6 sm:p-8 md:p-10 flex flex-col justify-between">
          <div>
            {/* Top Bar: Language / Region Selector */}
            <div className="flex justify-end mb-2">
              <div className="inline-flex items-center space-x-1 text-xs text-gray-500 font-medium cursor-pointer hover:text-gray-800 transition-colors">
                <span>Restricted (IND)</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Header */}
            <div className="mb-4">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900">
                Sign up
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Already have an account?{' '}
                <Link href="/login" className="text-emerald-700 font-semibold hover:underline">
                  Sign In
                </Link>
              </p>
            </div>

            {/* Role Pills (matching the radio pill selectors from Image 1) */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <button
                type="button"
                onClick={() => setRoleType('commander')}
                className={`flex items-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  roleType === 'commander'
                    ? 'border-emerald-600 bg-emerald-50/70 text-emerald-950 ring-2 ring-emerald-600/15'
                    : 'border-gray-200 bg-gray-50/50 text-gray-700 hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    roleType === 'commander'
                      ? 'border-emerald-700 bg-emerald-700'
                      : 'border-gray-300 bg-white'
                  }`}
                >
                  {roleType === 'commander' && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </span>
                <span className="font-semibold truncate">Commander</span>
              </button>

              <button
                type="button"
                onClick={() => setRoleType('welfare')}
                className={`flex items-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  roleType === 'welfare'
                    ? 'border-emerald-600 bg-emerald-50/70 text-emerald-950 ring-2 ring-emerald-600/15'
                    : 'border-gray-200 bg-gray-50/50 text-gray-700 hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    roleType === 'welfare'
                      ? 'border-emerald-700 bg-emerald-700'
                      : 'border-gray-300 bg-white'
                  }`}
                >
                  {roleType === 'welfare' && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </span>
                <span className="font-semibold truncate">Welfare Officer</span>
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center space-x-2 text-xs text-red-700">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {/* Full Name */}
              <div>
                <label className="block text-xs uppercase tracking-wider text-gray-600 font-semibold mb-1">
                  Full Officer Name *
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
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
                    className="w-full bg-gray-50/70 border border-gray-200 focus:bg-white focus:border-emerald-600 focus:ring-4 focus:ring-emerald-600/10 text-gray-900 text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-gray-400"
                    required
                  />
                </div>
              </div>

              {/* Grid: Username & Email */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs uppercase tracking-wider text-gray-600 font-semibold mb-1">
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
                    className="w-full bg-gray-50/70 border border-gray-200 focus:bg-white focus:border-emerald-600 focus:ring-4 focus:ring-emerald-600/10 text-gray-900 text-sm rounded-xl px-3.5 py-2.5 outline-none transition-all font-mono placeholder:text-gray-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-gray-600 font-semibold mb-1">
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
                    className="w-full bg-gray-50/70 border border-gray-200 focus:bg-white focus:border-emerald-600 focus:ring-4 focus:ring-emerald-600/10 text-gray-900 text-sm rounded-xl px-3.5 py-2.5 outline-none transition-all placeholder:text-gray-400"
                  />
                </div>
              </div>

              {/* Grid: Password & Confirm */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs uppercase tracking-wider text-gray-600 font-semibold mb-1">
                    Password *
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                      <Lock className="w-4 h-4" />
                    </span>
                    <input
                      id="commander-password-input"
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Min 6 chars"
                      disabled={isLoading}
                      className="w-full bg-gray-50/70 border border-gray-200 focus:bg-white focus:border-emerald-600 focus:ring-4 focus:ring-emerald-600/10 text-gray-900 text-sm rounded-xl pl-10 pr-3.5 py-2.5 outline-none transition-all placeholder:text-gray-400"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-gray-600 font-semibold mb-1">
                    Confirm Password *
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
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
                      className="w-full bg-gray-50/70 border border-gray-200 focus:bg-white focus:border-emerald-600 focus:ring-4 focus:ring-emerald-600/10 text-gray-900 text-sm rounded-xl pl-10 pr-3.5 py-2.5 outline-none transition-all placeholder:text-gray-400"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Organizational Scope Section */}
              <div className="pt-2 border-t border-gray-100 space-y-2">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-emerald-800 uppercase tracking-wider">
                  <Building2 className="w-3.5 h-3.5" />
                  <span>Assigned Command Scope</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Battalion Combobox */}
                  <SearchableSelect
                    id="battalion-select"
                    label="Battalion Assignment"
                    value={formData.battalion}
                    onChange={(val) => setFormData((prev) => ({ ...prev, battalion: val }))}
                    options={DEFAULT_BATTALIONS}
                    endpoint="/organizations/battalions"
                    placeholder="Search Battalion"
                    disabled={isLoading}
                    required
                    variant="light"
                  />

                  {/* Location Combobox */}
                  <SearchableSelect
                    id="location-select"
                    label="Command Location"
                    value={formData.location}
                    onChange={(val) => setFormData((prev) => ({ ...prev, location: val }))}
                    options={DEFAULT_LOCATIONS}
                    endpoint="/organizations/locations"
                    placeholder="Search Location"
                    disabled={isLoading}
                    required
                    variant="light"
                  />
                </div>
              </div>

              {/* Security Notice */}
              <div className="p-2.5 bg-emerald-50/60 rounded-xl border border-emerald-200/60 text-[11px] text-emerald-900">
                <span>
                  Role is strictly locked to <strong className="font-semibold text-emerald-950">Commander Authority</strong>. Access to personnel stress analytics and welfare alerts is bounded to your assigned unit.
                </span>
              </div>

              {/* Submit Button (matching Image 1 dark button) */}
              <button
                id="commander-signup-button"
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 bg-[#1b332b] hover:bg-[#142821] active:bg-[#0f1f1a] text-white font-medium py-3 px-4 rounded-xl text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-md hover:shadow-lg disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Registering Command Authority...</span>
                  </>
                ) : (
                  <span>Create an Account</span>
                )}
              </button>
            </form>
          </div>

          {/* Prototype Notice */}
          <div className="mt-4 pt-3 border-t border-gray-100 text-[11px] text-gray-400 leading-snug flex items-start space-x-1.5">
            <Info className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
            <p>
              <strong className="text-gray-600">Research Prototype:</strong> Unit associations ensure strict cross-unit privacy and access control demonstration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
