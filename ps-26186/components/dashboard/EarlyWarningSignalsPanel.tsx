'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  getCommanderAnomalies,
  acknowledgeAnomaly,
  reviewAnomaly,
  resolveAnomaly,
} from '@/lib/anomalies';
import { CommanderAnomalySummaryResponse, WelfareAnomalyOut } from '@/types/api';
import {
  Radar,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Lock,
  RefreshCw,
  Info,
  TrendingUp,
  Moon,
  Zap,
  Briefcase,
  Layers,
  Building,
  UserCheck,
  FileText,
  Calendar,
  ShieldCheck,
  Bell,
  ArrowRight,
  ExternalLink,
  X,
} from 'lucide-react';

const REVIEW_DECISIONS = [
  { value: 'CONTINUE_MONITORING', label: 'Continue Monitoring', desc: 'Observe baseline trend over next cycle' },
  { value: 'CONTACT_PERSONNEL', label: 'Contact Personnel', desc: 'Informal welfare check-in with Jawan' },
  { value: 'OFFER_WELFARE_SUPPORT', label: 'Offer Welfare Support', desc: 'Provide access to wellness resources' },
  { value: 'REVIEW_DUTY_WORKLOAD', label: 'Review Duty / Workload', desc: 'Evaluate roster and recovery allocation' },
  { value: 'SCHEDULE_FOLLOW_UP', label: 'Schedule Follow-up', desc: 'Formal longitudinal follow-up check' },
  { value: 'CREATE_WELFARE_CASE', label: 'Create / Link Welfare Case', desc: 'Open multi-disciplinary welfare case' },
  { value: 'RESOLVE_SIGNAL', label: 'Resolve Signal', desc: 'Conclude signal with resolution notification' },
];

