'use client';

import React, { useState } from 'react';
import { WelfareRequestOut } from '@/types/api';
import { updateWelfareRequestStatus } from '@/lib/welfare';
import RiskBadge from './RiskBadge';
import { X, CheckCircle, Clock, AlertTriangle, ArrowRight, LifeBuoy, Activity, CheckCheck } from 'lucide-react';
import Link from 'next/link';

interface JawanRequestDrawerProps {
  request: WelfareRequestOut;
  onClose: () => void;
  onRefresh?: () => void;
}

export default function JawanRequestDrawer({
  request,
  onClose,
  onRefresh,
}: JawanRequestDrawerProps) {
  const [currentReq, setCurrentReq] = useState<WelfareRequestOut>(request);
  const [updating, setUpdating] = useState(false);

  const handleStatusChange = async (
    newStatus: 'pending' | 'acknowledged' | 'in_progress' | 'resolved'
  ) => {
    setUpdating(true);
    try {
      const updated = await updateWelfareRequestStatus(currentReq.id, newStatus);
      setCurrentReq(updated);
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Failed to update request status: ${err?.message || 'Access denied'}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-surface border-l border-surfaceBorder shadow-elevated flex flex-col z-50 overflow-hidden">
      {/* Top Header */}
      <div className="flex items-center justify-between p-4 border-b border-surfaceBorder bg-surface">
        <div>
          <div className="flex items-center space-x-2">
            <LifeBuoy className="w-4 h-4 text-accent" />
            <h2 className="text-base font-semibold text-textPrimary uppercase tracking-wider">
              Jawan Welfare Support Request
            </h2>
          </div>
          <span className="text-xs font-mono text-accent">ID: REQ-{currentReq.id} • {currentReq.personnel_code}</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-surfaceHighlight rounded text-textSecondary hover:text-textPrimary transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Source Badge */}
        <div className="flex items-center justify-between">
          <span className="px-2.5 py-1 rounded text-xs font-mono font-bold uppercase bg-accent/15 text-accent border border-accent/30">
            Source: Jawan Request
          </span>
          <span
            className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold uppercase border ${
              currentReq.status === 'resolved'
                ? 'bg-[#EEF6F2] text-[#2D6346] border-[#BBD9C7]'
                : currentReq.status === 'in_progress'
                ? 'bg-[#F4EFF8] text-[#69428E] border-[#DCCBEA]'
                : currentReq.status === 'acknowledged'
                ? 'bg-[#EEF4F8] text-[#3E6580] border-[#BCD3E3]'
                : 'bg-[#FDF6EE] text-[#8E5B23] border-[#F3D2AE]'
            }`}
          >
            {currentReq.status === 'in_progress' ? 'In Progress' : currentReq.status}
          </span>
        </div>

        {/* Personnel Card */}
        <div className="p-4 bg-surfaceHighlight/40 rounded-lg border border-surfaceBorder flex justify-between items-start">
          <div>
            <h3 className="font-semibold text-textPrimary text-base">{currentReq.personnel_name}</h3>
            <p className="text-xs text-textSecondary">{currentReq.job_role} • {currentReq.department}</p>
            <p className="text-xs font-mono text-accent mt-1">Scope: {currentReq.battalion || '7th Battalion'} • {currentReq.location || 'Active Base'}</p>
          </div>
          {currentReq.current_risk_score !== null && (
            <div className="text-right">
              {currentReq.current_stress_level && (
                <RiskBadge level={currentReq.current_stress_level} />
              )}
              <div className="text-xl font-bold font-mono text-[#8E5B23] mt-1">
                {currentReq.current_risk_score}
                <span className="text-xs text-textSecondary font-normal">/100</span>
              </div>
              <span className="text-[10px] text-textSecondary uppercase font-mono block">Current Risk</span>
            </div>
          )}
        </div>

        {/* Request Details */}
        <div className="p-4 bg-surfaceHighlight/30 rounded-lg border border-surfaceBorder space-y-3">
          <div className="flex justify-between items-center text-xs">
            <span className="text-textSecondary">Concern Category:</span>
            <span className="font-semibold text-textPrimary">{currentReq.category}</span>
          </div>

          <div className="flex justify-between items-center text-xs">
            <span className="text-textSecondary">Self-Reported Urgency:</span>
            <span
              className={`font-mono font-bold px-2 py-0.5 rounded text-xs border ${
                currentReq.urgency === 'High'
                  ? 'bg-[#FAF0F0] text-[#964747] border-[#E8B4B4]'
                  : currentReq.urgency === 'Medium'
                  ? 'bg-[#FDF6EE] text-[#8E5B23] border-[#F3D2AE]'
                  : 'bg-[#EEF6F2] text-[#2D6346] border-[#BBD9C7]'
              }`}
            >
              {currentReq.urgency}
            </span>
          </div>

          <div className="flex justify-between items-center text-xs">
            <span className="text-textSecondary">Submitted At:</span>
            <span className="font-mono text-textPrimary">
              {new Date(currentReq.created_at).toLocaleString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>

          {currentReq.resolved_at && (
            <div className="flex justify-between items-center text-xs">
              <span className="text-textSecondary">Resolved At:</span>
              <span className="font-mono text-emerald-400">
                {new Date(currentReq.resolved_at).toLocaleString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          )}

          {currentReq.message && (
            <div className="pt-2 border-t border-surfaceHighlight">
              <span className="text-[11px] uppercase font-mono text-textSecondary block mb-1">
                Jawan Message / Context:
              </span>
              <p className="text-xs text-textPrimary bg-surfaceHighlight/40 p-3 rounded italic leading-relaxed border border-surfaceHighlight">
                &ldquo;{currentReq.message}&rdquo;
              </p>
            </div>
          )}
        </div>

        {/* Action Controls for Officer / Commander (Section 5) */}
        <div className="space-y-3">
          <span className="text-xs uppercase font-mono tracking-wider text-textSecondary font-semibold block">
            Command Actions
          </span>
          <div className="flex flex-col gap-2">
            {currentReq.status === 'pending' && (
              <button
                disabled={updating}
                onClick={() => handleStatusChange('acknowledged')}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg transition flex items-center justify-center gap-2"
              >
                <Clock className="w-4 h-4" />
                <span>Acknowledge Request</span>
              </button>
            )}

            {(currentReq.status === 'pending' || currentReq.status === 'acknowledged') && (
              <button
                disabled={updating}
                onClick={() => handleStatusChange('in_progress')}
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs rounded-lg transition flex items-center justify-center gap-2"
              >
                <Activity className="w-4 h-4" />
                <span>Mark In Progress</span>
              </button>
            )}

            {currentReq.status !== 'resolved' && (
              <button
                disabled={updating}
                onClick={() => handleStatusChange('resolved')}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-lg transition flex items-center justify-center gap-2"
              >
                <CheckCheck className="w-4 h-4" />
                <span>Resolve & Close Request</span>
              </button>
            )}

            {currentReq.status === 'resolved' && (
              <div className="p-3 bg-emerald-950/40 border border-emerald-800/40 rounded-lg text-emerald-300 text-xs flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 shrink-0 text-emerald-400" />
                <span>This welfare request has been resolved and closed.</span>
              </div>
            )}
          </div>
        </div>

        {/* Link to Full Dossier */}
        <div className="pt-4 border-t border-surfaceHighlight">
          <Link
            href={`/personnel/${currentReq.personnel_id}`}
            className="flex items-center justify-center space-x-2 w-full py-2.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary text-xs font-semibold rounded-lg transition"
          >
            <span>Open Complete Personnel Dossier</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
