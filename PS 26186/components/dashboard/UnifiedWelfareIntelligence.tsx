'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  fetchUnitWelfareIntelligence,
  fetchPersonnelWelfareSnapshot,
  UnitWelfareIntelligenceResponse,
  PersonnelWelfareSnapshotResponse,
  TimelineEventItem,
} from '@/lib/unified_intelligence';
import {
  Shield,
  Activity,
  HeartHandshake,
  CheckCircle2,
  Clock,
  Search,
  RefreshCw,
  Eye,
  X,
  Info,
  Layers,
  AlertOctagon,
  BellRing,
  FolderKanban,
} from 'lucide-react';

export default function UnifiedWelfareIntelligence() {
  const [data, setData] = useState<UnitWelfareIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [trendFilter, setTrendFilter] = useState<string>('ALL');
  const [reviewFilter, setReviewFilter] = useState<string>('ALL');
  const [timeFilter, setTimeFilter] = useState<string>('30d');

  // Drilldown Modal
  const [selectedPersonnelId, setSelectedPersonnelId] = useState<number | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState<boolean>(false);
  const [snapshotData, setSnapshotData] = useState<PersonnelWelfareSnapshotResponse | null>(null);
  const [snapshotError, setSnapshotError] = useState<string | null>(null);

  const loadUnitData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchUnitWelfareIntelligence({ timeFilter });
      setData(res);
    } catch (err: any) {
      console.error('Failed to load unified welfare intelligence:', err);
      setError(err?.message || 'Unable to retrieve unified welfare intelligence layer.');
    } finally {
      setLoading(false);
    }
  }, [timeFilter]);

  useEffect(() => {
    loadUnitData();
  }, [loadUnitData]);

  // Load drilldown snapshot
  const handleOpenSnapshot = async (personnelId: number) => {
    setSelectedPersonnelId(personnelId);
    setSnapshotLoading(true);
    setSnapshotError(null);
    try {
      const snap = await fetchPersonnelWelfareSnapshot(personnelId);
      setSnapshotData(snap);
    } catch (err: any) {
      console.error(`Failed to load snapshot for personnel ${personnelId}:`, err);
      setSnapshotError(err?.message || 'Unable to load personnel intelligence snapshot.');
    } finally {
      setSnapshotLoading(false);
    }
  };

  const handleCloseSnapshot = () => {
    setSelectedPersonnelId(null);
    setSnapshotData(null);
    setSnapshotError(null);
  };

  // Filter unranked personnel cards
  const filteredPersonnel = useMemo(() => {
    if (!data?.personnel_cards) return [];
    return data.personnel_cards.filter((card) => {
      // Search matching code or name
      const matchesSearch =
        !searchQuery ||
        card.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        card.personnel_code.toLowerCase().includes(searchQuery.toLowerCase());

      // Risk category filter
      const cat = card.current_risk_category || 'UNAVAILABLE';
      const matchesRisk =
        riskFilter === 'ALL' ||
        cat.toUpperCase() === riskFilter.toUpperCase();

      // Trend filter
      const matchesTrend =
        trendFilter === 'ALL' ||
        card.trend_direction.toUpperCase() === trendFilter.toUpperCase();

      // Review filter
      const matchesReview =
        reviewFilter === 'ALL' ||
        card.review_level.toUpperCase() === reviewFilter.toUpperCase();

      return matchesSearch && matchesRisk && matchesTrend && matchesReview;
    });
  }, [data?.personnel_cards, searchQuery, riskFilter, trendFilter, reviewFilter]);

  return (
    <div className="bg-surface/80 border border-border/80 rounded-xl p-5 shadow-sm space-y-6">
      {/* 1. Header Section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/60 pb-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-textPrimary uppercase tracking-wide">
                  Unified Welfare Intelligence & Decision-Support
                </h2>
              </div>
              <p className="text-xs text-textSecondary font-mono mt-0.5">
                Authoritative intelligence aggregation • Strictly non-scoring & unranked
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 self-start md:self-auto">
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
            className="bg-surfaceHighlight border border-border rounded-lg px-2.5 py-1.5 text-xs text-textPrimary font-mono focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="7d">Window: 7 Days</option>
            <option value="30d">Window: 30 Days</option>
            <option value="90d">Window: 90 Days</option>
          </select>

          <button
            onClick={loadUnitData}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-border disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && !data && (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-6 h-6 animate-spin text-accent" />
          <p className="text-xs text-textSecondary font-mono">Aggregating unit intelligence across Phases 34–41...</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg flex items-center space-x-3 text-red-200 text-sm">
          <AlertOctagon className="w-5 h-5 shrink-0 text-red-400" />
          <div>
            <p className="font-semibold">Intelligence Layer Communication Error</p>
            <p className="text-xs text-red-300 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          {/* Small-Group Privacy Banner (if suppressed) */}
          {data.data_suppressed && (
            <div className="p-4 bg-amber-950/30 border border-amber-800/50 rounded-lg flex items-center space-x-3 text-amber-200 text-xs">
              <Shield className="w-5 h-5 shrink-0 text-amber-400" />
              <div>
                <p className="font-semibold text-amber-300">Small-Group Privacy Protection Enforced (k &lt; 5)</p>
                <p className="mt-0.5 text-amber-200/90 leading-relaxed">
                  {data.suppression_reason || 'Monitored cohort size is below the mandatory privacy threshold (k = 5). Aggregate distributions and individual personnel cards are suppressed to prevent indirect identification.'}
                </p>
              </div>
            </div>
          )}

          {/* 2. Key Intelligence Metrics (Unit Overview) */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
              <div className="flex items-center justify-between text-textSecondary">
                <span className="text-[11px] font-mono uppercase">Monitored</span>
                <Shield className="w-3.5 h-3.5 text-textSecondary" />
              </div>
              <div className="text-xl font-bold text-textPrimary font-mono mt-1">
                {data.total_personnel_in_scope}
              </div>
              <div className="text-[10px] text-textSecondary font-mono mt-0.5">Active personnel</div>
            </div>

            <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
              <div className="flex items-center justify-between text-amber-400">
                <span className="text-[11px] font-mono uppercase">Active Alerts</span>
                <BellRing className="w-3.5 h-3.5" />
              </div>
              <div className="text-xl font-bold text-amber-400 font-mono mt-1">
                {data.data_suppressed ? '—' : data.unit_overview?.active_alerts_total ?? 0}
              </div>
              <div className="text-[10px] text-textSecondary font-mono mt-0.5">Phase 37 alerts</div>
            </div>

            <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
              <div className="flex items-center justify-between text-indigo-400">
                <span className="text-[11px] font-mono uppercase">Anomalies</span>
                <Activity className="w-3.5 h-3.5" />
              </div>
              <div className="text-xl font-bold text-indigo-400 font-mono mt-1">
                {data.data_suppressed ? '—' : data.unit_overview?.active_anomalies_total ?? 0}
              </div>
              <div className="text-[10px] text-textSecondary font-mono mt-0.5">Phase 39 early warning</div>
            </div>

            <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
              <div className="flex items-center justify-between text-blue-400">
                <span className="text-[11px] font-mono uppercase">Recommendations</span>
                <HeartHandshake className="w-3.5 h-3.5" />
              </div>
              <div className="text-xl font-bold text-blue-400 font-mono mt-1">
                {data.data_suppressed ? '—' : data.unit_overview?.open_recommendations_total ?? 0}
              </div>
              <div className="text-[10px] text-textSecondary font-mono mt-0.5">Phase 40 suggestions</div>
            </div>

            <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
              <div className="flex items-center justify-between text-emerald-400">
                <span className="text-[11px] font-mono uppercase">Interventions</span>
                <CheckCircle2 className="w-3.5 h-3.5" />
              </div>
              <div className="text-xl font-bold text-emerald-400 font-mono mt-1">
                {data.data_suppressed ? '—' : data.unit_overview?.open_interventions_total ?? 0}
              </div>
              <div className="text-[10px] text-textSecondary font-mono mt-0.5">Phase 37 active support</div>
            </div>

            <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
              <div className="flex items-center justify-between text-rose-400">
                <span className="text-[11px] font-mono uppercase">Follow-ups</span>
                <Clock className="w-3.5 h-3.5" />
              </div>
              <div className="text-xl font-bold text-rose-400 font-mono mt-1">
                {data.data_suppressed
                  ? '—'
                  : `${data.unit_overview?.followups_summary?.pending ?? 0} (${data.unit_overview?.followups_summary?.overdue ?? 0} overdue)`}
              </div>
              <div className="text-[10px] text-textSecondary font-mono mt-0.5">Phase 41 check-ins</div>
            </div>
          </div>

          {/* 3. Authoritative Risk & Welfare Trend Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Risk Distribution (Phase 34) */}
            <div className="p-4 bg-surfaceHighlight/30 border border-border/60 rounded-lg space-y-3">
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <div className="flex items-center space-x-2">
                  <Shield className="w-4 h-4 text-accent" />
                  <span className="text-xs font-bold text-textPrimary uppercase tracking-wide">
                    Risk Distribution (Phase 34)
                  </span>
                </div>
                <span className="text-[10px] font-mono text-textSecondary">Authoritative</span>
              </div>

              {data.data_suppressed || !data.unit_overview?.risk_distribution ? (
                <div className="text-xs text-textSecondary font-mono py-6 text-center">
                  Suppressed for privacy (k &lt; 5)
                </div>
              ) : (
                <div className="space-y-2 pt-1">
                  {Object.entries(data.unit_overview.risk_distribution).map(([cat, count]) => {
                    const total = data.total_personnel_in_scope || 1;
                    const pct = Math.round((count / total) * 100);
                    const colorClass =
                      cat === 'High'
                        ? 'bg-rose-500'
                        : cat === 'Medium'
                        ? 'bg-amber-500'
                        : cat === 'Low'
                        ? 'bg-emerald-500'
                        : 'bg-zinc-500';

                    return (
                      <div key={cat} className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-textSecondary">{cat}</span>
                          <span className="text-textPrimary font-semibold">
                            {count} ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-surfaceHighlight rounded-full overflow-hidden">
                          <div
                            className={`h-full ${colorClass}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Longitudinal Trend (Phase 36) */}
            <div className="p-4 bg-surfaceHighlight/30 border border-border/60 rounded-lg space-y-3">
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-bold text-textPrimary uppercase tracking-wide">
                    Welfare Trends (Phase 36)
                  </span>
                </div>
                <span className="text-[10px] font-mono text-textSecondary">Trajectory</span>
              </div>

              {data.data_suppressed || !data.unit_overview?.trend_distribution ? (
                <div className="text-xs text-textSecondary font-mono py-6 text-center">
                  Suppressed for privacy (k &lt; 5)
                </div>
              ) : (
                <div className="space-y-2 pt-1">
                  {Object.entries(data.unit_overview.trend_distribution).map(([dir, count]) => {
                    const total = data.total_personnel_in_scope || 1;
                    const pct = Math.round((count / total) * 100);
                    const colorClass =
                      dir === 'Worsening'
                        ? 'bg-rose-500'
                        : dir === 'Improving'
                        ? 'bg-emerald-500'
                        : dir === 'Stable'
                        ? 'bg-blue-500'
                        : 'bg-zinc-500';

                    return (
                      <div key={dir} className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-textSecondary">{dir}</span>
                          <span className="text-textPrimary font-semibold">
                            {count} ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-surfaceHighlight rounded-full overflow-hidden">
                          <div
                            className={`h-full ${colorClass}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Data Quality & Freshness Indicator */}
            <div className="p-4 bg-surfaceHighlight/30 border border-border/60 rounded-lg space-y-3">
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold text-textPrimary uppercase tracking-wide">
                    Data Quality & Freshness
                  </span>
                </div>
                <span className="text-[10px] font-mono text-textSecondary">Telemetry</span>
              </div>

              <div className="space-y-2 text-xs font-mono pt-1">
                <div className="flex justify-between items-center py-1 border-b border-border/20">
                  <span className="text-textSecondary">Valid Current Assessments</span>
                  <span className="font-semibold text-emerald-400">
                    {data.data_suppressed ? '—' : data.data_quality?.valid_assessments_count ?? 0}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-border/20">
                  <span className="text-textSecondary">Insufficient History</span>
                  <span className="font-semibold text-zinc-400">
                    {data.data_suppressed ? '—' : data.data_quality?.insufficient_data_count ?? 0}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-border/20">
                  <span className="text-textSecondary">Stale Telemetry (&gt;30d)</span>
                  <span className="font-semibold text-amber-400">
                    {data.data_suppressed ? '—' : data.data_quality?.stale_data_count ?? 0}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-textSecondary">Human Review Attention</span>
                  <span className="font-semibold text-indigo-400">
                    {data.data_suppressed
                      ? '—'
                      : `${data.human_review_summary?.review_needed_count ?? 0} Flagged`}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 4. Support Workflow Pipeline (Phase 40 -> Phase 37 -> Phase 41) */}
          <div className="p-4 bg-surfaceHighlight/20 border border-border/60 rounded-lg space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wide flex items-center space-x-2">
                <HeartHandshake className="w-4 h-4 text-blue-400" />
                <span>Support Workflow Progression</span>
              </h3>
              <span className="text-[10px] font-mono text-textSecondary">
                Multi-Phase Support Lifecycle
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <div className="p-3 bg-surfaceHighlight/40 border border-border/40 rounded-lg">
                <div className="text-[10px] font-mono text-textSecondary uppercase">Phase 40 Recommendations</div>
                <div className="text-base font-bold text-textPrimary font-mono mt-1">
                  {data.data_suppressed
                    ? '—'
                    : `${data.support_workflow?.recommendations_count ?? 0} Active / ${data.support_workflow?.human_decisions_count ?? 0} Actioned`}
                </div>
                <div className="text-[10px] text-textSecondary mt-0.5">Guidance suggestions</div>
              </div>

              <div className="p-3 bg-surfaceHighlight/40 border border-border/40 rounded-lg">
                <div className="text-[10px] font-mono text-textSecondary uppercase">Phase 37 Interventions</div>
                <div className="text-base font-bold text-textPrimary font-mono mt-1">
                  {data.data_suppressed
                    ? '—'
                    : `${data.support_workflow?.interventions_active_count ?? 0} In Progress`}
                </div>
                <div className="text-[10px] text-textSecondary mt-0.5">Commander-approved support</div>
              </div>

              <div className="p-3 bg-surfaceHighlight/40 border border-border/40 rounded-lg">
                <div className="text-[10px] font-mono text-textSecondary uppercase">Phase 41 Follow-ups</div>
                <div className="text-base font-bold text-textPrimary font-mono mt-1">
                  {data.data_suppressed
                    ? '—'
                    : `${data.support_workflow?.followups_completed_count ?? 0} Completed`}
                </div>
                <div className="text-[10px] text-textSecondary mt-0.5">Check-in schedule</div>
              </div>

              <div className="p-3 bg-surfaceHighlight/40 border border-border/40 rounded-lg">
                <div className="text-[10px] font-mono text-textSecondary uppercase">Outcome Observations</div>
                <div className="text-base font-bold text-textPrimary font-mono mt-1">
                  {data.data_suppressed
                    ? '—'
                    : `${data.support_workflow?.outcomes_observed_count ?? 0} Recorded`}
                </div>
                <div className="text-[10px] text-textSecondary mt-0.5">Post-support evaluation</div>
              </div>
            </div>
          </div>

          {/* 5. Unranked Personnel Roster & Filter Controls */}
          {!data.data_suppressed && (
            <div className="space-y-4 pt-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wide">
                    Personnel Welfare Decision Support Roster
                  </h3>
                  <span className="text-[10px] font-mono text-textSecondary px-2 py-0.5 bg-surfaceHighlight rounded border border-border/40">
                    UNRANKED
                  </span>
                </div>
                <div className="text-xs text-textSecondary font-mono">
                  Showing {filteredPersonnel.length} of {data.personnel_cards.length} personnel
                </div>
              </div>

              {/* Filters Bar */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-3 text-textSecondary" />
                  <input
                    type="text"
                    placeholder="Search Code or Name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-surfaceHighlight border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-textPrimary font-mono placeholder:text-textSecondary/60 focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                </div>

                <div>
                  <select
                    value={riskFilter}
                    onChange={(e) => setRiskFilter(e.target.value)}
                    className="w-full bg-surfaceHighlight border border-border rounded-lg px-2.5 py-1.5 text-xs text-textPrimary font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="ALL">All Risk Categories</option>
                    <option value="LOW">Low Risk</option>
                    <option value="MEDIUM">Medium Risk</option>
                    <option value="HIGH">High Risk</option>
                    <option value="UNAVAILABLE">Unavailable / Insufficient</option>
                  </select>
                </div>

                <div>
                  <select
                    value={trendFilter}
                    onChange={(e) => setTrendFilter(e.target.value)}
                    className="w-full bg-surfaceHighlight border border-border rounded-lg px-2.5 py-1.5 text-xs text-textPrimary font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="ALL">All Welfare Trends</option>
                    <option value="IMPROVING">Improving Trend</option>
                    <option value="STABLE">Stable Trend</option>
                    <option value="WORSENING">Worsening Trend</option>
                    <option value="INSUFFICIENT DATA">Insufficient Data</option>
                  </select>
                </div>

                <div>
                  <select
                    value={reviewFilter}
                    onChange={(e) => setReviewFilter(e.target.value)}
                    className="w-full bg-surfaceHighlight border border-border rounded-lg px-2.5 py-1.5 text-xs text-textPrimary font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="ALL">All Review Statuses</option>
                    <option value="REVIEW">REVIEW Flagged</option>
                    <option value="MONITOR">MONITOR</option>
                    <option value="NO_ACTIVE_REVIEW_SIGNAL">No Active Signal</option>
                    <option value="INSUFFICIENT_DATA">Insufficient Data</option>
                  </select>
                </div>
              </div>

              {/* Personnel Cards Grid */}
              {filteredPersonnel.length === 0 ? (
                <div className="p-8 text-center bg-surfaceHighlight/20 border border-border/60 rounded-lg text-xs text-textSecondary font-mono">
                  No personnel matching current filters.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {filteredPersonnel.map((card) => {
                    const reviewBadgeClass =
                      card.review_level === 'REVIEW'
                        ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                        : card.review_level === 'MONITOR'
                        ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                        : card.review_level === 'INSUFFICIENT_DATA'
                        ? 'bg-zinc-800 text-zinc-400 border-zinc-700'
                        : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60';

                    const riskCategory = card.current_risk_category || 'Unavailable';
                    const riskColor =
                      riskCategory === 'High'
                        ? 'text-rose-400'
                        : riskCategory === 'Medium'
                        ? 'text-amber-400'
                        : riskCategory === 'Low'
                        ? 'text-emerald-400'
                        : 'text-zinc-400';

                    return (
                      <div
                        key={card.personnel_id}
                        className="p-3.5 bg-surfaceHighlight/30 hover:bg-surfaceHighlight/50 border border-border/60 rounded-lg transition-colors flex flex-col justify-between space-y-3"
                      >
                        <div>
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="font-semibold text-textPrimary text-sm">
                                {card.name}
                              </div>
                              <div className="text-[11px] font-mono text-textSecondary">
                                {card.personnel_code} • {card.department || 'Operations'}
                              </div>
                            </div>

                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${reviewBadgeClass}`}
                            >
                              {card.review_level}
                            </span>
                          </div>

                          {/* Snapshot Indicators */}
                          <div className="grid grid-cols-2 gap-2 mt-3 pt-2 border-t border-border/40 text-xs font-mono">
                            <div>
                              <span className="text-textSecondary text-[10px] uppercase block">
                                Risk (P34)
                              </span>
                              <span className={`font-semibold ${riskColor}`}>
                                {riskCategory}
                              </span>
                            </div>

                            <div>
                              <span className="text-textSecondary text-[10px] uppercase block">
                                Trend (P36)
                              </span>
                              <span className="text-textPrimary font-semibold">
                                {card.trend_direction}
                              </span>
                            </div>

                            <div>
                              <span className="text-textSecondary text-[10px] uppercase block">
                                Alerts / Anomalies
                              </span>
                              <span className="text-textPrimary">
                                {card.active_alerts_count} / {card.active_anomalies_count}
                              </span>
                            </div>

                            <div>
                              <span className="text-textSecondary text-[10px] uppercase block">
                                Recs / Followup
                              </span>
                              <span className="text-textPrimary">
                                {card.open_recommendations_count} /{' '}
                                {card.has_overdue_followup ? (
                                  <span className="text-rose-400 font-semibold">Overdue</span>
                                ) : card.pending_followups_count > 0 ? (
                                  <span className="text-amber-400">Pending</span>
                                ) : (
                                  'None'
                                )}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => handleOpenSnapshot(card.personnel_id)}
                            className="flex items-center justify-center space-x-1.5 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded text-xs font-mono font-medium transition-colors border border-border"
                          >
                            <Eye className="w-3.5 h-3.5 text-accent" />
                            <span>Timeline</span>
                          </button>

                          <button
                            onClick={() => {
                              window.dispatchEvent(new CustomEvent('open-welfare-case', { detail: { personnelId: card.personnel_id } }));
                              const el = document.getElementById('welfare-case-management');
                              if (el) el.scrollIntoView({ behavior: 'smooth' });
                            }}
                            className="flex items-center justify-center space-x-1.5 py-1.5 bg-indigo-950/40 hover:bg-indigo-950/70 text-indigo-300 rounded text-xs font-mono font-medium transition-colors border border-indigo-800/40"
                          >
                            <FolderKanban className="w-3.5 h-3.5 text-indigo-400" />
                            <span>Open Case</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 6. Personnel Detail Modal (Chronological Unified Timeline) */}
      {selectedPersonnelId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-border/80 flex items-center justify-between bg-surfaceHighlight/30">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-textPrimary uppercase">
                    Unified Personnel Welfare Snapshot & Timeline
                  </h3>
                  <p className="text-xs text-textSecondary font-mono">
                    Complete multi-phase chronological audit trail for authorized review
                  </p>
                </div>
              </div>

              <button
                onClick={handleCloseSnapshot}
                className="p-1.5 hover:bg-surfaceHighlight rounded-lg text-textSecondary hover:text-textPrimary transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-6">
              {snapshotLoading && (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <RefreshCw className="w-6 h-6 animate-spin text-accent" />
                  <p className="text-xs text-textSecondary font-mono">
                    Constructing unified timeline & aggregating authoritative signals...
                  </p>
                </div>
              )}

              {snapshotError && (
                <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg flex items-center space-x-3 text-red-200 text-xs">
                  <AlertOctagon className="w-5 h-5 shrink-0 text-red-400" />
                  <div>
                    <p className="font-semibold">Snapshot Load Error</p>
                    <p className="mt-0.5">{snapshotError}</p>
                  </div>
                </div>
              )}

              {snapshotData && (
                <div className="space-y-6">
                  {/* Subject Overview Card */}
                  <div className="p-4 bg-surfaceHighlight/40 border border-border/60 rounded-lg flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                      <div className="text-lg font-bold text-textPrimary">{snapshotData.name}</div>
                      <div className="text-xs font-mono text-textSecondary mt-0.5">
                        Code: {snapshotData.personnel_code} • Battalion: {snapshotData.battalion || 'Unassigned'} • Location: {snapshotData.location || 'Base'}
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <div className="px-3 py-1 bg-surfaceHighlight border border-border rounded text-xs font-mono">
                        <span className="text-textSecondary">Review Indicator: </span>
                        <strong
                          className={
                            snapshotData.human_review_indicator.review_attention_level === 'REVIEW'
                              ? 'text-rose-400'
                              : snapshotData.human_review_indicator.review_attention_level === 'MONITOR'
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }
                        >
                          {snapshotData.human_review_indicator.review_attention_level}
                        </strong>
                      </div>

                      <div className="px-3 py-1 bg-surfaceHighlight border border-border rounded text-xs font-mono">
                        <span className="text-textSecondary">Freshness: </span>
                        <strong className="text-textPrimary">
                          {snapshotData.data_freshness.overall_freshness_status}
                        </strong>
                      </div>

                      <button
                        onClick={() => {
                          const pId = snapshotData.personnel_id;
                          handleCloseSnapshot();
                          setTimeout(() => {
                            window.dispatchEvent(new CustomEvent('open-welfare-case', { detail: { personnelId: pId } }));
                            const el = document.getElementById('welfare-case-management');
                            if (el) el.scrollIntoView({ behavior: 'smooth' });
                          }, 100);
                        }}
                        className="px-3 py-1 bg-accent hover:bg-accent/80 text-white rounded text-xs font-mono font-medium transition-colors shadow-sm flex items-center space-x-1.5"
                      >
                        <FolderKanban className="w-3.5 h-3.5" />
                        <span>Open Welfare Case</span>
                      </button>
                    </div>
                  </div>

                  {/* Review Explanation */}
                  {snapshotData.human_review_indicator.reasons.length > 0 && (
                    <div className="p-3 bg-indigo-950/20 border border-indigo-800/40 rounded-lg text-xs space-y-1">
                      <div className="font-semibold text-indigo-300 flex items-center space-x-1.5">
                        <Info className="w-3.5 h-3.5" />
                        <span>Review Indicator Justification (Rule-based, Non-Scored):</span>
                      </div>
                      <ul className="list-disc list-inside space-y-0.5 text-textSecondary font-mono pl-1">
                        {snapshotData.human_review_indicator.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Signal Matrix Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Phase 34 Risk Details */}
                    <div className="p-3.5 bg-surfaceHighlight/20 border border-border/60 rounded-lg space-y-2 text-xs font-mono">
                      <div className="font-bold text-textPrimary uppercase border-b border-border/40 pb-1.5 flex justify-between">
                        <span>Phase 34 Authoritative Risk</span>
                        <span className="text-accent">{snapshotData.current_risk.data_sufficiency}</span>
                      </div>
                      <div className="space-y-1 pt-1 text-textSecondary">
                        <div>
                          Category:{' '}
                          <strong className="text-textPrimary">
                            {snapshotData.current_risk.stress_level || 'Unavailable'}
                          </strong>
                        </div>
                        <div>
                          Score:{' '}
                          <strong className="text-textPrimary">
                            {snapshotData.current_risk.risk_score !== null
                              ? snapshotData.current_risk.risk_score
                              : 'Unavailable'}
                          </strong>
                        </div>
                        <div>
                          Priority:{' '}
                          <strong className="text-textPrimary">
                            {snapshotData.current_risk.risk_priority || 'Unavailable'}
                          </strong>
                        </div>
                        <div>
                          Last Assessed:{' '}
                          <span className="text-textPrimary">
                            {snapshotData.data_freshness.last_assessment_relative}
                          </span>
                        </div>
                        {snapshotData.current_risk.key_factors.length > 0 && (
                          <div className="pt-1">
                            <span>Key Factors: </span>
                            <span className="text-textPrimary">
                              {snapshotData.current_risk.key_factors.join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Phase 36 Trend Details */}
                    <div className="p-3.5 bg-surfaceHighlight/20 border border-border/60 rounded-lg space-y-2 text-xs font-mono">
                      <div className="font-bold text-textPrimary uppercase border-b border-border/40 pb-1.5 flex justify-between">
                        <span>Phase 36 Longitudinal Trend</span>
                        <span className="text-indigo-400">{snapshotData.trend.data_sufficiency}</span>
                      </div>
                      <div className="space-y-1 pt-1 text-textSecondary">
                        <div>
                          Direction:{' '}
                          <strong className="text-textPrimary">
                            {snapshotData.trend.trend_direction}
                          </strong>
                        </div>
                        <div>
                          Persistence:{' '}
                          <strong className="text-textPrimary">
                            {snapshotData.trend.persistence}
                          </strong>
                        </div>
                        <div>
                          Acceleration:{' '}
                          <strong className="text-textPrimary">
                            {snapshotData.trend.acceleration}
                          </strong>
                        </div>
                        <div>
                          Baseline Mean:{' '}
                          <span className="text-textPrimary">
                            {snapshotData.trend.personal_baseline_score !== null
                              ? snapshotData.trend.personal_baseline_score
                              : 'Unavailable'}
                          </span>
                        </div>
                        <div>
                          Explanation:{' '}
                          <span className="text-textPrimary">{snapshotData.trend.explanation}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Chronological Unified Timeline */}
                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between border-b border-border/60 pb-2">
                      <h4 className="text-xs font-bold text-textPrimary uppercase tracking-wide flex items-center space-x-1.5">
                        <Clock className="w-4 h-4 text-accent" />
                        <span>Chronological Unified Timeline (Descending)</span>
                      </h4>
                      <span className="text-[10px] font-mono text-textSecondary">
                        {snapshotData.timeline.length} Recorded Events
                      </span>
                    </div>

                    {snapshotData.timeline.length === 0 ? (
                      <div className="py-6 text-center text-xs text-textSecondary font-mono">
                        No recorded timeline events for this personnel member.
                      </div>
                    ) : (
                      <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
                        {snapshotData.timeline.map((evt: TimelineEventItem, idx: number) => {
                          const phaseBadgeColor =
                            evt.phase === 'Phase 34'
                              ? 'bg-amber-950/60 text-amber-300 border-amber-800/40'
                              : evt.phase === 'Phase 37'
                              ? 'bg-rose-950/60 text-rose-300 border-rose-800/40'
                              : evt.phase === 'Phase 39'
                              ? 'bg-indigo-950/60 text-indigo-300 border-indigo-800/40'
                              : evt.phase === 'Phase 40'
                              ? 'bg-blue-950/60 text-blue-300 border-blue-800/40'
                              : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/40';

                          return (
                            <div
                              key={idx}
                              className="p-3 bg-surfaceHighlight/20 border border-border/40 rounded-lg flex items-start space-x-3 text-xs"
                            >
                              <div className="pt-0.5 shrink-0">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${phaseBadgeColor}`}
                                >
                                  {evt.phase}
                                </span>
                              </div>

                              <div className="flex-1 space-y-1">
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold text-textPrimary">{evt.title}</span>
                                  <span className="text-[10px] font-mono text-textSecondary">
                                    {evt.relative_time}
                                  </span>
                                </div>
                                <p className="text-xs text-textSecondary font-mono">{evt.summary}</p>
                                <div className="text-[10px] font-mono text-textSecondary/80">
                                  Status: <span className="text-textPrimary">{evt.status}</span>
                                  {evt.severity_or_priority && (
                                    <> • Level/Priority: <span className="text-textPrimary">{evt.severity_or_priority}</span></>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Modal Disclaimer */}
                  <div className="p-3 bg-surfaceHighlight/30 border border-border/60 rounded-lg text-[11px] text-textSecondary font-mono leading-relaxed">
                    {snapshotData.disclaimer}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-border/80 flex justify-end bg-surfaceHighlight/30">
              <button
                onClick={handleCloseSnapshot}
                className="px-4 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-border"
              >
                Close Snapshot
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