export default function EarlyWarningSignalsPanel() {
  const [data, setData] = useState<CommanderAnomalySummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Review modal state
  const [selectedAnomalyForReview, setSelectedAnomalyForReview] = useState<WelfareAnomalyOut | null>(null);
  const [reviewDecision, setReviewDecision] = useState<string>('CONTINUE_MONITORING');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [reviewError, setReviewError] = useState<string | null>(null);

  // Resolution modal state
  const [selectedAnomalyForResolve, setSelectedAnomalyForResolve] = useState<WelfareAnomalyOut | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [notifyPersonnel, setNotifyPersonnel] = useState<boolean>(true);
  const [customMessage, setCustomMessage] = useState<string>(
    'Your recent welfare signal has been reviewed and resolved by your welfare officer. Please continue to monitor your wellbeing and contact your welfare officer if you need support.'
  );
  const [resolveError, setResolveError] = useState<string | null>(null);

  const fetchAnomalies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCommanderAnomalies();
      setData(res);
    } catch (err: any) {
      console.error('Failed to load commander early-warning anomalies:', err);
      setError(err?.message || 'Unable to retrieve early-warning signals.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnomalies();
  }, [fetchAnomalies]);

  const handleAcknowledge = async (anomalyId: number) => {
    setActionLoadingId(anomalyId);
    setSuccessBanner(null);
    try {
      await acknowledgeAnomaly(anomalyId);
      setSuccessBanner('Signal acknowledged successfully.');
      await fetchAnomalies();
    } catch (err: any) {
      alert(`Failed to acknowledge anomaly: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const openReviewModal = (anom: WelfareAnomalyOut) => {
    setSelectedAnomalyForReview(anom);
    setReviewDecision(anom.review_decision || 'CONTINUE_MONITORING');
    setReviewNotes(anom.review_notes || '');
    setReviewError(null);
  };

  const handleReviewSubmit = async () => {
    if (!selectedAnomalyForReview) return;
    setActionLoadingId(selectedAnomalyForReview.id);
    setReviewError(null);
    setSuccessBanner(null);
    try {
      await reviewAnomaly(selectedAnomalyForReview.id, {
        decision: reviewDecision,
        notes: reviewNotes.trim() ? reviewNotes.trim() : undefined,
      });
      const closedAnom = selectedAnomalyForReview;
      setSelectedAnomalyForReview(null);
      setSuccessBanner(`Signal review recorded (${reviewDecision.replace(/_/g, ' ')}).`);
      await fetchAnomalies();

      // If decision was to resolve signal, seamlessly open resolution modal
      if (reviewDecision === 'RESOLVE_SIGNAL') {
        openResolveModal(closedAnom);
      }
    } catch (err: any) {
      setReviewError(err?.message || 'Failed to record review.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const openResolveModal = (anom: WelfareAnomalyOut) => {
    setSelectedAnomalyForReview(null);
    setSelectedAnomalyForResolve(anom);
    setResolutionNotes(
      anom.review_notes
        ? `Welfare review completed. ${anom.review_notes}`
        : 'Reviewed duty pattern and welfare metrics. Personnel contacted and recovery support provided.'
    );
    setNotifyPersonnel(!!anom.personnel_id);
    setCustomMessage(
      'Your recent welfare signal has been reviewed and resolved by your welfare officer. Please continue to monitor your wellbeing and contact your welfare officer if you need support.'
    );
    setResolveError(null);
  };

  const handleResolveSubmit = async () => {
    if (!selectedAnomalyForResolve) return;
    if (!resolutionNotes.trim() || resolutionNotes.trim().length < 3) {
      setResolveError('Resolution notes explaining supportive actions are required (min 3 characters).');
      return;
    }
    setActionLoadingId(selectedAnomalyForResolve.id);
    setResolveError(null);
    setSuccessBanner(null);
    try {
      await resolveAnomaly(selectedAnomalyForResolve.id, {
        resolution_notes: resolutionNotes.trim(),
        notify_personnel: notifyPersonnel,
        custom_message: notifyPersonnel && customMessage.trim() ? customMessage.trim() : undefined,
      });
      setSelectedAnomalyForResolve(null);
      setResolutionNotes('');
      setSuccessBanner(
        notifyPersonnel && selectedAnomalyForResolve.personnel_id
          ? 'Signal resolved successfully and supportive notification delivered to Jawan.'
          : 'Signal resolved successfully.'
      );
      await fetchAnomalies();
    } catch (err: any) {
      setResolveError(err?.message || 'Failed to resolve anomaly.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const getAnomalyTypeIcon = (type: string) => {
    switch (type) {
      case 'RAPID_RISK_CHANGE':
        return <Zap className="w-4 h-4 text-[#C26D6D]" />;
      case 'RAPID_RISK_ACCELERATION':
        return <TrendingUp className="w-4 h-4 text-[#CB7A5C]" />;
      case 'WORKLOAD_ANOMALY':
        return <Briefcase className="w-4 h-4 text-[#D99B5C]" />;
      case 'SLEEP_RECOVERY_ANOMALY':
        return <Moon className="w-4 h-4 text-[#5B88A5]" />;
      case 'NIGHT_SHIFT_PATTERN_CHANGE':
        return <Clock className="w-4 h-4 text-[#69428E]" />;
      case 'WELFARE_FACTOR_CLUSTER':
        return <Layers className="w-4 h-4 text-[#C26D6D]" />;
      case 'UNIT_LEVEL_ANOMALY':
        return <Building className="w-4 h-4 text-accent" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-accent" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'URGENT_REVIEW':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]">
            URGENT REVIEW
          </span>
        );
      case 'ATTENTION':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#FDF6EE] text-[#8E5B23] border border-[#F3D2AE]">
            ATTENTION
          </span>
        );
      case 'WATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-[#EEF4F8] text-[#3E6580] border border-[#BCD3E3]">
            WATCH
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-surfaceHighlight text-textSecondary border border-surfaceBorder">
            INFO
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#EEF8F1] text-[#2B613B] border border-[#A8DBB5] flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>RESOLVED</span>
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#EBF3FB] text-[#285780] border border-[#ABCBE8] flex items-center space-x-1">
            <Clock className="w-3 h-3" />
            <span>UNDER REVIEW</span>
          </span>
        );
      case 'ACKNOWLEDGED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase bg-surfaceHighlight text-textPrimary border border-surfaceBorder">
            ACKNOWLEDGED
          </span>
        );
      case 'DETECTED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase bg-[#FFF9E6] text-[#7A5B04] border border-[#E8D49E]">
            NEW SIGNAL
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-surface text-textSecondary border border-surfaceBorder">
            {status}
          </span>
        );
    }
  };

  const filteredAnomalies =
    data?.anomalies.filter((a) => {
      if (filterType === 'ALL') return true;
      return a.anomaly_type === filterType;
    }) || [];

  return (
    <div className="bg-surface border border-surfaceBorder rounded-xl p-6 space-y-6 shadow-card" id="early-warning-signals">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surfaceBorder">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center">
              <Radar className="w-4 h-4 text-accent" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-textPrimary uppercase tracking-wider">
                  Early-Warning & Welfare Anomaly Signals
                </h2>
              </div>
              <p className="text-xs text-textSecondary font-mono mt-0.5">
                Baseline-First Personal & Unit-Level Anomaly Detection • Human Decision-Support Only
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchAnomalies}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono transition-colors border border-surfaceBorder disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Signals</span>
        </button>
      </div>

      {/* Success Confirmation Banner */}
      {successBanner && (
        <div className="p-3.5 bg-[#EEF8F1] border border-[#A8DBB5] rounded-lg text-[#2B613B] text-xs font-mono flex items-center justify-between animate-fadeIn">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-[#2B613B]" />
            <span>{successBanner}</span>
          </div>
          <button
            onClick={() => setSuccessBanner(null)}
            className="text-[#2B613B] hover:opacity-75 font-mono text-sm ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 bg-surfaceHighlight/50 rounded-lg"></div>
            ))}
          </div>
          <div className="h-32 bg-surfaceHighlight/50 rounded-lg"></div>
        </div>
      )}

      {/* Error Alert */}
      {!loading && error && (
        <div className="p-4 bg-[#FAF0F0] border border-[#E8B4B4] rounded-lg flex items-center space-x-3 text-[#964747] text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0 text-[#C26D6D]" />
          <div>
            <p className="font-semibold">Early-Warning Engine Notice</p>
            <p className="text-xs text-[#964747] mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Small Group Privacy Protection */}
      {!loading && data?.status === 'INSUFFICIENT_GROUP_SIZE' && (
        <div className="p-5 bg-[#FDF6EE] border border-[#F3D2AE] rounded-lg space-y-2">
          <div className="flex items-center space-x-2.5">
            <Lock className="w-4 h-4 text-[#8E5B23]" />
            <h3 className="text-xs font-bold text-[#8E5B23] uppercase tracking-wide">
              k-Anonymity Privacy Suppression Activated
            </h3>
          </div>
          <p className="text-xs text-textSecondary leading-relaxed">
            {data.message ||
              'Early-warning anomaly signals are withheld for units below the privacy threshold to prevent deductive re-identification of vulnerable personnel.'}
          </p>
        </div>
      )}

      {/* Active Content */}
      {!loading && data && data.status === 'SUCCESS' && (
        <div className="space-y-6">
          {/* Top Severity Counters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-surfaceHighlight/40 border border-surfaceBorder rounded-lg">
              <span className="text-[10px] uppercase font-mono text-textSecondary block">Total Active Signals</span>
              <span className="text-xl font-bold font-mono text-textPrimary">{data.active_anomalies_count}</span>
            </div>
            <div className="p-3 bg-[#FAF0F0] border border-[#E8B4B4] rounded-lg">
              <span className="text-[10px] uppercase font-mono text-[#964747]/80 block">Urgent Review</span>
              <span className="text-xl font-bold font-mono text-[#964747]">{data.by_severity['URGENT_REVIEW'] || 0}</span>
            </div>
            <div className="p-3 bg-[#FDF6EE] border border-[#F3D2AE] rounded-lg">
              <span className="text-[10px] uppercase font-mono text-[#8E5B23]/80 block">Attention</span>
              <span className="text-xl font-bold font-mono text-[#8E5B23]">{data.by_severity['ATTENTION'] || 0}</span>
            </div>
            <div className="p-3 bg-[#EEF4F8] border border-[#BCD3E3] rounded-lg">
              <span className="text-[10px] uppercase font-mono text-[#3E6580]/80 block">Watch & Monitor</span>
              <span className="text-xl font-bold font-mono text-[#3E6580]">{data.by_severity['WATCH'] || 0}</span>
            </div>
          </div>

          {/* Type Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] font-mono text-textSecondary mr-1">Filter Type:</span>
            <button
              onClick={() => setFilterType('ALL')}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                filterType === 'ALL'
                  ? 'bg-accent text-[#FAFAFC] font-semibold shadow-xs'
                  : 'bg-surfaceHighlight text-textSecondary hover:text-textPrimary'
              }`}
            >
              All Signals ({data.active_anomalies_count})
            </button>
            {Object.keys(data.by_type).map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-colors flex items-center space-x-1.5 ${
                  filterType === t
                    ? 'bg-accent text-[#FAFAFC] font-semibold shadow-xs'
                    : 'bg-surfaceHighlight text-textSecondary hover:text-textPrimary'
                }`}
              >
                <span>{t.replace(/_/g, ' ')}</span>
                <span className="opacity-80">({data.by_type[t]})</span>
              </button>
            ))}
          </div>

          {/* Anomaly Signal Cards */}
          {filteredAnomalies.length === 0 ? (
            <div className="p-8 bg-surfaceHighlight/30 border border-surfaceBorder rounded-lg text-center space-y-2">
              <CheckCircle2 className="w-6 h-6 text-[#7BA083] mx-auto" />
              <h4 className="text-sm font-semibold text-textPrimary">No Active Early-Warning Signals</h4>
              <p className="text-xs text-textSecondary max-w-md mx-auto">
                All personnel and unit welfare metrics currently adhere to expected historical baseline patterns.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredAnomalies.map((anom) => {
                const isResolved = anom.status === 'RESOLVED' || anom.status === 'DISMISSED';

                return (
                  <div
                    key={anom.id}
                    className="p-4 bg-surfaceHighlight/30 border border-surfaceBorder hover:border-accent/40 rounded-lg space-y-3 transition-colors"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center space-x-2.5">
                        <div className="p-1.5 bg-surface rounded-md border border-surfaceBorder">
                          {getAnomalyTypeIcon(anom.anomaly_type)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-textPrimary uppercase tracking-wide">
                              {anom.anomaly_type.replace(/_/g, ' ')}
                            </span>
                            {getSeverityBadge(anom.severity)}
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface border border-surfaceBorder text-textSecondary uppercase">
                              CONFIDENCE: {anom.confidence}
                            </span>
                          </div>
                          <p className="text-xs text-textSecondary font-mono mt-0.5">
                            {anom.scope_type === 'UNIT' ? (
                              <span>
                                Unit Scope: {anom.scope_battalion} • {anom.scope_location}
                              </span>
                            ) : (
                              <span>
                                <strong>{anom.personnel_name}</strong> ({anom.personnel_code}) • {anom.department} •{' '}
                                {anom.location}
                              </span>
                            )}
                          </p>
                        </div>
                      </div>

                      {/* Status & Review Buttons */}
                      <div className="flex items-center space-x-2 self-start sm:self-auto">
                        {getStatusBadge(anom.status)}

                        {anom.status === 'DETECTED' && (
                          <button
                            onClick={() => handleAcknowledge(anom.id)}
                            disabled={actionLoadingId === anom.id}
                            className="px-2.5 py-1 bg-surface hover:bg-surfaceHighlight text-textPrimary text-xs font-mono rounded border border-surfaceBorder transition-colors disabled:opacity-50"
                          >
                            Acknowledge
                          </button>
                        )}

                        {!isResolved && (
                          <>
                            <button
                              onClick={() => openReviewModal(anom)}
                              disabled={actionLoadingId === anom.id}
                              className="px-2.5 py-1 bg-surface hover:bg-surfaceHighlight text-textPrimary text-xs font-mono rounded border border-surfaceBorder transition-colors disabled:opacity-50 flex items-center space-x-1"
                            >
                              <UserCheck className="w-3 h-3 text-accent" />
                              <span>Review</span>
                            </button>
                            <button
                              onClick={() => openResolveModal(anom)}
                              disabled={actionLoadingId === anom.id}
                              className="px-2.5 py-1 bg-accent/20 hover:bg-accent/30 text-[#4F6E56] font-semibold text-xs font-mono rounded border border-accent/30 transition-colors flex items-center space-x-1"
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Resolve</span>
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Review Decision Banner if already under review */}
                    {anom.review_decision && (
                      <div className="p-2.5 bg-[#EBF3FB]/60 border border-[#ABCBE8] rounded-md text-xs font-mono space-y-1">
                        <div className="flex items-center justify-between text-[#285780]">
                          <span className="font-semibold uppercase flex items-center space-x-1.5">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Clinical Review: {anom.review_decision.replace(/_/g, ' ')}</span>
                          </span>
                          {anom.reviewed_at && (
                            <span className="text-[10px] text-textSecondary">
                              {new Date(anom.reviewed_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        {anom.review_notes && (
                          <p className="text-textPrimary font-sans text-xs italic pl-5">
                            &ldquo;{anom.review_notes}&rdquo;
                          </p>
                        )}
                      </div>
                    )}

                    {/* Explainable Evidence Box */}
                    <div className="p-3 bg-surface border border-surfaceBorder rounded-lg text-xs space-y-2">
                      <p className="text-textPrimary leading-relaxed font-sans">
                        {anom.evidence.explanation || anom.evidence.reason}
                      </p>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-textSecondary">
                        {anom.evidence.baseline_value !== undefined && (
                          <span>
                            Historical Baseline: <strong className="text-textPrimary">{anom.evidence.baseline_value}</strong>
                          </span>
                        )}
                        {anom.evidence.current_value !== undefined && (
                          <span>
                            Recent Observed: <strong className="text-textPrimary">{anom.evidence.current_value}</strong>
                          </span>
                        )}
                        {anom.evidence.delta !== undefined && (
                          <span>
                            Departure Delta: <strong className="text-[#C26D6D]">+{anom.evidence.delta}</strong>
                          </span>
                        )}
                        {anom.baseline_sample_count > 0 && (
                          <span>Baseline Samples: {anom.baseline_sample_count}</span>
                        )}
                        {anom.detected_at && (
                          <span>Detected: {new Date(anom.detected_at).toLocaleString()}</span>
                        )}
                      </div>

                      {anom.evidence.co_occurring_factors && anom.evidence.co_occurring_factors.length > 0 && (
                        <div className="pt-1 flex flex-wrap gap-1">
                          <span className="text-[10px] font-mono text-textSecondary mr-1">Co-factors:</span>
                          {anom.evidence.co_occurring_factors.map((cf) => (
                            <span
                              key={cf}
                              className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]"
                            >
                              {cf}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Resolution details if already resolved */}
                    {isResolved && anom.resolution_notes && (
                      <div className="p-2.5 bg-[#EEF8F1]/60 border border-[#A8DBB5] rounded-md text-xs font-mono space-y-1">
                        <div className="flex items-center space-x-1.5 text-[#2B613B] font-semibold">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Resolution Record:</span>
                        </div>
                        <p className="text-textPrimary font-sans text-xs pl-5">
                          {anom.resolution_notes}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 1. REVIEW WORKSPACE MODAL (Phase 48)                                      */}
      {/* ========================================================================= */}
      {selectedAnomalyForReview && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-surface border border-surfaceBorder rounded-xl max-w-xl w-full p-6 space-y-5 shadow-elevated max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-3 border-b border-surfaceBorder">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center">
                  <UserCheck className="w-4 h-4 text-accent" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider">
                    Early-Warning Signal Review
                  </h3>
                  <p className="text-xs text-textSecondary font-mono mt-0.5">
                    {selectedAnomalyForReview.personnel_name ? (
                      <span>
                        {selectedAnomalyForReview.personnel_name} • {selectedAnomalyForReview.personnel_code} (
                        {selectedAnomalyForReview.department || 'Unit'})
                      </span>
                    ) : (
                      <span>Unit Scope: {selectedAnomalyForReview.scope_battalion}</span>
                    )}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedAnomalyForReview(null)}
                className="text-textSecondary hover:text-textPrimary font-mono text-base p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Signal & Evidence Card */}
            <div className="p-4 bg-surfaceHighlight/30 border border-surfaceBorder rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getAnomalyTypeIcon(selectedAnomalyForReview.anomaly_type)}
                  <span className="text-xs font-bold text-textPrimary uppercase">
                    {selectedAnomalyForReview.anomaly_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex items-center space-x-1.5">
                  {getSeverityBadge(selectedAnomalyForReview.severity)}
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface border border-surfaceBorder text-textSecondary uppercase">
                    {selectedAnomalyForReview.confidence} CONFIDENCE
                  </span>
                </div>
              </div>

              <p className="text-xs text-textPrimary leading-relaxed">
                {selectedAnomalyForReview.evidence.explanation || selectedAnomalyForReview.evidence.reason}
              </p>

              <div className="grid grid-cols-3 gap-2 pt-1 border-t border-surfaceBorder/60 text-center font-mono">
                <div className="p-2 bg-surface rounded border border-surfaceBorder">
                  <span className="text-[10px] text-textSecondary block uppercase">Baseline</span>
                  <span className="text-xs font-bold text-textPrimary">
                    {selectedAnomalyForReview.evidence.baseline_value ?? 'N/A'}
                  </span>
                </div>
                <div className="p-2 bg-surface rounded border border-surfaceBorder">
                  <span className="text-[10px] text-textSecondary block uppercase">Recent Observed</span>
                  <span className="text-xs font-bold text-textPrimary">
                    {selectedAnomalyForReview.evidence.current_value ?? 'N/A'}
                  </span>
                </div>
                <div className="p-2 bg-surface rounded border border-surfaceBorder">
                  <span className="text-[10px] text-textSecondary block uppercase">Departure</span>
                  <span className="text-xs font-bold text-[#C26D6D]">
                    {selectedAnomalyForReview.evidence.delta !== undefined
                      ? `+${selectedAnomalyForReview.evidence.delta}`
                      : 'N/A'}
                  </span>
                </div>
              </div>

              {selectedAnomalyForReview.evidence.co_occurring_factors &&
                selectedAnomalyForReview.evidence.co_occurring_factors.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1 pt-1">
                    <span className="text-[10px] font-mono text-textSecondary mr-1">Co-factors:</span>
                    {selectedAnomalyForReview.evidence.co_occurring_factors.map((cf) => (
                      <span
                        key={cf}
                        className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]"
                      >
                        {cf}
                      </span>
                    ))}
                  </div>
                )}
            </div>

            {/* Review Error notice */}
            {reviewError && (
              <p className="text-xs text-[#964747] font-mono bg-[#FAF0F0] p-2.5 rounded-lg border border-[#E8B4B4]">
                {reviewError}
              </p>
            )}

            {/* Review Decision Dropdown */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono font-medium text-textSecondary flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5 text-accent" />
                <span>Review Decision:</span>
              </label>
              <select
                value={reviewDecision}
                onChange={(e) => setReviewDecision(e.target.value)}
                className="w-full bg-[#F1F7F4] border border-surfaceBorder rounded-lg p-2.5 text-xs text-textPrimary font-mono focus:outline-hidden focus:border-accent"
              >
                {REVIEW_DECISIONS.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label} — {d.desc}
                  </option>
                ))}
              </select>
            </div>

            {/* Review Notes Textarea */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono font-medium text-textSecondary flex items-center justify-between">
                <span>Clinical Review Notes:</span>
                <span className="text-[10px] opacity-75">{reviewNotes.length}/2000 chars</span>
              </label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="e.g. Reviewed the continuous duty pattern. Personnel should be contacted regarding recovery and duty scheduling."
                maxLength={2000}
                rows={3}
                className="w-full bg-[#F1F7F4] border border-surfaceBorder rounded-lg p-2.5 text-xs text-textPrimary placeholder:text-textSecondary focus:outline-hidden focus:border-accent"
              />
            </div>

            {/* Existing Welfare Workflow Navigation Links */}
            <div className="p-3 bg-surfaceHighlight/20 border border-surfaceBorder/80 rounded-lg text-xs space-y-2">
              <span className="text-[10px] font-mono text-textSecondary uppercase tracking-wider block">
                Connect to Existing Welfare Workflows:
              </span>
              <div className="flex flex-wrap gap-2">
                <Link
                  href="/dashboard/recommendations"
                  className="inline-flex items-center space-x-1 px-2.5 py-1 bg-surface hover:bg-surfaceHighlight text-textPrimary text-[11px] font-mono rounded border border-surfaceBorder transition-colors"
                >
                  <span>Welfare Recommendations</span>
                  <ExternalLink className="w-3 h-3 text-textSecondary" />
                </Link>
                <Link
                  href="/dashboard/follow-ups"
                  className="inline-flex items-center space-x-1 px-2.5 py-1 bg-surface hover:bg-surfaceHighlight text-textPrimary text-[11px] font-mono rounded border border-surfaceBorder transition-colors"
                >
                  <span>Follow-Up Scheduler</span>
                  <ExternalLink className="w-3 h-3 text-textSecondary" />
                </Link>
                <Link
                  href="/dashboard/cases"
                  className="inline-flex items-center space-x-1 px-2.5 py-1 bg-surface hover:bg-surfaceHighlight text-textPrimary text-[11px] font-mono rounded border border-surfaceBorder transition-colors"
                >
                  <span>Welfare Case Center</span>
                  <ExternalLink className="w-3 h-3 text-textSecondary" />
                </Link>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-surfaceBorder">
              <button
                onClick={() => setSelectedAnomalyForReview(null)}
                className="px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textSecondary hover:text-textPrimary rounded-lg text-xs font-mono transition-colors border border-surfaceBorder"
              >
                Cancel
              </button>

              <div className="flex items-center space-x-2">
                {reviewDecision === 'RESOLVE_SIGNAL' ? (
                  <button
                    onClick={() => {
                      const anom = selectedAnomalyForReview;
                      setSelectedAnomalyForReview(null);
                      openResolveModal(anom);
                    }}
                    className="px-4 py-1.5 bg-accent text-[#FAFAFC] font-semibold rounded-lg text-xs font-mono hover:bg-accent/90 transition-colors flex items-center space-x-1.5"
                  >
                    <span>Proceed to Resolution</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                ) : (
                  <button
                    onClick={handleReviewSubmit}
                    disabled={actionLoadingId === selectedAnomalyForReview.id}
                    className="px-4 py-1.5 bg-accent text-[#FAFAFC] font-semibold rounded-lg text-xs font-mono hover:bg-accent/90 transition-colors disabled:opacity-50 flex items-center space-x-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>
                      {actionLoadingId === selectedAnomalyForReview.id ? 'Submitting...' : 'Submit Review'}
                    </span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. RESOLUTION & JAWAN NOTIFICATION MODAL (Phase 48)                       */}
      {/* ========================================================================= */}
      {selectedAnomalyForResolve && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-surface border border-surfaceBorder rounded-xl max-w-xl w-full p-6 space-y-4 shadow-elevated max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-surfaceBorder">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#EEF8F1] border border-[#A8DBB5] flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 text-[#2B613B]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider">
                    Resolve Early-Warning Signal
                  </h3>
                  <p className="text-xs text-textSecondary font-mono mt-0.5">
                    {selectedAnomalyForResolve.personnel_name ? (
                      <span>
                        {selectedAnomalyForResolve.personnel_name} • {selectedAnomalyForResolve.personnel_code}
                      </span>
                    ) : (
                      <span>Unit Scope: {selectedAnomalyForResolve.scope_battalion}</span>
                    )}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedAnomalyForResolve(null)}
                className="text-textSecondary hover:text-textPrimary font-mono text-base p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Selected Signal Brief */}
            <div className="p-3 bg-surfaceHighlight/30 border border-surfaceBorder rounded-lg space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-textPrimary uppercase">
                  {selectedAnomalyForResolve.anomaly_type.replace(/_/g, ' ')}
                </span>
                {getSeverityBadge(selectedAnomalyForResolve.severity)}
              </div>
              <p className="text-textSecondary leading-relaxed font-sans">
                {selectedAnomalyForResolve.evidence.explanation || selectedAnomalyForResolve.evidence.reason}
              </p>
            </div>

            {/* Error display */}
            {resolveError && (
              <p className="text-xs text-[#964747] font-mono bg-[#FAF0F0] p-2.5 rounded-lg border border-[#E8B4B4]">
                {resolveError}
              </p>
            )}

            {/* Commander Resolution Notes (Internal Audit) */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono font-medium text-textSecondary flex items-center justify-between">
                <span>Commander Resolution Notes (Internal Audit Record):</span>
                <span className="text-[10px] opacity-75">{resolutionNotes.length}/2000 chars</span>
              </label>
              <textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="e.g. Conducted 1-on-1 check-in, reviewed duty allocation, and arranged recuperative rest."
                maxLength={2000}
                rows={3}
                className="w-full bg-[#F1F7F4] border border-surfaceBorder rounded-lg p-2.5 text-xs text-textPrimary placeholder:text-textSecondary focus:outline-hidden focus:border-accent"
              />
            </div>

            {/* Jawan Resolution Notification Section */}
            {selectedAnomalyForResolve.personnel_id && (
              <div className="p-4 bg-[#F1F7F4] border border-surfaceBorder rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifyPersonnel}
                      onChange={(e) => setNotifyPersonnel(e.target.checked)}
                      className="w-4 h-4 rounded text-accent focus:ring-accent border-surfaceBorder"
                    />
                    <span className="text-xs font-bold text-textPrimary flex items-center space-x-1.5">
                      <Bell className="w-3.5 h-3.5 text-accent" />
                      <span>Notify Affected Personnel</span>
                    </span>
                  </label>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-surface border border-surfaceBorder text-textSecondary">
                    Jawan Portal Delivery
                  </span>
                </div>

                <p className="text-[11px] text-textSecondary leading-relaxed">
                  Delivers a supportive, non-punitive welfare resolution notification to the Jawan&apos;s notification
                  center. Internal ML metrics and risk scores are strictly excluded.
                </p>

                {notifyPersonnel && (
                  <div className="space-y-1.5 pt-1">
                    <label className="text-[11px] font-mono text-textSecondary flex items-center justify-between">
                      <span>Welfare Resolution Message to Jawan:</span>
                      <span className="text-[10px] opacity-75">{customMessage.length}/1000 chars</span>
                    </label>
                    <textarea
                      value={customMessage}
                      onChange={(e) => setCustomMessage(e.target.value)}
                      placeholder="Enter supportive resolution message delivered to the Jawan..."
                      maxLength={1000}
                      rows={3}
                      className="w-full bg-surface border border-surfaceBorder rounded-lg p-2.5 text-xs text-textPrimary placeholder:text-textSecondary focus:outline-hidden focus:border-accent"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-surfaceBorder">
              <button
                onClick={() => setSelectedAnomalyForResolve(null)}
                className="px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textSecondary hover:text-textPrimary rounded-lg text-xs font-mono transition-colors border border-surfaceBorder"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveSubmit}
                disabled={actionLoadingId === selectedAnomalyForResolve.id}
                className="px-4 py-1.5 bg-accent text-[#FAFAFC] font-semibold rounded-lg text-xs font-mono hover:bg-accent/90 transition-colors disabled:opacity-50 flex items-center space-x-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>
                  {actionLoadingId === selectedAnomalyForResolve.id
                    ? 'Processing...'
                    : notifyPersonnel && selectedAnomalyForResolve.personnel_id
                    ? 'Resolve & Notify Personnel'
                    : 'Confirm Resolution'}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
