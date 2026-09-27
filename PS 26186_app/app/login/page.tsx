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
    <div 
      className="flex flex-col min-h-screen text-mb-text-primary p-6 justify-center bg-cover bg-center bg-no-repeat absolute inset-0 z-20"
      style={{ backgroundImage: "url('/login-bg.png')" }}
    >
      <div className="flex flex-col items-center mb-8">
        <div className="mb-4">
          <img src="/armed forces.png" alt="Indian Armed Forces" className="h-12 object-contain filter invert opacity-90" />
        </div>
        <div className="flex items-center justify-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full overflow-hidden bg-black/40 flex items-center justify-center p-1 border border-white/20">
            <img src="/army.png" alt="Indian Army" className="w-full h-full object-contain filter invert" />
          </div>
          <div className="w-16 h-16 rounded-full overflow-hidden bg-black/40 flex items-center justify-center p-1 border border-white/20">
            <img src="/navy.png" alt="Indian Navy" className="w-full h-full object-contain filter invert" />
          </div>
          <div className="w-16 h-16 rounded-full overflow-hidden bg-black/40 flex items-center justify-center p-1 border border-white/20">
            <img src="/airforce.png" alt="Indian Air Force" className="w-full h-full object-contain filter invert" />
          </div>
        </div>
        
        <h1 className="text-2xl font-bold text-mb-text-primary tracking-wider">ManoBal</h1>
        <p className="text-xs text-mb-text-primary uppercase tracking-widest font-mono mt-1 font-semibold">
          Personnel Wellness Check-In
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-950/60 border border-red-800/80 rounded-lg text-xs text-red-200 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-mb-danger shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1">
            Service Username
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
              <User className="w-4 h-4" />
            </span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. jawan_verma"
              disabled={loading}
              className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg pl-10 pr-3 py-3 outline-none transition-colors shadow-sm placeholder:text-gray-400"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs uppercase tracking-wider text-mb-text-primary font-bold mb-1">
            Password
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
              <Lock className="w-4 h-4" />
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              disabled={loading}
              className="w-full bg-white/90 border border-gray-300 focus:border-mb-accent text-gray-900 text-sm font-medium rounded-lg pl-10 pr-3 py-3 outline-none transition-colors shadow-sm placeholder:text-gray-400"
              required
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={loading}
          className="w-full mt-4 bg-mb-accent hover:bg-mb-accent text-mb-text-dark font-bold py-3 rounded-lg text-sm"
        >
          {loading ? 'Authenticating...' : 'Sign In to Portal'}
        </Button>

        <div className="pt-2 text-center">
          <p className="text-xs text-mb-text-secondary">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="text-mb-accent hover:underline font-semibold">
              Sign Up
            </Link>
          </p>
        </div>
      </form>

      <div className="mt-8 pt-6 border-t border-slate-800 text-center">
        <p className="text-xs text-mb-text-secondary mb-2 font-medium">Quick Demo Access:</p>
        <button
          type="button"
          onClick={fillJawan}
          className="w-full py-2 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono text-mb-accent font-semibold transition-colors"
        >
          Log in as Constable Rajesh Verma (PF-0001)
        </button>
      </div>
    </div>
  );
}


