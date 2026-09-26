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
    <div className="flex flex-col min-h-screen bg-[#141A22] text-slate-100 p-6 justify-center">
      {/* Disclaimer */}
      <div className="mb-6 p-3 bg-slate-800/80 border border-slate-700 rounded-lg text-xs text-slate-300 flex items-start space-x-2">
        <Info className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
        <p>
          <strong className="text-slate-100">Prototype Notice:</strong> Synthetically augmented research prototype. Does not contain real CRPF records. Supportive decision-support only.
        </p>
      </div>

      <div className="flex flex-col items-center mb-8">
        <div className="w-14 h-14 bg-teal-500/20 border border-teal-500/40 rounded-full flex items-center justify-center mb-3">
          <Shield className="w-7 h-7 text-teal-400" />
        </div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-wider">ManoBal</h1>
        <p className="text-xs text-slate-400 uppercase tracking-widest font-mono mt-1">
          Personnel Wellness Check-In
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-950/60 border border-red-800/80 rounded-lg text-xs text-red-200 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">
            Service Username
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <User className="w-4 h-4" />
            </span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. jawan_verma"
              disabled={loading}
              className="w-full bg-[#1C2530] border border-slate-700 focus:border-teal-500 text-slate-100 text-sm rounded-lg pl-10 pr-3 py-2.5 outline-none transition-colors"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">
            Password
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Lock className="w-4 h-4" />
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              disabled={loading}
              className="w-full bg-[#1C2530] border border-slate-700 focus:border-teal-500 text-slate-100 text-sm rounded-lg pl-10 pr-3 py-2.5 outline-none transition-colors"
              required
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={loading}
          className="w-full mt-4 bg-teal-500 hover:bg-teal-600 text-slate-950 font-bold py-2.5 rounded-lg text-sm"
        >
          {loading ? 'Authenticating...' : 'Sign In to Portal'}
        </Button>

        <div className="pt-2 text-center">
          <p className="text-xs text-slate-400">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="text-teal-400 hover:underline font-semibold">
              Sign Up
            </Link>
          </p>
        </div>
      </form>

      <div className="mt-8 pt-6 border-t border-slate-800 text-center">
        <p className="text-xs text-slate-400 mb-2 font-medium">Quick Demo Access:</p>
        <button
          type="button"
          onClick={fillJawan}
          className="w-full py-2 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono text-teal-400 font-semibold transition-colors"
        >
          Log in as Constable Rajesh Verma (PF-0001)
        </button>
      </div>
    </div>
  );
}
