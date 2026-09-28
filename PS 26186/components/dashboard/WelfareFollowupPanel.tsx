'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  WelfareFollowupOut,
  UnitFollowupAnalyticsResponse,
  getUnitFollowupSummary,
  getPersonnelFollowups,
  scheduleFollowup,
  completeFollowup,
  deferFollowup,
  cancelFollowup,
  reassessFollowupOutcome,
  createFollowup,
} from '@/lib/followups';
import {
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RotateCcw,
  UserCheck,
  ChevronRight,
  TrendingDown,
  TrendingUp,
  Activity,
  ShieldAlert,
  Info,
  RefreshCw,
  Plus,
  ArrowRight,
  X,
  FileCheck,
} from 'lucide-react';

export default function WelfareFollowupPanel() {
  const [analytics, setAnalytics] = useState<UnitFollowupAnalyticsResponse | null>(null);
  const [followups, setFollowups] = useState<WelfareFollowupOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [outcomeFilter, setOutcomeFilter] = useState<string>('ALL');

  // Modals state
  const [selectedFollowup, setSelectedFollowup] = useState<WelfareFollowupOut | null>(null);
  const [activeModal, setActiveModal] = useState<'schedule' | 'complete' | 'defer' | 'cancel' | 'create' | null>(null);

  // Form states
  const [scheduledAt, setScheduledAt] = useState<string>('');
  const [modalNotes, setModalNotes] = useState<string>('');
  const [deferDays, setDeferDays] = useState<number>(7);
  const [cancelReason, setCancelReason] = useState<string>('');
  const [triggerNewRec, setTriggerNewRec] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // Quick-create state
  const [newPersonnelId, setNewPersonnelId] = useState<number>(1);
  const [newFollowupType, setNewFollowupType] = useState<string>('WELFARE_CHECKIN');
  const [newReviewWindow, setNewReviewWindow] = useState<string>('Within 7 days');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const summary = await getUnitFollowupSummary().catch((err) => {
        console.warn('Unit follow-up summary fallback:', err);
        return null;
      });
      setAnalytics(summary);

      // Fetch sample personnel followups for display
      const listRes = await getPersonnelFollowups(1).catch(() => ({ followups: [] }));
      setFollowups(listRes.followups || []);
    } catch (err: any) {
      console.error('Failed to load follow-up telemetry:', err);
      setError(err?.message || 'Unable to load follow-up records from backend.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Action handlers
  const handleScheduleSubmit = async () => {
    if (!selectedFollowup || !scheduledAt) return;
    setActionLoading(true);
    try {
      await scheduleFollowup(selectedFollowup.id, {
        scheduled_at: new Date(scheduledAt).toISOString(),
        notes: modalNotes,
      });
      setActiveModal(null);
      await loadData();
    } catch (err: any) {
      alert(`Scheduling failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompleteSubmit = async () => {
    if (!selectedFollowup) return;
    setActionLoading(true);
    try {
      await completeFollowup(selectedFollowup.id, {
        notes: modalNotes,
        trigger_new_recommendation_if_worsening: triggerNewRec,
      });
      setActiveModal(null);
      await loadData();
    } catch (err: any) {
      alert(`Completion failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeferSubmit = async () => {
    if (!selectedFollowup) return;
    setActionLoading(true);
    try {
      await deferFollowup(selectedFollowup.id, {
        defer_days: deferDays,
        notes: modalNotes,
      });
      setActiveModal(null);
      await loadData();
    } catch (err: any) {
      alert(`Deferral failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelSubmit = async () => {
    if (!selectedFollowup || !cancelReason.trim()) return;
    setActionLoading(true);
    try {
      await cancelFollowup(selectedFollowup.id, {
        reason: cancelReason,
      });
      setActiveModal(null);
      await loadData();
    } catch (err: any) {
      alert(`Cancellation failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReassess = async (followupId: number) => {
    try {
      await reassessFollowupOutcome(followupId);
      await loadData();
    } catch (err: any) {
      alert(`Reassessment failed: ${err.message}`);
    }
  };

  const handleCreateSubmit = async () => {
    setActionLoading(true);
    try {
      await createFollowup({
        personnel_id: newPersonnelId,
        followup_type: newFollowupType,
        review_window: newReviewWindow,
        notes: modalNotes,
      });
      setActiveModal(null);
      await loadData();
    } catch (err: any) {
      alert(`Creation failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Filtered followups
  const filteredFollowups = followups.filter((f) => {
    if (statusFilter === 'OVERDUE') {
      if (!f.is_overdue) return false;
    } else if (statusFilter !== 'ALL' && f.status !== statusFilter) {
      return false;
    }
    if (outcomeFilter !== 'ALL' && f.outcome_status !== outcomeFilter) {
      return false;
    }
    return true;
  });

  const getOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case 'IMPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950/70 text-emerald-400 border border-emerald-800/40">
            <TrendingDown className="w-3.5 h-3.5" />
            IMPROVED
          </span>
        );
      case 'STABLE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-950/70 text-blue-400 border border-blue-800/40">
            <Activity className="w-3.5 h-3.5" />
            STABLE
          </span>
        );
      case 'PERSISTENT_CONCERN':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-950/70 text-amber-400 border border-amber-800/40">
            <AlertTriangle className="w-3.5 h-3.5" />
            PERSISTENT CONCERN
          </span>
        );
      case 'WORSENING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-950/70 text-rose-400 border border-rose-800/40">
            <TrendingUp className="w-3.5 h-3.5" />
            WORSENING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-700">
            <Clock className="w-3.5 h-3.5" />
            INSUFFICIENT DATA
          </span>
        );
    }
  };

  const getStatusBadge = (f: WelfareFollowupOut) => {
    if (f.is_overdue) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-rose-950 text-rose-300 border border-rose-800 animate-pulse">
          OVERDUE
        </span>
      );
    }
    switch (f.status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
            COMPLETED
          </span>
        );
      case 'SCHEDULED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-blue-950/60 text-blue-400 border border-blue-800/40">
            SCHEDULED
          </span>
        );
      case 'DEFERRED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/40">
            DEFERRED
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-900 text-slate-400 border border-slate-700">
            CANCELLED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-indigo-950/60 text-indigo-400 border border-indigo-800/40">
            PENDING
          </span>
        );
    }
  };

  return (
    <section className="bg-surface rounded-xl border border-surfaceHighlight p-6 space-y-6" id="welfare-followups-panel">
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-surfaceHighlight/60 pb-5">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-emerald-950/60 text-emerald-400 rounded-lg border border-emerald-800/40">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-textPrimary uppercase tracking-wide flex items-center gap-2">
                Phase 41: Welfare Follow-Up & Support Effectiveness
                <span className="text-[10px] px-2 py-0.5 bg-emerald-950/80 text-emerald-400 border border-emerald-800/50 rounded font-mono">
                  CLOSED-LOOP MONITORING
                </span>
              </h2>
              <p className="text-xs text-textSecondary font-mono mt-0.5">
                Objective post-intervention outcome tracking & longitudinal trajectory evaluation
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              setActiveModal('create');
              setModalNotes('');
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-900/60 hover:bg-emerald-800/80 text-emerald-200 border border-emerald-700/60 rounded-lg text-xs font-mono font-medium transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Initiate Follow-Up</span>
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-surfaceHighlight disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Ethical Guidance Banner */}
      <div className="p-3 bg-surfaceHighlight/30 border border-surfaceHighlight rounded-lg text-xs text-textSecondary flex items-start space-x-2.5">
        <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-textPrimary">Observational Monitoring Protocol:</strong> Follow-up outcome states are descriptive data observations derived from subsequent validated assessments. They do not constitute clinical recovery, fitness-for-duty decisions, or personnel performance appraisals.
        </p>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-surfaceHighlight/40 border border-surfaceHighlight/70 rounded-lg p-3.5">
          <span className="text-[11px] font-mono text-textSecondary block">Total Follow-Ups</span>
          <span className="text-2xl font-bold font-mono text-textPrimary mt-1 block">
            {analytics?.followups_total ?? followups.length}
          </span>
          <span className="text-[10px] text-textSecondary mt-0.5 block">Closed-loop records</span>
        </div>

        <div className="bg-surfaceHighlight/40 border border-surfaceHighlight/70 rounded-lg p-3.5">
          <span className="text-[11px] font-mono text-blue-400 block">Scheduled / Pending</span>
          <span className="text-2xl font-bold font-mono text-blue-300 mt-1 block">
            {(analytics?.followups_scheduled ?? 0) + (analytics?.followups_pending ?? 0)}
          </span>
          <span className="text-[10px] text-textSecondary mt-0.5 block">Awaiting completion</span>
        </div>

        <div className="bg-surfaceHighlight/40 border border-surfaceHighlight/70 rounded-lg p-3.5">
          <span className="text-[11px] font-mono text-emerald-400 block">Completed</span>
          <span className="text-2xl font-bold font-mono text-emerald-300 mt-1 block">
            {analytics?.followups_completed ?? 0}
          </span>
          <span className="text-[10px] text-textSecondary mt-0.5 block">Outcome recorded</span>
        </div>

        <div className="bg-surfaceHighlight/40 border border-surfaceHighlight/70 rounded-lg p-3.5">
          <span className="text-[11px] font-mono text-rose-400 block">Overdue</span>
          <span className="text-2xl font-bold font-mono text-rose-300 mt-1 block">
            {analytics?.followups_overdue ?? 0}
          </span>
          <span className="text-[10px] text-textSecondary mt-0.5 block">Review window passed</span>
        </div>

        <div className="bg-surfaceHighlight/40 border border-surfaceHighlight/70 rounded-lg p-3.5">
          <span className="text-[11px] font-mono text-amber-400 block">Persistent Concern</span>
          <span className="text-2xl font-bold font-mono text-amber-300 mt-1 block">
            {analytics?.persistent_concern_count ?? 0}
          </span>
          <span className="text-[10px] text-textSecondary mt-0.5 block">Sustained strain observed</span>
        </div>
      </div>

      {/* Outcome Distribution Tracker */}
      {analytics && !analytics.data_suppressed && analytics.outcome_distribution && (
        <div className="bg-surfaceHighlight/20 border border-surfaceHighlight/60 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold text-textPrimary uppercase">
              Unit Observational Outcome Trajectory
            </span>
            <span className="text-[11px] font-mono text-textSecondary">
              Scope: {analytics.scope_battalion || 'Authorized Battalion'}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {Object.entries(analytics.outcome_distribution).map(([key, val]) => (
              <div key={key} className="bg-surfaceHighlight/40 border border-surfaceHighlight/80 rounded p-2 text-center">
                <span className="text-[10px] font-mono text-textSecondary block uppercase">{key.replace('_', ' ')}</span>
                <span className="text-lg font-bold font-mono text-textPrimary mt-0.5 block">{val}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surfaceHighlight/60 pb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-mono text-textSecondary mr-1">Status:</span>
          {['ALL', 'PENDING', 'SCHEDULED', 'COMPLETED', 'OVERDUE', 'DEFERRED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                statusFilter === st
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-surfaceHighlight/40 text-textSecondary hover:text-textPrimary border border-transparent'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-mono text-textSecondary mr-1">Outcome:</span>
          {['ALL', 'IMPROVED', 'STABLE', 'PERSISTENT_CONCERN', 'WORSENING'].map((oc) => (
            <button
              key={oc}
              onClick={() => setOutcomeFilter(oc)}
              className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
                outcomeFilter === oc
                  ? 'bg-blue-950 text-blue-300 border border-blue-800'
                  : 'bg-surfaceHighlight/40 text-textSecondary hover:text-textPrimary border border-transparent'
              }`}
            >
              {oc.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Follow-Up Records Timeline & Cards */}
      <div className="space-y-4">
        {filteredFollowups.length === 0 ? (
          <div className="p-8 text-center bg-surfaceHighlight/20 rounded-lg border border-surfaceHighlight/40">
            <CheckCircle2 className="w-8 h-8 text-emerald-400/60 mx-auto mb-2" />
            <p className="text-sm font-mono text-textPrimary">No follow-up records found matching filter criteria.</p>
            <p className="text-xs text-textSecondary mt-1 font-mono">
              All welfare recommendations and interventions have completed follow-ups or no active entries exist.
            </p>
          </div>
        ) : (
          filteredFollowups.map((f) => (
            <div
              key={f.id}
              className="bg-surfaceHighlight/30 border border-surfaceHighlight/80 hover:border-surfaceHighlight rounded-lg p-5 space-y-4 transition-all"
            >
              {/* Header Info */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-surfaceHighlight/50 pb-3">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-surfaceHighlight rounded-lg border border-surfaceHighlight/70">
                    <UserCheck className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-bold text-textPrimary font-mono">
                        {f.personnel_name || `Cadet #${f.personnel_id}`}
                      </span>
                      <span className="text-xs text-textSecondary font-mono">({f.personnel_code || `P-${f.personnel_id}`})</span>
                      {getStatusBadge(f)}
                    </div>
                    <span className="text-[11px] text-textSecondary font-mono block mt-0.5">
                      {f.department || 'Infantry'} • {f.battalion || '1st Battalion'} • {f.location || 'Srinagar'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {getOutcomeBadge(f.outcome_status)}
                </div>
              </div>

              {/* Closed-Loop Pipeline Flow */}
              <div className="bg-surfaceHighlight/40 border border-surfaceHighlight/60 rounded-md p-3 text-xs font-mono flex flex-wrap items-center gap-2 text-textSecondary">
                <span className="text-textPrimary font-semibold">Workflow Loop:</span>
                <span className="px-2 py-0.5 bg-surfaceHighlight rounded text-[11px]">
                  Rec #{f.recommendation_id || 'N/A'}
                </span>
                <ArrowRight className="w-3 h-3" />
                <span className="px-2 py-0.5 bg-surfaceHighlight rounded text-[11px]">
                  Intervention #{f.intervention_id || 'Direct'}
                </span>
                <ArrowRight className="w-3 h-3" />
                <span className="px-2 py-0.5 bg-emerald-950/80 text-emerald-300 rounded text-[11px]">
                  {f.followup_type}
                </span>
                <ArrowRight className="w-3 h-3" />
                <span className="px-2 py-0.5 bg-blue-950/80 text-blue-300 rounded text-[11px]">
                  Outcome: {f.outcome_status}
                </span>
              </div>

              {/* Evidence & Objective Observation */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="bg-surfaceHighlight/30 border border-surfaceHighlight/50 rounded p-3 space-y-2">
                  <span className="text-textSecondary uppercase font-semibold block text-[10px]">
                    Baseline vs Follow-Up Comparison
                  </span>
                  <div className="space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-textSecondary">Baseline Source:</span>
                      <span className="text-textPrimary font-semibold">{f.baseline_source || 'PRE_ASSESSMENT'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-textSecondary">Baseline Score:</span>
                      <span className="text-textPrimary">
                        {f.evidence?.baseline_score != null ? `${f.evidence.baseline_score.toFixed(1)} pts (${f.evidence.baseline_category || 'N/A'})` : 'Awaiting baseline'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-textSecondary">Subsequent Score:</span>
                      <span className="text-textPrimary">
                        {f.evidence?.followup_score != null ? `${f.evidence.followup_score.toFixed(1)} pts (${f.evidence.followup_category || 'N/A'})` : 'Pending assessment'}
                      </span>
                    </div>
                    {f.evidence?.score_delta != null && (
                      <div className="flex justify-between border-t border-surfaceHighlight/60 pt-1.5">
                        <span className="text-textSecondary">Score Delta:</span>
                        <span className={`font-bold ${f.evidence.score_delta <= -5.0 ? 'text-emerald-400' : f.evidence.score_delta >= 5.0 ? 'text-rose-400' : 'text-blue-400'}`}>
                          {f.evidence.score_delta > 0 ? `+${f.evidence.score_delta}` : f.evidence.score_delta} pts
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-surfaceHighlight/30 border border-surfaceHighlight/50 rounded p-3 space-y-2">
                  <span className="text-textSecondary uppercase font-semibold block text-[10px]">
                    Observational Narrative
                  </span>
                  <p className="text-textPrimary leading-relaxed">
                    {f.evidence?.explanation || 'Follow-up observation pending subsequent assessment and review.'}
                  </p>
                  <div className="pt-2 border-t border-surfaceHighlight/60 flex items-center justify-between text-[11px] text-textSecondary">
                    <span>Review Window: {f.review_window || 'Not specified'}</span>
                    <span>Sufficiency: {f.evidence?.data_sufficiency || 'INSUFFICIENT'}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-surfaceHighlight/50">
                <span className="text-[11px] font-mono text-textSecondary">
                  {f.completed_at ? `Completed: ${new Date(f.completed_at).toLocaleDateString()}` : f.scheduled_at ? `Scheduled for: ${new Date(f.scheduled_at).toLocaleDateString()}` : `Created: ${new Date(f.created_at || '').toLocaleDateString()}`}
                </span>

                <div className="flex items-center space-x-2">
                  {f.status !== 'COMPLETED' && f.status !== 'CANCELLED' && (
                    <>
                      <button
                        onClick={() => {
                          setSelectedFollowup(f);
                          setActiveModal('schedule');
                          setScheduledAt(f.scheduled_at ? new Date(f.scheduled_at).toISOString().slice(0, 16) : '');
                          setModalNotes('');
                        }}
                        className="px-2.5 py-1 bg-blue-950/70 hover:bg-blue-900/90 text-blue-300 border border-blue-800/60 rounded text-xs font-mono font-medium transition-colors"
                      >
                        Schedule
                      </button>

                      <button
                        onClick={() => {
                          setSelectedFollowup(f);
                          setActiveModal('complete');
                          setModalNotes('');
                        }}
                        className="px-2.5 py-1 bg-emerald-950/70 hover:bg-emerald-900/90 text-emerald-300 border border-emerald-800/60 rounded text-xs font-mono font-medium transition-colors"
                      >
                        Complete
                      </button>

                      <button
                        onClick={() => {
                          setSelectedFollowup(f);
                          setActiveModal('defer');
                          setDeferDays(7);
                          setModalNotes('');
                        }}
                        className="px-2.5 py-1 bg-amber-950/70 hover:bg-amber-900/90 text-amber-300 border border-amber-800/60 rounded text-xs font-mono font-medium transition-colors"
                      >
                        Defer
                      </button>

                      <button
                        onClick={() => {
                          setSelectedFollowup(f);
                          setActiveModal('cancel');
                          setCancelReason('');
                        }}
                        className="px-2.5 py-1 bg-rose-950/70 hover:bg-rose-900/90 text-rose-300 border border-rose-800/60 rounded text-xs font-mono font-medium transition-colors"
                      >
                        Cancel
                      </button>
                    </>
                  )}

                  {f.status === 'COMPLETED' && (
                    <button
                      onClick={() => handleReassess(f.id)}
                      className="px-2.5 py-1 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded text-xs font-mono font-medium transition-colors border border-surfaceHighlight flex items-center space-x-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Re-evaluate Outcome</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* SCHEDULE MODAL */}
      {activeModal === 'schedule' && selectedFollowup && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-md w-full p-6 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-surfaceHighlight pb-3">
              <h3 className="text-sm font-bold text-textPrimary uppercase">Schedule Follow-Up</h3>
              <button onClick={() => setActiveModal(null)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-textSecondary block mb-1">Scheduled Date & Time:</label>
                <input
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={(e) => setScheduledAt(e.target.value)}
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>

              <div>
                <label className="text-textSecondary block mb-1">Review Notes / Agenda:</label>
                <textarea
                  rows={3}
                  value={modalNotes}
                  onChange={(e) => setModalNotes(e.target.value)}
                  placeholder="e.g. In-person discussion regarding duty schedule and recovery rest"
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-surfaceHighlight">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 bg-surfaceHighlight rounded text-xs text-textSecondary"
              >
                Close
              </button>
              <button
                onClick={handleScheduleSubmit}
                disabled={actionLoading || !scheduledAt}
                className="px-3 py-1.5 bg-blue-900 text-blue-100 rounded text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? 'Saving...' : 'Confirm Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* COMPLETE MODAL */}
      {activeModal === 'complete' && selectedFollowup && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-md w-full p-6 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-surfaceHighlight pb-3">
              <h3 className="text-sm font-bold text-textPrimary uppercase">Complete Follow-Up</h3>
              <button onClick={() => setActiveModal(null)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-textSecondary">
                Completing this follow-up will compare the post-intervention assessment with the baseline and determine the observational outcome state (IMPROVED, STABLE, PERSISTENT_CONCERN, or WORSENING).
              </p>

              <div>
                <label className="text-textSecondary block mb-1">Review Observations & Notes:</label>
                <textarea
                  rows={3}
                  value={modalNotes}
                  onChange={(e) => setModalNotes(e.target.value)}
                  placeholder="Record summary of discussion and observed state..."
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="triggerRec"
                  checked={triggerNewRec}
                  onChange={(e) => setTriggerNewRec(e.target.checked)}
                  className="rounded border-surfaceHighlight"
                />
                <label htmlFor="triggerRec" className="text-textSecondary text-[11px] cursor-pointer">
                  Trigger Phase 40 supportive recommendation if outcome reflects WORSENING or PERSISTENT_CONCERN
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-surfaceHighlight">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 bg-surfaceHighlight rounded text-xs text-textSecondary"
              >
                Close
              </button>
              <button
                onClick={handleCompleteSubmit}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-emerald-900 text-emerald-100 rounded text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? 'Recording...' : 'Record Outcome & Complete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DEFER MODAL */}
      {activeModal === 'defer' && selectedFollowup && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-md w-full p-6 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-surfaceHighlight pb-3">
              <h3 className="text-sm font-bold text-textPrimary uppercase">Defer Follow-Up Review</h3>
              <button onClick={() => setActiveModal(null)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-textSecondary block mb-1">Defer Days (1-90):</label>
                <input
                  type="number"
                  min={1}
                  max={90}
                  value={deferDays}
                  onChange={(e) => setDeferDays(parseInt(e.target.value) || 7)}
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>

              <div>
                <label className="text-textSecondary block mb-1">Operational Justification:</label>
                <textarea
                  rows={3}
                  value={modalNotes}
                  onChange={(e) => setModalNotes(e.target.value)}
                  placeholder="e.g. Personnel on sanctioned leave; defer until return to battalion"
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-surfaceHighlight">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 bg-surfaceHighlight rounded text-xs text-textSecondary"
              >
                Close
              </button>
              <button
                onClick={handleDeferSubmit}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-amber-900 text-amber-100 rounded text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? 'Saving...' : 'Confirm Deferral'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CANCEL MODAL */}
      {activeModal === 'cancel' && selectedFollowup && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-md w-full p-6 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-surfaceHighlight pb-3">
              <h3 className="text-sm font-bold text-textPrimary uppercase">Cancel Follow-Up</h3>
              <button onClick={() => setActiveModal(null)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-textSecondary block mb-1">Mandatory Cancellation Reason:</label>
                <textarea
                  rows={3}
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="e.g. Transfer to separate operational command, duplicate entry..."
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-surfaceHighlight">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 bg-surfaceHighlight rounded text-xs text-textSecondary"
              >
                Close
              </button>
              <button
                onClick={handleCancelSubmit}
                disabled={actionLoading || !cancelReason.trim()}
                className="px-3 py-1.5 bg-rose-900 text-rose-100 rounded text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? 'Processing...' : 'Confirm Cancellation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* INITIATE FOLLOW-UP MODAL */}
      {activeModal === 'create' && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-md w-full p-6 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-surfaceHighlight pb-3">
              <h3 className="text-sm font-bold text-textPrimary uppercase">Initiate Welfare Follow-Up</h3>
              <button onClick={() => setActiveModal(null)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-textSecondary block mb-1">Personnel ID:</label>
                <input
                  type="number"
                  min={1}
                  value={newPersonnelId}
                  onChange={(e) => setNewPersonnelId(parseInt(e.target.value) || 1)}
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>

              <div>
                <label className="text-textSecondary block mb-1">Follow-Up Type:</label>
                <select
                  value={newFollowupType}
                  onChange={(e) => setNewFollowupType(e.target.value)}
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                >
                  <option value="WELFARE_CHECKIN">WELFARE_CHECKIN (General Welfare)</option>
                  <option value="RECOVERY_REVIEW">RECOVERY_REVIEW (Workload & Rest)</option>
                  <option value="DUTY_SCHEDULE_REVIEW">DUTY_SCHEDULE_REVIEW (Shift Rotation)</option>
                  <option value="SUPPORT_RESOURCE_FOLLOWUP">SUPPORT_RESOURCE_FOLLOWUP (Resources Offered)</option>
                  <option value="REASSESSMENT">REASSESSMENT (Post-Concern Testing)</option>
                  <option value="INTERVENTION_REVIEW">INTERVENTION_REVIEW (Post-Intervention Review)</option>
                </select>
              </div>

              <div>
                <label className="text-textSecondary block mb-1">Review Window:</label>
                <select
                  value={newReviewWindow}
                  onChange={(e) => setNewReviewWindow(e.target.value)}
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                >
                  <option value="Within 24–48 hours">Within 24–48 hours</option>
                  <option value="Within 3–5 days">Within 3–5 days</option>
                  <option value="Within 7 days">Within 7 days</option>
                  <option value="Within 14 days">Within 14 days</option>
                  <option value="Within 30 days">Within 30 days</option>
                  <option value="NOT_SPECIFIED">NOT_SPECIFIED</option>
                </select>
              </div>

              <div>
                <label className="text-textSecondary block mb-1">Initial Notes:</label>
                <textarea
                  rows={2}
                  value={modalNotes}
                  onChange={(e) => setModalNotes(e.target.value)}
                  placeholder="Context and objective for this follow-up..."
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight rounded p-2 text-textPrimary"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-surfaceHighlight">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 bg-surfaceHighlight rounded text-xs text-textSecondary"
              >
                Close
              </button>
              <button
                onClick={handleCreateSubmit}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-emerald-900 text-emerald-100 rounded text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? 'Creating...' : 'Create Follow-Up'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
