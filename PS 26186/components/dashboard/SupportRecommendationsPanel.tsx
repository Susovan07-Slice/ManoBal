'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  getCommanderRecommendations,
  acknowledgeRecommendation,
  acceptRecommendation,
  deferRecommendation,
  dismissRecommendation,
  actionRecommendation,
} from '@/lib/recommendations';
import {
  CommanderRecommendationSummaryResponse,
  WelfareRecommendationOut,
  RecommendationPriority,
  RecommendationStatus,
} from '@/types/api';
import {
  Sparkles,
  Shield,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  RefreshCw,
  Info,
  Calendar,
  Layers,
  ChevronDown,
  ChevronUp,
  FileText,
  UserCheck,
  Send,
  XCircle,
  ExternalLink,
  Lock,
  Bell,
} from 'lucide-react';
import SendWelfareNotificationModal from './SendWelfareNotificationModal';

export default function SupportRecommendationsPanel() {
  const [data, setData] = useState<CommanderRecommendationSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [notifyModalRec, setNotifyModalRec] = useState<WelfareRecommendationOut | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  // Expanded card tracking
  const [expandedIds, setExpandedIds] = useState<Record<number, boolean>>({});

  // Modals state
  const [acceptModalRec, setAcceptModalRec] = useState<WelfareRecommendationOut | null>(null);
  const [acceptInterventionType, setAcceptInterventionType] = useState<string>('WELLNESS_CHECKIN');
  const [acceptCreateIntervention, setAcceptCreateIntervention] = useState<boolean>(true);
  const [acceptDate, setAcceptDate] = useState<string>('');
  const [acceptNotes, setAcceptNotes] = useState<string>('');

  const [deferModalRec, setDeferModalRec] = useState<WelfareRecommendationOut | null>(null);
  const [deferDays, setDeferDays] = useState<number>(7);
  const [deferNotes, setDeferNotes] = useState<string>('');

  const [dismissModalRec, setDismissModalRec] = useState<WelfareRecommendationOut | null>(null);
  const [dismissReason, setDismissReason] = useState<string>('');
  const [dismissError, setDismissError] = useState<string | null>(null);

  const [actionModalRec, setActionModalRec] = useState<WelfareRecommendationOut | null>(null);
  const [actionNotes, setActionNotes] = useState<string>('');
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCommanderRecommendations({
        status: statusFilter,
        priority: priorityFilter,
        recommendation_type: typeFilter,
      });
      setData(res);
    } catch (err: any) {
      console.error('Failed to load commander welfare recommendations:', err);
      setError(err?.message || 'Unable to retrieve welfare recommendations.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, typeFilter]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const toggleExpand = (id: number) => {
    setExpandedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleAcknowledge = async (rec: WelfareRecommendationOut) => {
    setActionLoadingId(rec.id);
    try {
      await acknowledgeRecommendation(rec.id, 'Acknowledged via Commander Dashboard review');
      await fetchRecommendations();
    } catch (err: any) {
      alert(`Failed to acknowledge recommendation: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleAcceptSubmit = async () => {
    if (!acceptModalRec) return;
    setActionLoadingId(acceptModalRec.id);
    try {
      await acceptRecommendation(acceptModalRec.id, {
        create_intervention: acceptCreateIntervention,
        intervention_type: acceptInterventionType,
        scheduled_date: acceptDate ? new Date(acceptDate).toISOString() : undefined,
        notes: acceptNotes || 'Accepted recommendation for supportive action',
      });
      setAcceptModalRec(null);
      setAcceptNotes('');
      await fetchRecommendations();
    } catch (err: any) {
      alert(`Failed to accept recommendation: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeferSubmit = async () => {
    if (!deferModalRec) return;
    setActionLoadingId(deferModalRec.id);
    try {
      await deferRecommendation(deferModalRec.id, {
        defer_days: deferDays,
        notes: deferNotes || `Deferred review for ${deferDays} days`,
      });
      setDeferModalRec(null);
      setDeferNotes('');
      await fetchRecommendations();
    } catch (err: any) {
      alert(`Failed to defer recommendation: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDismissSubmit = async () => {
    if (!dismissModalRec) return;
    if (!dismissReason.trim()) {
      setDismissError('A valid operational or welfare rationale is required to dismiss.');
      return;
    }
    setActionLoadingId(dismissModalRec.id);
    setDismissError(null);
    try {
      await dismissRecommendation(dismissModalRec.id, { reason: dismissReason.trim() });
      setDismissModalRec(null);
      setDismissReason('');
      await fetchRecommendations();
    } catch (err: any) {
      setDismissError(err?.message || 'Failed to dismiss recommendation');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleActionSubmit = async () => {
    if (!actionModalRec) return;
    if (!actionNotes.trim()) {
      setActionError('Action notes detailing supportive steps taken are required.');
      return;
    }
    setActionLoadingId(actionModalRec.id);
    setActionError(null);
    try {
      await actionRecommendation(actionModalRec.id, { action_notes: actionNotes.trim() });
      setActionModalRec(null);
      setActionNotes('');
      await fetchRecommendations();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to complete action');
    } finally {
      setActionLoadingId(null);
    }
  };

  // Badge styling helpers
  const getPriorityBadge = (p: RecommendationPriority) => {
    switch (p) {
      case 'CRITICAL':
        return 'bg-[#FAF0F0] text-[#964747] border-[#E8B4B4]';
      case 'HIGH':
        return 'bg-[#FDF2EC] text-[#8F4B33] border-[#F1C5B3]';
      case 'ELEVATED':
        return 'bg-[#FDF6EE] text-[#8E5B23] border-[#F3D2AE]';
      case 'ROUTINE':
      default:
        return 'bg-[#EEF6F2] text-[#2D6346] border-[#BBD9C7]';
    }
  };

  const getStatusBadge = (s: RecommendationStatus) => {
    switch (s) {
      case 'SUGGESTED':
        return 'bg-[#F4EFF8] text-[#69428E] border-[#DCCBEA]';
      case 'ACKNOWLEDGED':
        return 'bg-[#EEF4F8] text-[#3E6580] border-[#BCD3E3]';
      case 'ACCEPTED':
        return 'bg-[#EEF6F2] text-[#2D6346] border-[#BBD9C7]';
      case 'ACTIONED':
        return 'bg-[#E6EFE8] text-[#4F6E56] border-[#B5CFBB]';
      case 'DEFERRED':
        return 'bg-[#F1F5F9] text-[#64748B] border-[#CBD5E1]';
      case 'DISMISSED':
        return 'bg-[#F8FAFC] text-[#94A3B8] border-[#E2E8F0]';
      default:
        return 'bg-surfaceHighlight text-textSecondary border-surfaceBorder';
    }
  };

  const formatRecType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const recList = data?.recommendations || [];
  const totalActive = data?.total_active_recommendations || 0;
  const isSuppressed = data?.small_group_suppressed || false;

  return (
    <div id="welfare-recommendations" className="space-y-6">
      {/* Panel Header */}
      <div className="bg-surface border border-surfaceHighlight rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-textPrimary tracking-tight">
                  Welfare Recommendations & Support Actions
                </h2>
                <span className="hidden sm:inline-flex px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-surfaceHighlight text-textSecondary">
                  {totalActive} Active
                </span>
              </div>
              <p className="text-xs text-textSecondary mt-0.5">
                Explainable, non-punitive decision support for authorized unit reviewers and commanders
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 self-end md:self-auto">
            <button
              onClick={fetchRecommendations}
              disabled={loading}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-surfaceHighlight disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Small-Group Privacy Suppression Banner */}
        {isSuppressed && (
          <div className="mt-4 p-3.5 bg-amber-950/40 border border-amber-800/60 rounded-lg text-xs text-amber-200 flex items-start space-x-2.5">
            <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-300">Privacy Protection Threshold Active</p>
              <p className="mt-0.5 leading-relaxed text-amber-200/90">
                Individual recommendation details are suppressed because the unit size in scope is below the minimum threshold (5 personnel). This prevents re-identification and protects personnel confidentiality.
              </p>
            </div>
          </div>
        )}

        {/* Filter Controls */}
        <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-surfaceHighlight/60">
          <div>
            <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
              Filter by Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg px-3 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
            >
              <option value="ALL">All Statuses</option>
              <option value="SUGGESTED">Suggested (New)</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="ACTIONED">Actioned (Completed)</option>
              <option value="DEFERRED">Deferred</option>
              <option value="DISMISSED">Dismissed</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
              Filter by Priority
            </label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg px-3 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="ELEVATED">Elevated</option>
              <option value="ROUTINE">Routine</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
              Filter by Type
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg px-3 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
            >
              <option value="ALL">All Types</option>
              <option value="RECOVERY_REVIEW">Recovery Review</option>
              <option value="DUTY_SCHEDULE_REVIEW">Duty Schedule Review</option>
              <option value="WELFARE_FOLLOW_UP">Welfare Follow-up</option>
              <option value="VOLUNTARY_WELLNESS_CHECKIN">Voluntary Wellness Check-in</option>
              <option value="SUPPORT_RESOURCE_REFERRAL">Support Resource Referral</option>
              <option value="FOLLOW_UP_ASSESSMENT">Follow-up Assessment</option>
              <option value="CONTINUE_MONITORING">Continue Monitoring</option>
              <option value="HUMAN_REVIEW">Human Review</option>
            </select>
          </div>
        </div>

        {/* Metrics Row */}
        {data && !isSuppressed && (
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 border-t border-surfaceHighlight/40 text-center">
            <div className="p-2 rounded-lg bg-surfaceHighlight/20">
              <span className="text-[10px] font-mono uppercase text-textSecondary">Suggested</span>
              <p className="text-base font-bold text-purple-400">
                {data.status_breakdown?.['SUGGESTED'] || 0}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-surfaceHighlight/20">
              <span className="text-[10px] font-mono uppercase text-textSecondary">Acknowledged</span>
              <p className="text-base font-bold text-cyan-400">
                {data.status_breakdown?.['ACKNOWLEDGED'] || 0}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-surfaceHighlight/20">
              <span className="text-[10px] font-mono uppercase text-textSecondary">Accepted / Actioned</span>
              <p className="text-base font-bold text-emerald-400">
                {(data.status_breakdown?.['ACCEPTED'] || 0) + (data.status_breakdown?.['ACTIONED'] || 0)}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-surfaceHighlight/40 border border-surfaceBorder">
              <span className="text-[10px] font-mono uppercase text-textSecondary">High/Critical Priority</span>
              <p className="text-base font-bold text-[#C26D6D]">
                {(data.priority_breakdown?.['HIGH'] || 0) + (data.priority_breakdown?.['CRITICAL'] || 0)}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-[#FAF0F0] border border-[#E8B4B4] rounded-xl flex items-center space-x-3 text-[#964747] text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0 text-[#C26D6D]" />
          <p>{error}</p>
        </div>
      )}

      {/* Recommendations List */}
      {!isSuppressed && !error && (
        <div className="space-y-4">
          {recList.length === 0 ? (
            <div className="p-8 text-center bg-surface border border-surfaceHighlight rounded-xl">
              <Sparkles className="w-8 h-8 text-indigo-400/50 mx-auto mb-2" />
              <p className="text-sm font-medium text-textPrimary">No recommendations found</p>
              <p className="text-xs text-textSecondary mt-1">
                All personnel welfare indicators within current scope are within nominal bounds.
              </p>
            </div>
          ) : (
            recList.map((rec) => {
              const isExpanded = !!expandedIds[rec.id];
              const isLoading = actionLoadingId === rec.id;

              return (
                <div
                  key={rec.id}
                  className="bg-surface border border-surfaceHighlight hover:border-surfaceHighlight/80 rounded-xl transition-all shadow-sm overflow-hidden"
                >
                  {/* Card Header */}
                  <div className="p-4 sm:p-5">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold border ${getPriorityBadge(
                              rec.priority
                            )}`}
                          >
                            {rec.priority}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-surfaceHighlight text-textSecondary border border-surfaceHighlight">
                            {formatRecType(rec.recommendation_type)}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${getStatusBadge(
                              rec.status
                            )}`}
                          >
                            {rec.status}
                          </span>
                          {rec.recommended_review_window && (
                            <span className="inline-flex items-center text-[11px] text-textSecondary font-mono space-x-1">
                              <Clock className="w-3 h-3 text-textSecondary/70 inline" />
                              <span>{rec.recommended_review_window}</span>
                            </span>
                          )}
                        </div>

                        <h3 className="text-base font-semibold text-textPrimary pt-0.5">
                          {rec.title}
                        </h3>

                        <p className="text-xs text-textSecondary leading-relaxed">
                          {rec.description || rec.recommendation_text}
                        </p>

                        {/* Personnel Meta info */}
                        <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] font-mono text-textSecondary">
                          <span>
                            Personnel:{' '}
                            <strong className="text-textPrimary font-semibold">
                              {rec.personnel_name || `#${rec.personnel_code || rec.personnel_id}`}
                            </strong>
                          </span>
                          {rec.battalion && <span>• Battalion: {rec.battalion}</span>}
                          {rec.location && <span>• Location: {rec.location}</span>}
                          <span>• Confidence: {rec.confidence}</span>
                        </div>
                      </div>

                      {/* Top Action Controls */}
                      <div className="flex items-center space-x-2 self-start pt-1">
                        <button
                          onClick={() => toggleExpand(rec.id)}
                          className="flex items-center space-x-1 px-2.5 py-1 text-xs text-textSecondary hover:text-textPrimary hover:bg-surfaceHighlight rounded-lg transition-colors font-mono"
                        >
                          <span>{isExpanded ? 'Less' : 'Evidence'}</span>
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Source Signals Pills */}
                    {rec.source_signals && rec.source_signals.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-surfaceHighlight/50 flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-mono uppercase text-textSecondary mr-1">
                          Source Signals:
                        </span>
                        {rec.source_signals.map((sig, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-surfaceHighlight/40 text-textSecondary border border-surfaceHighlight/60"
                          >
                            {sig}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Expandable Traceability & Evidence Drawer */}
                    {isExpanded && (
                      <div className="mt-4 p-4 rounded-lg bg-surfaceHighlight/20 border border-surfaceHighlight/60 space-y-3 text-xs">
                        <div>
                          <span className="font-semibold text-textPrimary uppercase tracking-wider text-[10px] font-mono">
                            Supportive Rationale & Trigger
                          </span>
                          <p className="mt-1 text-textSecondary leading-relaxed">
                            {rec.reason || 'Triggered by continuous multi-modal signal aggregation.'}
                          </p>
                        </div>

                        {/* Evidence Metrics */}
                        {rec.evidence?.evidence_metrics &&
                          Object.keys(rec.evidence.evidence_metrics).length > 0 && (
                            <div>
                              <span className="font-semibold text-textPrimary uppercase tracking-wider text-[10px] font-mono">
                                Quantified Evidence Metrics
                              </span>
                              <div className="mt-1.5 grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {Object.entries(rec.evidence.evidence_metrics).map(([k, v]) => (
                                  <div
                                    key={k}
                                    className="p-2 rounded bg-surfaceHighlight/40 border border-surfaceHighlight text-[11px] font-mono"
                                  >
                                    <span className="text-textSecondary block text-[10px]">
                                      {k.replace(/_/g, ' ')}:
                                    </span>
                                    <span className="text-textPrimary font-semibold">
                                      {typeof v === 'number' ? v.toFixed(1) : String(v)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                        {/* Traceability links */}
                        <div className="pt-2 border-t border-surfaceHighlight/40 flex flex-wrap gap-3 text-[11px] font-mono text-textSecondary">
                          {rec.linked_alert_id && (
                            <span className="text-amber-400">
                              Linked Alert #{rec.linked_alert_id}
                            </span>
                          )}
                          {rec.linked_anomaly_id && (
                            <span className="text-rose-400">
                              Linked Anomaly #{rec.linked_anomaly_id}
                            </span>
                          )}
                          {rec.linked_intervention_id && (
                            <span className="text-emerald-400">
                              Linked Phase 37 Intervention #{rec.linked_intervention_id}
                            </span>
                          )}
                          {rec.action_notes && (
                            <div className="w-full mt-1 p-2 rounded bg-teal-950/20 border border-teal-800/40 text-teal-300">
                              <strong>Recorded Action:</strong> {rec.action_notes}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Reviewer Action Buttons */}
                    <div className="mt-4 pt-3 border-t border-surfaceHighlight/60 flex flex-wrap items-center justify-between gap-2">
                      <div className="text-[11px] font-mono text-textSecondary">
                        Updated {new Date(rec.updated_at).toLocaleDateString()}
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        {rec.status === 'SUGGESTED' && (
                          <button
                            onClick={() => handleAcknowledge(rec)}
                            disabled={isLoading}
                            className="flex items-center space-x-1.5 px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-lg text-xs font-mono font-medium transition-colors disabled:opacity-50"
                          >
                            <UserCheck className="w-3.5 h-3.5" />
                            <span>Acknowledge</span>
                          </button>
                        )}

                        {(rec.status === 'SUGGESTED' || rec.status === 'ACKNOWLEDGED') && (
                          <button
                            onClick={() => {
                              setAcceptModalRec(rec);
                              setAcceptDate(new Date().toISOString().slice(0, 16));
                            }}
                            disabled={isLoading}
                            className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-mono font-medium transition-colors disabled:opacity-50"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Accept & Plan Support</span>
                          </button>
                        )}

                        {(rec.status === 'SUGGESTED' ||
                          rec.status === 'ACKNOWLEDGED' ||
                          rec.status === 'ACCEPTED') && (
                          <button
                            onClick={() => setActionModalRec(rec)}
                            disabled={isLoading}
                            className="flex items-center space-x-1.5 px-3 py-1.5 bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 rounded-lg text-xs font-mono font-medium transition-colors disabled:opacity-50"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>Record Action</span>
                          </button>
                        )}

                        {(rec.status === 'SUGGESTED' || rec.status === 'ACKNOWLEDGED') && (
                          <button
                            onClick={() => setDeferModalRec(rec)}
                            disabled={isLoading}
                            className="flex items-center space-x-1.5 px-2.5 py-1.5 text-textSecondary hover:bg-surfaceHighlight rounded-lg text-xs font-mono font-medium transition-colors disabled:opacity-50"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                            <span>Defer</span>
                          </button>
                        )}

                        {(rec.status === 'SUGGESTED' || rec.status === 'ACKNOWLEDGED') && (
                          <button
                            onClick={() => setDismissModalRec(rec)}
                            disabled={isLoading}
                            className="flex items-center space-x-1.5 px-2.5 py-1.5 text-zinc-400 hover:bg-surfaceHighlight rounded-lg text-xs font-mono font-medium transition-colors disabled:opacity-50"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Dismiss</span>
                          </button>
                        )}

                        {rec.status === 'ACTIONED' && (
                          <span className="inline-flex items-center space-x-1 px-3 py-1 bg-teal-950/40 text-teal-300 border border-teal-800/40 rounded-lg text-xs font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Action Completed</span>
                          </span>
                        )}

                        <button
                          onClick={() => setNotifyModalRec(rec)}
                          className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-mono font-medium transition-colors"
                        >
                          <Bell className="w-3.5 h-3.5" />
                          <span>Notify Jawan</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* ACCEPT & PLAN MODAL */}
      {acceptModalRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-lg w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-surfaceHighlight">
              <h3 className="font-semibold text-textPrimary text-sm flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-[#7BA083]" />
                <span>Accept Recommendation & Initiate Support</span>
              </h3>
              <button
                onClick={() => setAcceptModalRec(null)}
                className="text-textSecondary hover:text-textPrimary"
              >
                &times;
              </button>
            </div>

            <div className="p-3 bg-surfaceHighlight/30 rounded-lg text-xs text-textSecondary">
              <strong className="text-textPrimary block">{acceptModalRec.title}</strong>
              <p className="mt-0.5">{acceptModalRec.recommendation_text}</p>
            </div>

            <div className="space-y-3">
              <label className="flex items-center space-x-2 text-xs text-textPrimary">
                <input
                  type="checkbox"
                  checked={acceptCreateIntervention}
                  onChange={(e) => setAcceptCreateIntervention(e.target.checked)}
                  className="rounded border-surfaceHighlight bg-surfaceHighlight/40 text-accent focus:ring-accent"
                />
                <span>Schedule Phase 37 Supportive Welfare Intervention</span>
              </label>

              {acceptCreateIntervention && (
                <div className="space-y-3 pl-5 border-l-2 border-surfaceHighlight">
                  <div>
                    <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
                      Intervention Type
                    </label>
                    <select
                      value={acceptInterventionType}
                      onChange={(e) => setAcceptInterventionType(e.target.value)}
                      className="w-full bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg px-3 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
                    >
                      <option value="WELLNESS_CHECKIN">Voluntary Wellness Check-in</option>
                      <option value="MANDATORY_REST_INTERVAL">Rest / Recovery Interval</option>
                      <option value="COUNSELING_SESSION">Support Counseling Session</option>
                      <option value="DUTY_SCHEDULE_ADJUSTMENT">Duty Schedule Adjustment</option>
                      <option value="PEER_SUPPORT">Peer Buddy Support Assignment</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
                      Scheduled Date & Time
                    </label>
                    <input
                      type="datetime-local"
                      value={acceptDate}
                      onChange={(e) => setAcceptDate(e.target.value)}
                      className="w-full bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg px-3 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
                  Support Review Notes
                </label>
                <textarea
                  value={acceptNotes}
                  onChange={(e) => setAcceptNotes(e.target.value)}
                  placeholder="Record planned steps or supervisor coordination details..."
                  className="w-full h-20 bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg p-2.5 text-xs text-textPrimary focus:outline-none focus:border-accent resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-surfaceHighlight">
              <button
                onClick={() => setAcceptModalRec(null)}
                className="px-3 py-1.5 text-xs font-mono text-textSecondary hover:bg-surfaceHighlight rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleAcceptSubmit}
                disabled={actionLoadingId === acceptModalRec.id}
                className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-xs font-mono font-medium disabled:opacity-50"
              >
                Confirm Acceptance
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DEFER MODAL */}
      {deferModalRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-surfaceHighlight">
              <h3 className="font-semibold text-textPrimary text-sm flex items-center space-x-2">
                <RotateCcw className="w-4 h-4 text-slate-400" />
                <span>Defer Recommendation Review</span>
              </h3>
              <button
                onClick={() => setDeferModalRec(null)}
                className="text-textSecondary hover:text-textPrimary"
              >
                &times;
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
                  Defer Review By
                </label>
                <select
                  value={deferDays}
                  onChange={(e) => setDeferDays(Number(e.target.value))}
                  className="w-full bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg px-3 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
                >
                  <option value={7}>7 Days (1 Week)</option>
                  <option value={14}>14 Days (2 Weeks)</option>
                  <option value={30}>30 Days (1 Month)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
                  Deferral Context / Notes
                </label>
                <textarea
                  value={deferNotes}
                  onChange={(e) => setDeferNotes(e.target.value)}
                  placeholder="e.g., Awaiting upcoming unit rotation cycle before review..."
                  className="w-full h-20 bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg p-2.5 text-xs text-textPrimary focus:outline-none focus:border-accent resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-surfaceHighlight">
              <button
                onClick={() => setDeferModalRec(null)}
                className="px-3 py-1.5 text-xs font-mono text-textSecondary hover:bg-surfaceHighlight rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleDeferSubmit}
                disabled={actionLoadingId === deferModalRec.id}
                className="px-4 py-1.5 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-xs font-mono font-medium disabled:opacity-50"
              >
                Confirm Deferral
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DISMISS MODAL */}
      {dismissModalRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-surface border border-surfaceBorder rounded-xl max-w-md w-full p-5 space-y-4 shadow-elevated">
            <div className="flex items-center justify-between pb-3 border-b border-surfaceBorder">
              <h3 className="font-semibold text-textPrimary text-sm flex items-center space-x-2">
                <XCircle className="w-4 h-4 text-textSecondary" />
                <span>Dismiss Recommendation</span>
              </h3>
              <button
                onClick={() => setDismissModalRec(null)}
                className="text-textSecondary hover:text-textPrimary"
              >
                &times;
              </button>
            </div>

            {dismissError && (
              <div className="p-3 bg-[#FAF0F0] border border-[#E8B4B4] rounded-lg text-xs text-[#964747]">
                {dismissError}
              </div>
            )}

            <div className="space-y-3">
              <p className="text-xs text-textSecondary">
                Dismissing marks this recommendation as reviewed with no further action required.
                A clear, non-punitive rationale must be recorded for audit purposes.
              </p>

              <div>
                <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
                  Dismissal Rationale (Required)
                </label>
                <textarea
                  value={dismissReason}
                  onChange={(e) => setDismissReason(e.target.value)}
                  placeholder="e.g., Personnel currently on sanctioned leave; telemetry anomaly verified as sensor charging gap."
                  className="w-full h-24 bg-[#F1F7F4] border border-surfaceBorder rounded-lg p-2.5 text-xs text-textPrimary focus:outline-none focus:border-accent resize-none placeholder:text-textSecondary"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-surfaceBorder">
              <button
                onClick={() => setDismissModalRec(null)}
                className="px-3 py-1.5 text-xs font-mono text-textSecondary hover:bg-surfaceHighlight rounded-lg border border-surfaceBorder"
              >
                Cancel
              </button>
              <button
                onClick={handleDismissSubmit}
                disabled={actionLoadingId === dismissModalRec.id}
                className="px-4 py-1.5 bg-[#64748B] hover:bg-[#475569] text-[#FAFAFC] rounded-lg text-xs font-mono font-medium disabled:opacity-50"
              >
                Confirm Dismissal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* RECORD ACTION MODAL */}
      {actionModalRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-surface border border-surfaceBorder rounded-xl max-w-md w-full p-5 space-y-4 shadow-elevated">
            <div className="flex items-center justify-between pb-3 border-b border-surfaceBorder">
              <h3 className="font-semibold text-textPrimary text-sm flex items-center space-x-2">
                <Send className="w-4 h-4 text-accent" />
                <span>Record Supportive Action Taken</span>
              </h3>
              <button
                onClick={() => setActionModalRec(null)}
                className="text-textSecondary hover:text-textPrimary"
              >
                &times;
              </button>
            </div>

            {actionError && (
              <div className="p-3 bg-[#FAF0F0] border border-[#E8B4B4] rounded-lg text-xs text-[#964747]">
                {actionError}
              </div>
            )}

            <div className="space-y-3">
              <p className="text-xs text-textSecondary">
                Record the supportive adjustments or welfare coordination completed with the individual.
              </p>

              <div>
                <label className="block text-[11px] font-mono text-textSecondary uppercase mb-1">
                  Action Summary (Required)
                </label>
                <textarea
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder="e.g., Met with personnel during morning muster; scheduled 48-hour recovery rotation and assigned peer buddy."
                  className="w-full h-24 bg-[#F1F7F4] border border-surfaceBorder rounded-lg p-2.5 text-xs text-textPrimary focus:outline-none focus:border-accent resize-none placeholder:text-textSecondary"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-surfaceBorder">
              <button
                onClick={() => setActionModalRec(null)}
                className="px-3 py-1.5 text-xs font-mono text-textSecondary hover:bg-surfaceHighlight rounded-lg border border-surfaceBorder"
              >
                Cancel
              </button>
              <button
                onClick={handleActionSubmit}
                disabled={actionLoadingId === actionModalRec.id}
                className="px-4 py-1.5 bg-accent hover:bg-accent/90 text-[#FAFAFC] rounded-lg text-xs font-mono font-medium disabled:opacity-50"
              >
                Save & Complete Action
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Phase 47: Send Welfare Notification Modal */}
      {notifyModalRec && (
        <SendWelfareNotificationModal
          isOpen={!!notifyModalRec}
          onClose={() => setNotifyModalRec(null)}
          personnelId={notifyModalRec.personnel_id}
          personnelCode={notifyModalRec.personnel_code || undefined}
          personnelName={notifyModalRec.personnel_name || undefined}
          battalion={notifyModalRec.battalion || undefined}
          initialType="SUPPORT_RECOMMENDATION"
          initialTitle={`Support Recommendation: ${notifyModalRec.title || 'Guidance'}`}
          initialMessage={notifyModalRec.recommendation_text || 'Supportive guidance and wellness resources have been arranged for you.'}
          initialActionUrl="/trends"
          sourceType="RECOMMENDATION"
          sourceId={notifyModalRec.id}
        />
      )}
    </div>
  );
}
