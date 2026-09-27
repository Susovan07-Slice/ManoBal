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
    <div className="min-h-screen bg-[#070b09] flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 relative selection:bg-emerald-800 selection:text-white">
      {/* Ambient background glow */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-950/40 rounded-full blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-950/30 rounded-full blur-3xl pointer-events-none translate-x-1/2 translate-y-1/2" />

      {/* Main Split Container */}
      <div className="relative z-10 max-w-4xl w-full bg-[#0a120c] rounded-3xl shadow-2xl shadow-black/80 overflow-hidden grid grid-cols-1 md:grid-cols-2 border border-emerald-900/40">
        
        {/* Left Side: Indian Armed Forces Hero Section */}
        <div className="relative bg-black p-6 sm:p-8 flex flex-col justify-between overflow-hidden border-b md:border-b-0 md:border-r border-emerald-950/20 min-h-[580px]">
          {/* Top Brand Watermark */}
          <div className="relative z-10 flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-700/40 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-widest font-bold text-emerald-400">ManoBal</span>
              <span className="text-[10px] text-gray-400 block tracking-wider uppercase font-mono">Defense Portal</span>
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
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight leading-snug">
              Indian Armed Forces
            </h1>
            <p className="text-gray-400 text-xs mt-1 font-normal leading-relaxed">
              Personnel Stress & Welfare Decision-Support System. Official authorized access for Command personnel.
            </p>
          </div>
        </div>

        {/* Right Side: Army Tactical Camouflage Form Panel */}
        <div className="relative p-8 sm:p-10 flex flex-col justify-between overflow-hidden bg-[#111c13] border-t md:border-t-0 md:border-l border-emerald-900/40">
          {/* Subtle military camouflage pattern overlay */}
          <div 
            className="absolute inset-0 bg-repeat opacity-25 mix-blend-overlay pointer-events-none"
            style={{ 
              backgroundImage: "url('/army_camo.png')",
              backgroundSize: '360px 360px'
            }}
          />
          {/* Tactical atmospheric dark gradient vignette */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#142318]/90 via-[#0e1710]/92 to-[#09100a]/96 pointer-events-none" />

          <div className="relative z-10">
            {/* Top Bar: Language / Region Selector */}
            <div className="flex justify-end mb-4">
              <div className="inline-flex items-center space-x-1 text-xs text-emerald-400/80 font-mono font-medium cursor-pointer hover:text-emerald-300 transition-colors">
                <span>Restricted (IND)</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Header */}
            <div className="mb-6">
              <h2 className="text-3xl font-extrabold tracking-tight text-white font-sans">
                Sign in
              </h2>
              <p className="text-sm text-emerald-200/70 mt-1.5 font-normal">
                Don&apos;t have an account?{' '}
                <Link href="/signup" className="text-emerald-400 font-semibold hover:underline hover:text-emerald-300">
                  Sign Up
                </Link>
              </p>
            </div>

            {/* Role Pills (Tactical Military Selectors) */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <button
                type="button"
                onClick={() => selectRolePill('officer', 'officer_sharma', 'OfficerPassword123!')}
                className={`flex items-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  activeRole === 'officer'
                    ? 'border-emerald-500 bg-emerald-950/80 text-emerald-200 ring-2 ring-emerald-500/30 shadow-md shadow-emerald-950/50'
                    : 'border-emerald-900/50 bg-black/40 text-gray-300 hover:bg-black/60 hover:border-emerald-700'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    activeRole === 'officer'
                      ? 'border-emerald-400 bg-emerald-500'
                      : 'border-gray-600 bg-transparent'
                  }`}
                >
                  {activeRole === 'officer' && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </span>
                <span className="font-semibold truncate">Commander</span>
              </button>

              <button
                type="button"
                onClick={() => selectRolePill('counselor', 'counselor_priya', 'WelfarePassword123!')}
                className={`flex items-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  activeRole === 'counselor'
                    ? 'border-emerald-500 bg-emerald-950/80 text-emerald-200 ring-2 ring-emerald-500/30 shadow-md shadow-emerald-950/50'
                    : 'border-emerald-900/50 bg-black/40 text-gray-300 hover:bg-black/60 hover:border-emerald-700'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    activeRole === 'counselor'
                      ? 'border-emerald-400 bg-emerald-500'
                      : 'border-gray-600 bg-transparent'
                  }`}
                >
                  {activeRole === 'counselor' && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </span>
                <span className="font-semibold truncate">Welfare Officer</span>
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-5 p-3 bg-red-950/60 border border-red-800/80 rounded-xl flex items-center space-x-2 text-xs text-red-200">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-wider text-emerald-400 font-bold mb-1.5 font-mono">
                  Service Username
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-emerald-500/70">
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
                    className="w-full bg-black/50 border border-emerald-900/60 focus:bg-black/75 focus:border-emerald-400 focus:ring-4 focus:ring-emerald-500/20 text-white text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-gray-500"
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-emerald-400 font-bold mb-1.5 font-mono">
                  Password
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-emerald-500/70">
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
                    className="w-full bg-black/50 border border-emerald-900/60 focus:bg-black/75 focus:border-emerald-400 focus:ring-4 focus:ring-emerald-500/20 text-white text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-gray-500"
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
                className="w-full mt-2 bg-gradient-to-r from-emerald-800 via-emerald-700 to-teal-800 hover:from-emerald-700 hover:to-teal-700 active:from-emerald-900 active:to-teal-900 text-white font-bold py-3 px-4 rounded-xl text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/60 border border-emerald-600/40 disabled:opacity-50"
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

            {/* Quick Demo Switcher */}
            <div className="mt-5 pt-4 border-t border-emerald-900/40">
              <p className="text-[11px] uppercase tracking-wider font-semibold text-emerald-400/70 mb-2 font-mono">
                All Demo Roles:
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => fillCredentials('admin', 'AdminPassword123!')}
                  className="px-2.5 py-1.5 bg-black/40 hover:bg-black/60 rounded-lg border border-emerald-900/50 hover:border-emerald-700 text-left transition-colors"
                >
                  <div className="font-semibold text-gray-200 text-[11px]">Administrator</div>
                  <div className="text-emerald-400/80 font-mono text-[9px]">admin</div>
                </button>
                <button
                  type="button"
                  onClick={() => fillCredentials('jawan_verma', 'PersonnelPassword123!')}
                  className="px-2.5 py-1.5 bg-black/40 hover:bg-black/60 rounded-lg border border-emerald-900/50 hover:border-emerald-700 text-left transition-colors"
                >
                  <div className="font-semibold text-gray-200 text-[11px]">Personnel / Jawan</div>
                  <div className="text-emerald-400/80 font-mono text-[9px]">jawan_verma</div>
                </button>
              </div>
            </div>
          </div>

          {/* Prototype Notice */}
          <div className="relative z-10 mt-6 pt-3 border-t border-emerald-900/40 text-[11px] text-emerald-300/60 leading-snug flex items-start space-x-1.5">
            <Info className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
            <p>
              <strong className="text-emerald-300">Notice:</strong> System uses synthetic dataset for research & demonstration. Decisions are advisory indicators.
            </p>
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
        <div className="min-h-screen bg-[#070b09] flex items-center justify-center text-gray-400 text-xs">
          Loading command portal...
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
