'use client';
import React from 'react';
import { useRole } from '@/lib/RoleContext';

export default function RoleToggle() {
  const { role, setRole } = useRole();

  return (
    <div className="flex items-center space-x-2 bg-surfaceHighlight p-1 rounded border border-surface">
      <button 
        onClick={() => setRole('officer')}
        className={`px-3 py-1 text-sm rounded font-medium transition-colors ${
          role === 'officer' ? 'bg-accent text-white' : 'text-textSecondary hover:text-textPrimary'
        }`}
      >
        Officer
      </button>
      <button 
        onClick={() => setRole('welfare')}
        className={`px-3 py-1 text-sm rounded font-medium transition-colors ${
          role === 'welfare' ? 'bg-accent text-white' : 'text-textSecondary hover:text-textPrimary'
        }`}
      >
        Welfare
      </button>
    </div>
  );
}
