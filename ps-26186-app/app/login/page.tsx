'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/AuthContext';
import { Shield, Lock, User, AlertCircle, Info } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function MobileLoginPage() {
  const router = useRouter();
  const { user, login } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      router.push('/');
      return;
    }
    // Onboarding guard
    try {
      if (!sessionStorage.getItem('manobal_onboarding_seen')) {
        router.replace('/welcome');
      }
    } catch (e) {
      // Ignore storage errors, default to allowing login
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please provide service username and password.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
      router.push('/');
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillJawan = () => {
    setUsername('jawan_verma');
    setPassword('PersonnelPassword123!');
    setError(null);
  };

  return (
    <div 
      className="flex flex-col min-h-[100dvh] p-6 justify-center absolute inset-0 z-20 overflow-y-auto"
    >
      {/* Logo & Branding */}
      <div className="flex flex-col items-center mb-8 animate-fade-up">
        <div className="w-28 h-28 mb-5 rounded-full bg-white shadow-[0_10px_30px_rgba(31,110,140,0.15)] border-2 border-white flex items-center justify-center overflow-hidden">
          <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-cover scale-110" />
        </div>
        <h1 className="text-[28px] font-bold text-ink tracking-tight">ManoBal</h1>
        <p className="eyebrow mt-2">
          Personnel Wellness Check-In
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-4 p-3.5 bg-alert-bg border border-alert/30 rounded-2xl text-[13px] text-ink flex items-center space-x-2.5 animate-fade-up">
          <AlertCircle className="w-4 h-4 text-alert shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Login Form Card */}
      <div className="glass-card p-6 space-y-5 animate-fade-up stagger-1">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
              Service Username
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ink-3">
                <User className="w-4 h-4" />
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. jawan_verma"
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl pl-11 pr-4 h-[52px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ink-3">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                disabled={loading}
                className="w-full bg-white border border-sky-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 text-ink text-sm font-medium rounded-2xl pl-11 pr-4 h-[52px] outline-none transition-all shadow-sm placeholder:text-ink-3"
                required
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full mt-2"
          >
            {loading ? 'Authenticating...' : 'Sign In to Portal'}
          </Button>

          <div className="pt-1 text-center">
            <p className="text-[13px] text-ink-2">
              Don&apos;t have an account?{' '}
              <Link href="/signup" className="text-brand-500 hover:text-brand-600 hover:underline font-semibold">
                Sign Up
              </Link>
            </p>
          </div>
        </form>
      </div>

      {/* Demo Access */}
      <div className="mt-8 pt-6 border-t border-sky-200/60 text-center animate-fade-up stagger-2">
        <p className="text-[12px] text-ink-3 mb-3 font-medium">Quick Demo Access:</p>
        <button
          type="button"
          onClick={fillJawan}
          className="w-full h-[48px] bg-white/70 backdrop-blur-md hover:bg-white border border-sky-200 rounded-full text-[12px] font-semibold text-brand-600 transition-all shadow-sm"
        >
          Log in as Constable Rajesh Verma (PF-0001)
        </button>
      </div>
    </div>
  );
}
