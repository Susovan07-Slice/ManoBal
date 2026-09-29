'use client';

import React, { useEffect, useState } from 'react';
import { HighRiskPersonnelItem, StressAssessmentOut } from '@/types/api';
import { ROLE_CONFIG } from '@/lib/rbac';
import { UserRole } from '@/types/rbac';
import RiskBadge from './RiskBadge';
import { X, CheckCircle, Clock, AlertTriangle, ArrowRight } from 'lucide-react';
import { getPersonnelAssessments, updateRecommendationStatus } from '@/lib/assessments';
import Link from 'next/link';

interface AlertDetailDrawerProps {
  alert: HighRiskPersonnelItem;
  role: UserRole;
  onClose: () => void;
  onRefresh?: () => void;
}

export default function AlertDetailDrawer({
  alert,
  role,
  onClose,
  onRefresh
}: AlertDetailDrawerProps) {
  const config = ROLE_CONFIG[role] || ROLE_CONFIG.officer;
  const [assessment, setAssessment] = useState<StressAssessmentOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  useEffect(() => {
    async function loadAssessment() {
      setLoading(true);
      try {
        const history = await getPersonnelAssessments(alert.personnel_id);
        if (history && history.length > 0) {
          setAssessment(history[0]);
        }
      } catch (err) {
        console.error('Failed to load assessment details for personnel:', err);
      } finally {
        setLoading(false);
      }
    }

    loadAssessment();
  }, [alert.personnel_id]);

  const handleStatusChange = async (recId: number, newStatus: 'pending' | 'acknowledged' | 'completed' | 'dismissed') => {
    setUpdatingId(recId);
    try {
      await updateRecommendationStatus(recId, newStatus);
      // Update local state
      if (assessment) {
        setAssessment({
          ...assessment,
          recommendations: assessment.recommendations.map(r =>
            r.id === recId ? { ...r, status: newStatus } : r
          ),
        });
      }
      if (onRefresh) onRefresh();
    } catch (err: any) {
      if (typeof window !== 'undefined') {
        window.alert(`Failed to update recommendation status: ${err?.message || 'Access denied'}`);
      }
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-surface border-l border-surfaceBorder shadow-elevated flex flex-col z-50 overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-surfaceBorder bg-surface">
        <div>
          <h2 className="text-base font-semibold text-textPrimary uppercase tracking-wider">
            Operational Welfare Alert
          </h2>
          <span className="text-xs font-mono text-accent">{alert.personnel_code}</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-surfaceHighlight rounded text-textSecondary hover:text-textPrimary transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Header Overview */}
        <div className="p-4 bg-surfaceHighlight/30 rounded border border-surfaceHighlight flex justify-between items-start">
          <div>
            <h3 className="font-semibold text-textPrimary text-base">{alert.personnel_name}</h3>
            <p className="text-xs text-textSecondary">{alert.job_role} • {alert.department}</p>
            <p className="text-xs font-mono text-textSecondary mt-1">Station: {alert.location}</p>
          </div>
          <div className="text-right">
            <RiskBadge level={alert.stress_level} />
            <div className="text-xl font-bold font-mono text-[#C26D6D] mt-1">
              {alert.risk_score}<span className="text-xs text-textSecondary font-normal">/100</span>
            </div>
            <span className="text-[10px] font-mono uppercase text-accent font-semibold">
              {alert.risk_priority} Priority
            </span>
          </div>
        </div>

        {/* Contributing Operational Metrics */}
        <div>
          <h4 className="text-xs uppercase tracking-widest text-textSecondary font-semibold mb-3">
            Contributing Operational Telemetry
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-surfaceHighlight/40 p-2.5 rounded-lg border border-surfaceBorder">
              <span className="text-textSecondary block">Duty Hours/Wk</span>
              <span className="font-mono text-textPrimary font-bold text-sm">
                {alert.duty_hours_per_week} hrs
              </span>
            </div>
            <div className="bg-surfaceHighlight/40 p-2.5 rounded-lg border border-surfaceBorder">
              <span className="text-textSecondary block">Consecutive Duty</span>
              <span className="font-mono text-textPrimary font-bold text-sm">
                {alert.consecutive_duty_days} days
              </span>
            </div>
            <div className="bg-surfaceHighlight/40 p-2.5 rounded-lg border border-surfaceBorder">
              <span className="text-textSecondary block">Night Shifts / Mo</span>
              <span className="font-mono text-textPrimary font-bold text-sm">
                {alert.night_shifts_per_month} shifts
              </span>
            </div>
            <div className="bg-surfaceHighlight/40 p-2.5 rounded-lg border border-surfaceBorder">
              <span className="text-textSecondary block">Leave Gap Days</span>
              <span className="font-mono text-textPrimary font-bold text-sm">
                {alert.leave_gap_days} days
              </span>
            </div>
          </div>
        </div>

        {/* Key Model-Associated Factors */}
        <div>
          <h4 className="text-xs uppercase tracking-widest text-textSecondary font-semibold mb-1">
            Factors Associated with This Prediction
          </h4>
          <p className="text-[11px] text-textSecondary mb-3 italic">
            Statistical model associations; does not imply medical or operational causation.
          </p>

          {alert.key_factors && alert.key_factors.length > 0 ? (
            <ul className="space-y-2">
              {alert.key_factors.map((factor, i) => (
                <li
                  key={i}
                  className="text-xs text-textPrimary bg-surfaceHighlight/40 p-2.5 rounded-lg border-l-2 border-accent flex items-start space-x-2"
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-accent shrink-0 mt-0.5" />
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-xs text-textSecondary p-3 bg-surfaceHighlight/40 rounded-lg border border-surfaceBorder">
              Standard operational baselines observed.
            </div>
          )}
        </div>

        {/* Welfare Recommendations */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-xs uppercase tracking-widest text-textSecondary font-semibold">
              Actionable Welfare Decision Support
            </h4>
            {loading && <div className="w-3.5 h-3.5 border border-accent border-t-transparent rounded-full animate-spin" />}
          </div>

          {assessment?.recommendations && assessment.recommendations.length > 0 ? (
            <div className="space-y-3">
              {assessment.recommendations.map((rec) => (
                <div
                  key={rec.id}
                  className="p-3 bg-surfaceHighlight/40 rounded-lg border border-surfaceBorder text-xs space-y-2"
                >
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-accent uppercase tracking-wider text-[10px]">
                      {rec.recommendation_type}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-mono font-bold border ${
                        rec.status === 'pending'
                          ? 'bg-[#FDF6EE] text-[#8E5B23] border-[#F3D2AE]'
                          : rec.status === 'acknowledged'
                          ? 'bg-[#EEF4F8] text-[#3E6580] border-[#BCD3E3]'
                          : rec.status === 'completed'
                          ? 'bg-[#EEF6F2] text-[#2D6346] border-[#BBD9C7]'
                          : 'bg-surfaceHighlight text-textSecondary border-surfaceBorder'
                      }`}
                    >
                      {rec.status}
                    </span>
                  </div>

                  <p className="text-textPrimary leading-relaxed">
                    {rec.recommendation_text}
                  </p>

                  {/* Status Action Buttons for Authorized Roles */}
                  {config.canEditStatus && (
                    <div className="pt-2 border-t border-surfaceHighlight/50 flex flex-wrap gap-1.5 justify-end">
                      {rec.status !== 'acknowledged' && rec.status !== 'completed' && (
                        <button
                          disabled={updatingId === rec.id}
                          onClick={() => handleStatusChange(rec.id, 'acknowledged')}
                          className="px-2 py-1 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-[10px] text-blue-300 rounded font-medium transition-colors"
                        >
                          Acknowledge
                        </button>
                      )}
                      {rec.status !== 'completed' && (
                        <button
                          disabled={updatingId === rec.id}
                          onClick={() => handleStatusChange(rec.id, 'completed')}
                          className="px-2 py-1 bg-emerald-950/60 hover:bg-emerald-900/60 text-[10px] text-emerald-300 rounded font-medium border border-emerald-800/40 transition-colors"
                        >
                          Mark Completed
                        </button>
                      )}
                      {rec.status !== 'dismissed' && rec.status !== 'completed' && (
                        <button
                          disabled={updatingId === rec.id}
                          onClick={() => handleStatusChange(rec.id, 'dismissed')}
                          className="px-2 py-1 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-[10px] text-textSecondary rounded font-medium transition-colors"
                        >
                          Dismiss
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-textSecondary p-3 bg-surfaceHighlight/20 rounded">
              {loading ? 'Retrieving active recommendations...' : 'No active welfare interventions logged.'}
            </div>
          )}
        </div>
      </div>

      {/* Footer Navigation to Personnel Detail */}
      <div className="p-4 border-t border-surfaceHighlight bg-surfaceHighlight/20 flex justify-between items-center">
        <Link
          href={`/personnel/${alert.personnel_id}`}
          className="text-xs text-accent hover:underline flex items-center space-x-1"
        >
          <span>View Full Personnel Service Record</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
        <button
          onClick={onClose}
          className="px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-xs text-textPrimary rounded font-medium transition-colors"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
}
