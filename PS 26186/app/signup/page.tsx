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
    <div className="min-h-screen bg-[#F1F7F4] flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 relative selection:bg-[#7BA083]/30 selection:text-[#2D3748]">
      {/* Ambient background glow */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#7BA083]/10 rounded-full blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#A3BFAB]/15 rounded-full blur-3xl pointer-events-none translate-x-1/2 translate-y-1/2" />

      {/* Main Split Container */}
      <div className="relative z-10 max-w-4xl w-full bg-[#FAFAFC] rounded-3xl shadow-xl shadow-slate-300/40 overflow-hidden grid grid-cols-1 md:grid-cols-2 border border-[#D0DFD5] my-6">
        
        {/* Left Side: Indian Army Insignia Hero Panel */}
        <div className="relative bg-[#E8F0EC] p-6 sm:p-8 md:p-10 flex flex-col justify-between overflow-hidden border-b md:border-b-0 md:border-r border-[#D0DFD5]">
          {/* Top Brand Watermark */}
          <div className="relative z-10 flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-[#DCEAE0] border border-[#BACFC2] flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-[#7BA083]" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-widest font-bold text-[#7BA083]">ManoBal</span>
              <span className="text-[10px] text-[#64748B] block tracking-wider uppercase font-mono">Command Enlistment</span>
            </div>
          </div>

          {/* Center: Image (Indian Army Insignia) */}
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
                className="object-contain"
                style={{ objectFit: 'contain' }}
              />
            </div>
          </div>

          {/* Bottom Heading & Subtext */}
          <div className="relative z-10 mt-auto">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#2D3748] tracking-tight leading-tight">
              Create your <br />
              <span className="text-[#7BA083]">
                Officer Account
              </span>
            </h1>
            <p className="text-[#64748B] text-xs sm:text-sm mt-3 font-normal leading-relaxed">
              Register unit authority to access personnel psychological assessment telemetry, predictive risk monitoring, and welfare pipelines.
            </p>
          </div>
        </div>

        {/* Right Side: Clean Form Panel */}
        <div className="bg-[#FAFAFC] p-6 sm:p-8 md:p-10 flex flex-col justify-between">
          <div>
            {/* Top Bar: Language / Region Selector */}
            <div className="flex justify-end mb-2">
              <div className="inline-flex items-center space-x-1 text-xs text-[#64748B] font-medium cursor-pointer hover:text-[#2D3748] transition-colors">
                <span>Restricted (IND)</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Header */}
            <div className="mb-4">
              <h2 className="text-3xl font-bold tracking-tight text-[#2D3748]">
                Sign up
              </h2>
              <p className="text-sm text-[#64748B] mt-1">
                Already have an account?{' '}
                <Link href="/login" className="text-[#7BA083] font-semibold hover:underline hover:text-[#5C8064]">
                  Sign In
                </Link>
              </p>
            </div>

            {/* Role Pills */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <button
                type="button"
                onClick={() => setRoleType('commander')}
                className={`flex items-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  roleType === 'commander'
                    ? 'border-[#7BA083] bg-[#E8F0EC] text-[#2D3748] ring-2 ring-[#7BA083]/20 shadow-sm'
                    : 'border-[#D0DFD5] bg-[#FAFAFC] text-[#64748B] hover:bg-[#F1F7F4] hover:border-[#BACFC2]'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    roleType === 'commander'
                      ? 'border-[#7BA083] bg-[#7BA083]'
                      : 'border-[#BACFC2] bg-transparent'
                  }`}
                >
                  {roleType === 'commander' && <span className="w-1.5 h-1.5 rounded-full bg-[#FAFAFC]" />}
                </span>
                <span className="font-semibold truncate">Commander</span>
              </button>

              <button
                type="button"
                onClick={() => setRoleType('welfare')}
                className={`flex items-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  roleType === 'welfare'
                    ? 'border-[#7BA083] bg-[#E8F0EC] text-[#2D3748] ring-2 ring-[#7BA083]/20 shadow-sm'
                    : 'border-[#D0DFD5] bg-[#FAFAFC] text-[#64748B] hover:bg-[#F1F7F4] hover:border-[#BACFC2]'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    roleType === 'welfare'
                      ? 'border-[#7BA083] bg-[#7BA083]'
                      : 'border-[#BACFC2] bg-transparent'
                  }`}
                >
                  {roleType === 'welfare' && <span className="w-1.5 h-1.5 rounded-full bg-[#FAFAFC]" />}
                </span>
                <span className="font-semibold truncate">Welfare Officer</span>
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-[#FAF0F0] border border-[#E8B4B4] rounded-xl flex items-center space-x-2 text-xs text-[#964747]">
                <AlertCircle className="w-4 h-4 shrink-0 text-[#C26D6D]" />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {/* Full Name */}
              <div>
                <label className="block text-xs uppercase tracking-wider text-[#64748B] font-semibold mb-1">
                  Full Officer Name *
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7BA083]">
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
                    className="w-full bg-[#F1F7F4] border border-[#D0DFD5] focus:bg-[#FAFAFC] focus:border-[#7BA083] focus:ring-4 focus:ring-[#7BA083]/20 text-[#2D3748] text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-[#94A3B8]"
                    required
                  />
                </div>
              </div>

              {/* Grid: Username & Email */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs uppercase tracking-wider text-[#64748B] font-semibold mb-1">
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
                    className="w-full bg-[#F1F7F4] border border-[#D0DFD5] focus:bg-[#FAFAFC] focus:border-[#7BA083] focus:ring-4 focus:ring-[#7BA083]/20 text-[#2D3748] text-sm rounded-xl px-3.5 py-2.5 outline-none transition-all font-mono placeholder:text-[#94A3B8]"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-[#64748B] font-semibold mb-1">
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
                    className="w-full bg-[#F1F7F4] border border-[#D0DFD5] focus:bg-[#FAFAFC] focus:border-[#7BA083] focus:ring-4 focus:ring-[#7BA083]/20 text-[#2D3748] text-sm rounded-xl px-3.5 py-2.5 outline-none transition-all placeholder:text-[#94A3B8]"
                  />
                </div>
              </div>

              {/* Grid: Password & Confirm */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs uppercase tracking-wider text-[#64748B] font-semibold mb-1">
                    Password *
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7BA083]">
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
                      className="w-full bg-[#F1F7F4] border border-[#D0DFD5] focus:bg-[#FAFAFC] focus:border-[#7BA083] focus:ring-4 focus:ring-[#7BA083]/20 text-[#2D3748] text-sm rounded-xl pl-10 pr-3.5 py-2.5 outline-none transition-all placeholder:text-[#94A3B8]"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-[#64748B] font-semibold mb-1">
                    Confirm Password *
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7BA083]">
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
                      className="w-full bg-[#F1F7F4] border border-[#D0DFD5] focus:bg-[#FAFAFC] focus:border-[#7BA083] focus:ring-4 focus:ring-[#7BA083]/20 text-[#2D3748] text-sm rounded-xl pl-10 pr-3.5 py-2.5 outline-none transition-all placeholder:text-[#94A3B8]"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Organizational Scope Section */}
              <div className="pt-2 border-t border-[#D0DFD5] space-y-2">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-[#7BA083] uppercase tracking-wider">
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
              <div className="p-2.5 bg-[#EEF6F2] rounded-xl border border-[#D0DFD5] text-[11px] text-[#2D3748]">
                <span>
                  Role is strictly locked to <strong className="font-semibold text-[#2D3748]">Commander Authority</strong>. Access to personnel stress analytics and welfare alerts is bounded to your assigned unit.
                </span>
              </div>

              {/* Submit Button */}
              <button
                id="commander-signup-button"
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 bg-[#7BA083] hover:bg-[#688E70] active:bg-[#5C8064] text-white font-medium py-3 px-4 rounded-xl text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-sm hover:shadow border border-[#688E70] disabled:opacity-50"
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
          <div className="mt-4 pt-3 border-t border-[#D0DFD5] text-[11px] text-[#64748B] leading-snug flex items-start space-x-1.5">
            <Info className="w-3.5 h-3.5 text-[#7BA083] shrink-0 mt-0.5" />
            <p>
              <strong className="text-[#2D3748]">Research Prototype:</strong> Unit associations ensure strict cross-unit privacy and access control demonstration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
