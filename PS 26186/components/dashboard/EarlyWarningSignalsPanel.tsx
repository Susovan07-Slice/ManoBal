'use client';

import React, { useEffect, useState, useCallback } from 'react';
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
} from 'lucide-react';

export default function EarlyWarningSignalsPanel() {
  const [data, setData] = useState<CommanderAnomalySummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');

  // Resolution modal state
  const [selectedAnomalyForResolve, setSelectedAnomalyForResolve] = useState<WelfareAnomalyOut | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
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
    try {
      await acknowledgeAnomaly(anomalyId);
      await fetchAnomalies();
    } catch (err: any) {
      alert(`Failed to acknowledge anomaly: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReview = async (anomalyId: number) => {
    setActionLoadingId(anomalyId);
    try {
      await reviewAnomaly(anomalyId);
      await fetchAnomalies();
    } catch (err: any) {
      alert(`Failed to start review: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleResolveSubmit = async () => {
    if (!selectedAnomalyForResolve) return;
    if (!resolutionNotes.trim()) {
      setResolveError('Resolution notes explaining supportive actions are required.');
      return;
    }
    setActionLoadingId(selectedAnomalyForResolve.id);
    setResolveError(null);
    try {
      await resolveAnomaly(selectedAnomalyForResolve.id, resolutionNotes.trim());
      setSelectedAnomalyForResolve(null);
      setResolutionNotes('');
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

  const filteredAnomalies = data?.anomalies.filter((a) => {
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
            {data.message || 'Early-warning anomaly signals are withheld for units below the privacy threshold to prevent deductive re-identification of vulnerable personnel.'}
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
              {filteredAnomalies.map((anom) => (
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
                            <span>Unit Scope: {anom.scope_battalion} • {anom.scope_location}</span>
                          ) : (
                            <span>
                              {anom.personnel_name} ({anom.personnel_code}) • {anom.department} • {anom.location}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>

                    {/* Status & Review Buttons */}
                    <div className="flex items-center space-x-2 self-start sm:self-auto">
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-surface text-textSecondary border border-surfaceBorder">
                        {anom.status}
                      </span>

                      {anom.status === 'DETECTED' && (
                        <button
                          onClick={() => handleAcknowledge(anom.id)}
                          disabled={actionLoadingId === anom.id}
                          className="px-2.5 py-1 bg-surface hover:bg-surfaceHighlight text-textPrimary text-xs font-mono rounded border border-surfaceBorder transition-colors disabled:opacity-50"
                        >
                          Acknowledge
                        </button>
                      )}

                      {anom.status !== 'RESOLVED' && anom.status !== 'DISMISSED' && (
                        <>
                          <button
                            onClick={() => handleReview(anom.id)}
                            disabled={actionLoadingId === anom.id}
                            className="px-2.5 py-1 bg-surface hover:bg-surfaceHighlight text-textPrimary text-xs font-mono rounded border border-surfaceBorder transition-colors disabled:opacity-50"
                          >
                            Review
                          </button>
                          <button
                            onClick={() => {
                              setSelectedAnomalyForResolve(anom);
                              setResolutionNotes('');
                              setResolveError(null);
                            }}
                            className="px-2.5 py-1 bg-accent/20 hover:bg-accent/30 text-[#4F6E56] font-semibold text-xs font-mono rounded border border-accent/30 transition-colors"
                          >
                            Resolve
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Explainable Evidence Box */}
                  <div className="p-3 bg-surface border border-surfaceBorder rounded-lg text-xs space-y-2">
                    <p className="text-textPrimary leading-relaxed font-sans">
                      {anom.evidence.explanation || anom.evidence.reason}
                    </p>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-textSecondary">
                      {anom.evidence.baseline_value !== undefined && (
                        <span>Historical Baseline: <strong className="text-textPrimary">{anom.evidence.baseline_value}</strong></span>
                      )}
                      {anom.evidence.current_value !== undefined && (
                        <span>Recent Observed: <strong className="text-textPrimary">{anom.evidence.current_value}</strong></span>
                      )}
                      {anom.evidence.delta !== undefined && (
                        <span>Departure Delta: <strong className="text-[#C26D6D]">+{anom.evidence.delta}</strong></span>
                      )}
                      {anom.baseline_sample_count > 0 && (
                        <span>Baseline Samples: {anom.baseline_sample_count}</span>
                      )}
                    </div>

                    {anom.evidence.co_occurring_factors && anom.evidence.co_occurring_factors.length > 0 && (
                      <div className="pt-1 flex flex-wrap gap-1">
                        <span className="text-[10px] font-mono text-textSecondary mr-1">Co-factors:</span>
                        {anom.evidence.co_occurring_factors.map((cf) => (
                          <span key={cf} className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]">
                            {cf}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Resolution Modal */}
      {selectedAnomalyForResolve && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-surface border border-surfaceBorder rounded-xl max-w-lg w-full p-6 space-y-4 shadow-elevated">
            <div className="flex items-center justify-between pb-2 border-b border-surfaceBorder">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-[#7BA083]" />
                <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider">
                  Resolve Early-Warning Anomaly Signal
                </h3>
              </div>
              <button
                onClick={() => setSelectedAnomalyForResolve(null)}
                className="text-textSecondary hover:text-textPrimary font-mono text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-textSecondary">
              Document the supportive welfare action, counseling check-in, or roster adjustment implemented to address this anomaly.
            </p>

            {resolveError && (
              <p className="text-xs text-[#964747] font-mono bg-[#FAF0F0] p-2 rounded-lg border border-[#E8B4B4]">
                {resolveError}
              </p>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-mono font-medium text-textSecondary">
                Resolution & Supportive Follow-up Notes:
              </label>
              <textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="e.g. Conducted 1-on-1 supportive check-in, reallocated night shifts, and arranged 48-hour recuperative respite."
                rows={4}
                className="w-full bg-[#F1F7F4] border border-surfaceBorder rounded-lg p-2.5 text-xs text-textPrimary placeholder:text-textSecondary focus:outline-hidden focus:border-accent"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-surfaceBorder">
              <button
                onClick={() => setSelectedAnomalyForResolve(null)}
                className="px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textSecondary hover:text-textPrimary rounded-lg text-xs font-mono transition-colors border border-surfaceBorder"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveSubmit}
                disabled={actionLoadingId === selectedAnomalyForResolve.id}
                className="px-4 py-1.5 bg-accent text-[#FAFAFC] font-semibold rounded-lg text-xs font-mono hover:bg-accent/90 transition-colors disabled:opacity-50"
              >
                {actionLoadingId === selectedAnomalyForResolve.id ? 'Resolving...' : 'Confirm Resolution'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
