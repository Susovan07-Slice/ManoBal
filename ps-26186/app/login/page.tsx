'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/lib/AuthContext';
import { ShieldAlert, Lock, User, AlertCircle, Info, ChevronDown, Check, ShieldCheck } from 'lucide-react';
import armyInsignia from '@/public/army_insignia.jpg';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login } = useAuth();

  const [username, setUsername] = useState('officer_sharma');
  const [password, setPassword] = useState('OfficerPassword123!');
  const [activeRole, setActiveRole] = useState<'officer' | 'counselor' | 'custom'>('officer');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get('expired')) {
      setError('Your session has expired. Please sign in again.');
    }
  }, [searchParams]);

  useEffect(() => {
    if (user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please provide both username and password.');
      return;
    }

    setError(null);
    setIsLoading(true);
    try {
      await login(username.trim(), password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const selectRolePill = (role: 'officer' | 'counselor', u: string, p: string) => {
    setActiveRole(role);
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  const fillCredentials = (u: string, p: string) => {
    setActiveRole('custom');
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#F1F7F4] flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 relative selection:bg-[#7BA083]/30 selection:text-[#2D3748]">
      {/* Ambient background glow */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#7BA083]/10 rounded-full blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#A3BFAB]/15 rounded-full blur-3xl pointer-events-none translate-x-1/2 translate-y-1/2" />

      {/* Main Split Container */}
      <div className="relative z-10 max-w-4xl w-full bg-[#FAFAFC] rounded-3xl shadow-xl shadow-slate-300/40 overflow-hidden grid grid-cols-1 md:grid-cols-2 border border-[#D0DFD5]">
        
        {/* Left Side: Armed Forces Hero Section */}
        <div className="relative bg-[#E8F0EC] p-6 sm:p-8 flex flex-col justify-between overflow-hidden border-b md:border-b-0 md:border-r border-[#D0DFD5] min-h-[580px]">
          {/* Top Brand Watermark */}
          <div className="relative z-10 flex items-center space-x-3">
            <div className="w-14 h-14 flex items-center justify-center">
              <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-contain drop-shadow-sm" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-widest font-bold text-[#7BA083]">ManoBal</span>
              <span className="text-[10px] text-[#64748B] block tracking-wider uppercase font-mono">Defense Portal</span>
            </div>
          </div>

          {/* Center: Complete Logo Filling the Section without any cropping */}
          <div className="relative z-10 flex-1 my-auto w-full flex items-center justify-center py-2 px-2">
            <div className="w-full h-full max-h-[460px] relative transition-transform duration-500 hover:scale-[1.02] flex items-center justify-center">
              <img
                src="/armed_forces_badges.png"
                alt="Indian Armed Forces Insignia"
                className="w-full h-full object-contain"
              />
            </div>
          </div>

          {/* Bottom Heading & Subtext */}
          <div className="relative z-10 mt-auto pt-2">
            <h1 className="text-xl sm:text-2xl font-bold text-[#2D3748] tracking-tight leading-snug">
              Indian Armed Forces
            </h1>
            <p className="text-[#64748B] text-xs mt-1 font-normal leading-relaxed">
              Personnel Stress & Welfare Decision-Support System. Official authorized access for Command personnel.
            </p>
          </div>
        </div>

        {/* Right Side: Form Panel */}
        <div className="relative p-8 sm:p-10 flex flex-col justify-between overflow-hidden bg-[#FAFAFC]">
          <div className="relative z-10">
            {/* Top Bar: Language / Region Selector */}
            <div className="flex justify-end mb-4">
              <div className="inline-flex items-center space-x-1 text-xs text-[#7BA083] font-mono font-medium cursor-pointer hover:text-[#5C8064] transition-colors">
                <span>Restricted (IND)</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Header */}
            <div className="mb-6">
              <h2 className="text-3xl font-extrabold tracking-tight text-[#2D3748] font-sans">
                Sign in
              </h2>
              <p className="text-sm text-[#64748B] mt-1.5 font-normal">
                Don&apos;t have an account?{' '}
                <Link href="/signup" className="text-[#7BA083] font-semibold hover:underline hover:text-[#5C8064]">
                  Sign Up
                </Link>
              </p>
            </div>

            {/* Role Pills */}
            <div className="grid grid-cols-1 mb-6">
              <button
                type="button"
                onClick={() => selectRolePill('officer', 'officer_sharma', 'OfficerPassword123!')}
                className={`w-full flex items-center justify-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  activeRole === 'officer'
                    ? 'border-[#7BA083] bg-[#E8F0EC] text-[#2D3748] ring-2 ring-[#7BA083]/25 shadow-sm'
                    : 'border-[#D0DFD5] bg-[#FAFAFC] text-[#64748B] hover:bg-[#F1F7F4] hover:border-[#BACFC2]'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    activeRole === 'officer'
                      ? 'border-[#7BA083] bg-[#7BA083]'
                      : 'border-[#BACFC2] bg-transparent'
                  }`}
                >
                  {activeRole === 'officer' && <span className="w-1.5 h-1.5 rounded-full bg-[#FAFAFC]" />}
                </span>
                <span className="font-semibold truncate">Commander</span>
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-5 p-3 bg-[#FAF0F0] border border-[#E8B4B4] rounded-xl flex items-center space-x-2 text-xs text-[#964747]">
                <AlertCircle className="w-4 h-4 shrink-0 text-[#C26D6D]" />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-wider text-[#64748B] font-bold mb-1.5 font-mono">
                  Service Username (only lowercase)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7BA083]">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    id="username-input"
                    type="text"
                    value={username}
                    onChange={(e) => {
                      setUsername(e.target.value);
                      setActiveRole('custom');
                    }}
                    placeholder="e.g. officer_sharma"
                    disabled={isLoading}
                    className="w-full bg-[#F1F7F4] border border-[#D0DFD5] focus:bg-[#FAFAFC] focus:border-[#7BA083] focus:ring-4 focus:ring-[#7BA083]/20 text-[#2D3748] text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-[#94A3B8]"
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#64748B] font-bold mb-1.5 font-mono">
                  Password
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7BA083]">
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    id="password-input"
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setActiveRole('custom');
                    }}
                    placeholder="••••••••••••"
                    disabled={isLoading}
                    className="w-full bg-[#F1F7F4] border border-[#D0DFD5] focus:bg-[#FAFAFC] focus:border-[#7BA083] focus:ring-4 focus:ring-[#7BA083]/20 text-[#2D3748] text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-[#94A3B8]"
                    autoComplete="current-password"
                    required
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                id="login-button"
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 bg-[#7BA083] hover:bg-[#688E70] active:bg-[#5C8064] text-white font-bold py-3 px-4 rounded-xl text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-sm border border-[#688E70] disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Authenticating...</span>
                  </>
                ) : (
                  <span>Sign In to Command Center</span>
                )}
              </button>
            </form>


          </div>


        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#F1F7F4] flex items-center justify-center text-[#64748B] text-xs">
          Loading command portal...
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
