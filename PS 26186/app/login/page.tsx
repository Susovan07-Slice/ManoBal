'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/AuthContext';
import { ShieldAlert, Lock, User, AlertCircle, Info, CheckCircle2 } from 'lucide-react';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
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

  const fillCredentials = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4">
      {/* Ethical Prototype Disclaimer Banner */}
      <div className="max-w-md w-full mb-6 p-3 bg-surfaceHighlight/60 border border-military rounded text-xs text-textSecondary flex items-start space-x-2">
        <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
        <p>
          <strong className="text-textPrimary">Prototype Notice:</strong> This system uses a synthetically augmented dataset for demonstration and research prototyping. It does not contain real CRPF personnel data. Predictions are decision-support indicators and are not medical diagnoses or disciplinary decisions.
        </p>
      </div>

      <div className="max-w-md w-full bg-surface border border-surfaceHighlight rounded-lg shadow-card p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-accent/20 rounded-full flex items-center justify-center mb-3 border border-accent/40">
            <ShieldAlert className="w-6 h-6 text-accent" />
          </div>
          <h1 className="text-2xl font-bold text-textPrimary uppercase tracking-wider">ManoBal</h1>
          <p className="text-xs text-textSecondary uppercase tracking-widest font-mono mt-1">
            Command & Welfare Portal
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-900/30 border border-red-700/50 rounded flex items-center space-x-2 text-sm text-red-200">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
              Service Username
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-textSecondary">
                <User className="w-4 h-4" />
              </span>
              <input
                id="username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. officer_sharma"
                disabled={isLoading}
                className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-textPrimary text-sm rounded pl-10 pr-3 py-2.5 outline-none transition-colors"
                autoComplete="username"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-textSecondary">
                <Lock className="w-4 h-4" />
              </span>
              <input
                id="password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                disabled={isLoading}
                className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-textPrimary text-sm rounded pl-10 pr-3 py-2.5 outline-none transition-colors"
                autoComplete="current-password"
                required
              />
            </div>
          </div>

          <button
            id="login-button"
            type="submit"
            disabled={isLoading}
            className="w-full mt-6 bg-accent hover:bg-accent/80 text-white font-medium py-2.5 px-4 rounded text-sm transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
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

        <div className="mt-4 text-center">
          <p className="text-xs text-textSecondary">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="text-accent hover:underline font-semibold">
              Sign Up as Commander
            </Link>
          </p>
        </div>

        {/* Demo Credentials Quick-Select */}
        <div className="mt-6 pt-6 border-t border-surfaceHighlight">
          <p className="text-xs uppercase tracking-wider font-semibold text-textSecondary mb-3">
            Quick-Login Demo Accounts:
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => fillCredentials('officer_sharma', 'OfficerPassword123!')}
              className="p-2 bg-surfaceHighlight/50 hover:bg-surfaceHighlight rounded border border-surfaceHighlight text-left transition-colors"
            >
              <div className="font-semibold text-textPrimary">Commanding Officer</div>
              <div className="text-textSecondary font-mono text-[10px]">officer_sharma</div>
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('counselor_priya', 'WelfarePassword123!')}
              className="p-2 bg-surfaceHighlight/50 hover:bg-surfaceHighlight rounded border border-surfaceHighlight text-left transition-colors"
            >
              <div className="font-semibold text-textPrimary">Welfare Counselor</div>
              <div className="text-textSecondary font-mono text-[10px]">counselor_priya</div>
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('admin', 'AdminPassword123!')}
              className="p-2 bg-surfaceHighlight/50 hover:bg-surfaceHighlight rounded border border-surfaceHighlight text-left transition-colors"
            >
              <div className="font-semibold text-textPrimary">Administrator</div>
              <div className="text-textSecondary font-mono text-[10px]">admin</div>
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('jawan_verma', 'PersonnelPassword123!')}
              className="p-2 bg-surfaceHighlight/50 hover:bg-surfaceHighlight rounded border border-surfaceHighlight text-left transition-colors"
            >
              <div className="font-semibold text-textPrimary">Personnel / Jawan</div>
              <div className="text-textSecondary font-mono text-[10px]">jawan_verma</div>
            </button>
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
        <div className="min-h-screen bg-background flex items-center justify-center text-textSecondary text-xs">
          Loading login portal...
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
