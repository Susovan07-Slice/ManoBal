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
      <div className="relative z-10 max-w-4xl w-full bg-white rounded-3xl shadow-2xl overflow-hidden grid grid-cols-1 md:grid-cols-2 border border-emerald-950/20">
        
        {/* Left Side: Indian Army Insignia Hero Panel (matching Image 1 layout with Image 2) */}
        <div className="relative bg-black p-8 md:p-10 flex flex-col justify-between overflow-hidden border-b md:border-b-0 md:border-r border-black">
          {/* Top Brand Watermark */}
          <div className="relative z-10 flex items-center space-x-3">
            <div className="w-14 h-14 flex items-center justify-center">
              <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-contain drop-shadow-md" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-widest font-bold text-emerald-400">ManoBal</span>
              <span className="text-[10px] text-gray-400 block tracking-wider uppercase font-mono">Defense Portal</span>
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

          {/* Bottom Heading & Subtext (typography matching Image 1) */}
          <div className="relative z-10 mt-auto">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Sign in to your <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-200 via-white to-teal-200">
                Command Account
              </span>
            </h1>
            <p className="text-gray-300 text-xs sm:text-sm mt-3 font-normal leading-relaxed">
              Personnel Stress & Welfare Decision-Support System. Official authorized access for Indian Armed Forces command personnel.
            </p>
          </div>
        </div>

        {/* Right Side: Clean Form Panel (matching Image 1 right column) */}
        <div className="bg-white p-8 sm:p-10 flex flex-col justify-between">
          <div>
            {/* Top Bar: Language / Region Selector */}
            <div className="flex justify-end mb-4">
              <div className="inline-flex items-center space-x-1 text-xs text-gray-500 font-medium cursor-pointer hover:text-gray-800 transition-colors">
                <span>Restricted (IND)</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Header */}
            <div className="mb-6">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900">
                Sign in
              </h2>
              <p className="text-sm text-gray-500 mt-1.5">
                Don&apos;t have an account?{' '}
                <Link href="/signup" className="text-emerald-700 font-semibold hover:underline">
                  Sign Up
                </Link>
              </p>
            </div>

            {/* Role Pills (matching the radio pill selectors from Image 1) */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <button
                type="button"
                onClick={() => selectRolePill('officer', 'officer_sharma', 'OfficerPassword123!')}
                className={`flex items-center space-x-2.5 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                  activeRole === 'officer'
                    ? 'border-emerald-600 bg-emerald-50/70 text-emerald-950 ring-2 ring-emerald-600/15'
                    : 'border-gray-200 bg-gray-50/50 text-gray-700 hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    activeRole === 'officer'
                      ? 'border-emerald-700 bg-emerald-700'
                      : 'border-gray-300 bg-white'
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
                    ? 'border-emerald-600 bg-emerald-50/70 text-emerald-950 ring-2 ring-emerald-600/15'
                    : 'border-gray-200 bg-gray-50/50 text-gray-700 hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    activeRole === 'counselor'
                      ? 'border-emerald-700 bg-emerald-700'
                      : 'border-gray-300 bg-white'
                  }`}
                >
                  {activeRole === 'counselor' && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </span>
                <span className="font-semibold truncate">Welfare Officer</span>
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-5 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center space-x-2 text-xs text-red-700">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-wider text-gray-600 font-semibold mb-1.5">
                  Service Username
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
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
                    className="w-full bg-gray-50/70 border border-gray-200 focus:bg-white focus:border-emerald-600 focus:ring-4 focus:ring-emerald-600/10 text-gray-900 text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-gray-400"
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-gray-600 font-semibold mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
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
                    className="w-full bg-gray-50/70 border border-gray-200 focus:bg-white focus:border-emerald-600 focus:ring-4 focus:ring-emerald-600/10 text-gray-900 text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none transition-all placeholder:text-gray-400"
                    autoComplete="current-password"
                    required
                  />
                </div>
              </div>

              {/* Submit Button (matching Image 1 dark button) */}
              <button
                id="login-button"
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 bg-[#1b332b] hover:bg-[#142821] active:bg-[#0f1f1a] text-white font-medium py-3 px-4 rounded-xl text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-md hover:shadow-lg disabled:opacity-50"
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
            <div className="mt-5 pt-4 border-t border-gray-100">
              <p className="text-[11px] uppercase tracking-wider font-semibold text-gray-400 mb-2">
                All Demo Roles:
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => fillCredentials('admin', 'AdminPassword123!')}
                  className="px-2.5 py-1.5 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 text-left transition-colors"
                >
                  <div className="font-semibold text-gray-800 text-[11px]">Administrator</div>
                  <div className="text-gray-400 font-mono text-[9px]">admin</div>
                </button>
                <button
                  type="button"
                  onClick={() => fillCredentials('jawan_verma', 'PersonnelPassword123!')}
                  className="px-2.5 py-1.5 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 text-left transition-colors"
                >
                  <div className="font-semibold text-gray-800 text-[11px]">Personnel / Jawan</div>
                  <div className="text-gray-400 font-mono text-[9px]">jawan_verma</div>
                </button>
              </div>
            </div>
          </div>

          {/* Prototype Notice */}
          <div className="mt-6 pt-3 border-t border-gray-100 text-[11px] text-gray-400 leading-snug flex items-start space-x-1.5">
            <Info className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
            <p>
              <strong className="text-gray-600">Notice:</strong> System uses synthetic dataset for research & demonstration. Decisions are advisory indicators.
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
