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
    <div className="flex flex-col min-h-screen bg-transparent text-mb-text-primary p-6 justify-center">
      {/* Disclaimer */}
      <div className="mb-6 p-3 bg-slate-800/80 border border-slate-700 rounded-lg text-xs text-mb-text-secondary flex items-start space-x-2">
        <Info className="w-4 h-4 text-mb-accent shrink-0 mt-0.5" />
        <p>
          <strong className="text-mb-text-primary">Prototype Notice:</strong> Synthetically augmented research prototype. Does not contain real CRPF records. Supportive decision-support only.
        </p>
      </div>

      <div className="flex flex-col items-center mb-8">
        <div className="w-14 h-14 bg-mb-accent/20 border border-mb-accent/40 rounded-full flex items-center justify-center mb-3">
          <Shield className="w-7 h-7 text-mb-accent" />
        </div>
        <h1 className="text-2xl font-bold text-mb-text-primary tracking-wider">ManoBal</h1>
        <p className="text-xs text-mb-text-secondary uppercase tracking-widest font-mono mt-1">
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
          <label className="block text-xs uppercase tracking-wider text-mb-text-secondary font-semibold mb-1">
            Service Username
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-mb-text-muted">
              <User className="w-4 h-4" />
            </span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. jawan_verma"
              disabled={loading}
              className="w-full bg-mb-glass-strong backdrop-blur-md border border-mb-glass-border focus:border-mb-accent text-mb-text-primary text-sm rounded-lg pl-10 pr-3 py-2.5 outline-none transition-colors"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs uppercase tracking-wider text-mb-text-secondary font-semibold mb-1">
            Password
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-mb-text-muted">
              <Lock className="w-4 h-4" />
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢"
              disabled={loading}
              className="w-full bg-mb-glass-strong backdrop-blur-md border border-mb-glass-border focus:border-mb-accent text-mb-text-primary text-sm rounded-lg pl-10 pr-3 py-2.5 outline-none transition-colors"
              required
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={loading}
          className="w-full mt-4 bg-mb-accent hover:bg-mb-accent text-mb-text-dark font-bold py-2.5 rounded-lg text-sm"
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


