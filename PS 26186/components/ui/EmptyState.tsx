import React from 'react';
import { LucideIcon } from 'lucide-react';

export default function EmptyState({ 
  icon: Icon, 
  title, 
  description 
}: { 
  icon: LucideIcon; 
  title: string; 
  description: string; 
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center h-full w-full">
      <div className="p-4 bg-surfaceHighlight/30 rounded-full mb-4">
        <Icon className="w-8 h-8 text-textSecondary" />
      </div>
      <h3 className="text-base font-semibold text-textPrimary tracking-tight mb-1">{title}</h3>
      <p className="text-sm text-textSecondary max-w-sm">{description}</p>
    </div>
  );
}
