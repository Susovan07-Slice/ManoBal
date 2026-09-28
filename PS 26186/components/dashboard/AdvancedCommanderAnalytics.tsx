'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { getCommanderAnalytics } from '@/lib/analytics';
import { CommanderAnalyticsResponse } from '@/types/api';
import {
  ShieldAlert,
  Users,
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  Clock,
  HeartHandshake,
  Lock,
  RefreshCw,
  Info,
  Calendar,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';

export default function AdvancedCommanderAnalytics() {
  const [data, setData] = useState<CommanderAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [timeFilter, setTimeFilter] = useState<string>('30d');
  const [customStart, setCustomStart] = useState<string>('');
  const [customEnd, setCustomEnd] = useState<string>('');
  const [showCustomRange, setShowCustomRange] = useState<boolean>(false);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCommanderAnalytics({
        timeFilter,
        startDate: customStart || undefined,
        endDate: customEnd || undefined,
      });
      setData(res);
    } catch (err: any) {
      console.error('Failed to load commander analytics:', err);
      setError(err?.message || 'Unable to retrieve commander analytics.');
    } finally {
      setLoading(false);
    }
  }, [timeFilter, customStart, customEnd]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleFilterChange = (filter: string) => {
    setTimeFilter(filter);
    if (filter !== 'custom') {
      setShowCustomRange(false);
    } else {
      setShowCustomRange(true);
    }
  };

  return (
    <div className="bg-surface border border-surfaceHighlight rounded-xl p-6 space-y-6 shadow-md" id="advanced-analytics">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-surfaceHighlight">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/40 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4 text-accent" />
            </div>
            <div>
              <h2 className="text-base font-bold text-textPrimary uppercase tracking-wider">
                Unit-Level Welfare Intelligence & Advanced Analytics
              </h2>
              <p className="text-xs text-textSecondary font-mono mt-0.5">
                Authorized Organizational Scope: {data?.scope?.battalion || 'Command Scope'} • {data?.scope?.location || 'All Assigned Outposts'}
              </p>
            </div>
          </div>
        </div>

        {/* Filter Controls & Refresh */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="bg-surfaceHighlight/60 p-1 rounded-lg border border-surfaceHighlight flex items-center space-x-1 text-xs font-mono">
            {['7d', '30d', '90d', 'all', 'custom'].map((f) => (
              <button
                key={f}
                onClick={() => handleFilterChange(f)}
                className={`px-2.5 py-1 rounded transition-colors uppercase ${
                  timeFilter === f
                    ? 'bg-accent text-[#FAFAFC] font-semibold shadow-xs'
                    : 'text-textSecondary hover:text-textPrimary hover:bg-surfaceHighlight'
                }`}
              >
                {f === 'all' ? 'All' : f}
              </button>
            ))}
          </div>

          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono transition-colors border border-surfaceBorder disabled:opacity-50"
            title="Refresh Unit Analytics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Custom Date Range Picker */}
      {showCustomRange && (
        <div className="flex flex-wrap items-center gap-3 p-3 bg-surfaceHighlight/40 border border-surfaceBorder rounded-lg text-xs font-mono">
          <Calendar className="w-4 h-4 text-accent" />
          <span className="text-textSecondary">Custom Range:</span>
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="bg-surface border border-surfaceBorder rounded px-2 py-1 text-textPrimary"
          />
          <span className="text-textSecondary">to</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="bg-surface border border-surfaceBorder rounded px-2 py-1 text-textPrimary"
          />
          <button
            onClick={fetchAnalytics}
            className="px-3 py-1 bg-accent text-[#FAFAFC] font-semibold rounded hover:bg-accent/90"
          >
            Apply
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-4 animate-pulse">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-24 bg-surfaceHighlight/50 rounded-lg"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="h-64 bg-surfaceHighlight/50 rounded-lg"></div>
            <div className="h-64 bg-surfaceHighlight/50 rounded-lg"></div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {!loading && error && (
        <div className="p-4 bg-[#FAF0F0] border border-[#E8B4B4] rounded-lg flex items-center space-x-3 text-[#964747] text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 text-[#C26D6D]" />
          <div>
            <p className="font-semibold">Analytics Sync Error</p>
            <p className="text-xs text-[#964747] mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Privacy Protection Notice (INSUFFICIENT_GROUP_SIZE) */}
      {!loading && data?.status === 'INSUFFICIENT_GROUP_SIZE' && (
        <div className="p-5 bg-[#FDF6EE] border border-[#F3D2AE] rounded-lg space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-[#FDF6EE] border border-[#F3D2AE] flex items-center justify-center shrink-0">
              <Lock className="w-4 h-4 text-[#8E5B23]" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#8E5B23] uppercase tracking-wide">
                Privacy Protection Activated (k-Anonymity)
              </h3>
              <p className="text-xs text-[#8E5B23]/80 font-mono mt-0.5">
                Authorized Personnel in Scope: {data.scope.total_authorized_personnel} (Minimum required: {data.scope.min_group_size_threshold})
              </p>
            </div>
          </div>
          <p className="text-xs text-textSecondary leading-relaxed">
            {data.message || 'Aggregate welfare analytics are withheld for populations below the privacy threshold to prevent deductive re-identification of individual risk classifications.'}
          </p>
        </div>
      )}

      {/* Insufficient Data State */}
      {!loading && data?.status === 'INSUFFICIENT_DATA' && (
        <div className="p-6 bg-surfaceHighlight/20 border border-surfaceHighlight rounded-lg text-center space-y-2">
          <Info className="w-6 h-6 text-accent mx-auto" />
          <h4 className="text-sm font-semibold text-textPrimary">No Assessments Recorded</h4>
          <p className="text-xs text-textSecondary max-w-md mx-auto">
            Authorized personnel in scope have not submitted assessments within the selected time window. Once regular check-ins are logged, aggregate welfare patterns will appear here.
          </p>
        </div>
      )}

      {/* Analytics Content When Available */}
      {!loading && data?.status === 'SUCCESS' && data.summary && (
        <div className="space-y-6">
          {/* Section 1: KPI Overview Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {/* Total Personnel & Coverage */}
            <div className="p-4 bg-surfaceHighlight/30 border border-surfaceHighlight rounded-lg space-y-1">
              <div className="flex items-center justify-between text-xs text-textSecondary font-mono">
                <span>Roster Coverage</span>
                <Users className="w-4 h-4 text-accent" />
              </div>
              <div className="text-xl font-bold text-textPrimary font-mono">
                {data.summary.assessed_personnel_count}
                <span className="text-xs text-textSecondary font-normal"> / {data.summary.total_authorized_personnel}</span>
              </div>
              <p className="text-[11px] text-textSecondary font-mono">
                {data.summary.assessment_coverage_pct}% checked in
              </p>
            </div>

            {/* Active Alerts */}
            <div className="p-4 bg-surfaceHighlight/40 border border-surfaceBorder rounded-lg space-y-1">
              <div className="flex items-center justify-between text-xs text-textSecondary font-mono">
                <span>Open Alerts</span>
                <AlertTriangle className="w-4 h-4 text-[#D99B5C]" />
              </div>
              <div className="text-xl font-bold text-[#8E5B23] font-mono">
                {data.summary.open_alerts_count}
              </div>
              <p className="text-[11px] text-textSecondary font-mono">
                Needs review
              </p>
            </div>

            {/* Worsening Trajectory */}
            <div className="p-4 bg-surfaceHighlight/40 border border-surfaceBorder rounded-lg space-y-1">
              <div className="flex items-center justify-between text-xs text-textSecondary font-mono">
                <span>Worsening Trend</span>
                <TrendingUp className="w-4 h-4 text-[#C26D6D]" />
              </div>
              <div className="text-xl font-bold text-[#C26D6D] font-mono">
                {data.summary.worsening_trend_pct}%
              </div>
              <p className="text-[11px] text-textSecondary font-mono">
                {data.summary.worsening_trend_count} personnel
              </p>
            </div>

            {/* Persistent Elevated Risk */}
            <div className="p-4 bg-surfaceHighlight/40 border border-surfaceBorder rounded-lg space-y-1">
              <div className="flex items-center justify-between text-xs text-textSecondary font-mono">
                <span>Persistent Elevated</span>
                <Clock className="w-4 h-4 text-[#CB7A5C]" />
              </div>
              <div className="text-xl font-bold text-[#CB7A5C] font-mono">
                {data.summary.persistent_elevated_pct}%
              </div>
              <p className="text-[11px] text-textSecondary font-mono">
                {data.summary.persistent_elevated_count} personnel
              </p>
            </div>

            {/* Scope Average Risk Score */}
            <div className="p-4 bg-surfaceHighlight/40 border border-surfaceBorder rounded-lg space-y-1">
              <div className="flex items-center justify-between text-xs text-textSecondary font-mono">
                <span>Mean Risk Score</span>
                <Activity className="w-4 h-4 text-accent" />
              </div>
              <div className="text-xl font-bold text-textPrimary font-mono">
                {data.summary.average_risk_score !== null ? data.summary.average_risk_score : '—'}
                <span className="text-xs text-textSecondary font-normal"> / 100</span>
              </div>
              <p className="text-[11px] text-textSecondary font-mono">
                Continuous scale
              </p>
            </div>
          </div>

          {/* Section 2: Current Risk Distribution & Longitudinal Trend */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Distribution Card */}
            {data.risk_distribution && (
              <div className="p-4 bg-surface border border-surfaceBorder rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider">
                      Current Risk Distribution (Latest Assessments)
                    </h3>
                    <p className="text-[11px] text-textSecondary font-mono">
                      Authoritative Phase 34 V2 5-tier classification ({data.risk_distribution.total_represented} unique personnel)
                    </p>
                  </div>
                </div>

                <div className="space-y-3 pt-2">
                  {data.risk_distribution.categories.map((cat) => {
                    const colorMap: Record<string, { bg: string; text: string; bar: string }> = {
                      Low: { bg: 'bg-[#EEF6F2]', text: 'text-[#2D6346]', bar: 'bg-[#7BA083]' },
                      Moderate: { bg: 'bg-[#EEF4F8]', text: 'text-[#3E6580]', bar: 'bg-[#5B88A5]' },
                      Elevated: { bg: 'bg-[#FDF6EE]', text: 'text-[#8E5B23]', bar: 'bg-[#D99B5C]' },
                      High: { bg: 'bg-[#FDF2EC]', text: 'text-[#8F4B33]', bar: 'bg-[#CB7A5C]' },
                      Critical: { bg: 'bg-[#FAF0F0]', text: 'text-[#964747]', bar: 'bg-[#C26D6D]' },
                    };
                    const styling = colorMap[cat.label] || { bg: 'bg-surfaceHighlight', text: 'text-textPrimary', bar: 'bg-accent' };

                    return (
                      <div key={cat.label} className="space-y-1">
                        <div className="flex items-center justify-between text-xs font-mono">
                          <span className={`font-semibold ${styling.text}`}>{cat.label}</span>
                          <span className="text-textSecondary">
                            {cat.count} personnel ({cat.percentage}%)
                          </span>
                        </div>
                        <div className="w-full h-2 bg-surfaceHighlight rounded-full overflow-hidden">
                          <div
                            className={`h-full ${styling.bar} transition-all duration-500 rounded-full`}
                            style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Longitudinal Trend Card */}
            {data.trend && (
              <div className="p-4 bg-surface border border-surfaceBorder rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider">
                      Longitudinal Organizational Trajectory
                    </h3>
                    <p className="text-[11px] text-textSecondary font-mono">
                      Phase 36 longitudinal trajectory across recent assessment windows
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold uppercase ${
                      data.trend.direction === 'IMPROVING'
                        ? 'bg-[#EEF6F2] text-[#2D6346] border border-[#BBD9C7]'
                        : data.trend.direction === 'WORSENING'
                        ? 'bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]'
                        : 'bg-surfaceHighlight text-textSecondary border border-surfaceBorder'
                    }`}
                  >
                    {data.trend.direction}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center pt-2">
                  <div className="p-2.5 bg-[#EEF6F2]/70 rounded-lg border border-[#BBD9C7]">
                    <span className="text-[10px] text-textSecondary font-mono block">Improving</span>
                    <span className="text-base font-bold text-[#2D6346] font-mono">{data.trend.improving_pct}%</span>
                    <span className="text-[10px] text-textSecondary block font-mono">{data.trend.improving_count} personnel</span>
                  </div>
                  <div className="p-2.5 bg-[#EEF4F8]/70 rounded-lg border border-[#BCD3E3]">
                    <span className="text-[10px] text-textSecondary font-mono block">Stable</span>
                    <span className="text-base font-bold text-[#3E6580] font-mono">{data.trend.stable_pct}%</span>
                    <span className="text-[10px] text-textSecondary block font-mono">{data.trend.stable_count} personnel</span>
                  </div>
                  <div className="p-2.5 bg-[#FAF0F0] rounded-lg border border-[#E8B4B4]">
                    <span className="text-[10px] text-textSecondary font-mono block">Worsening</span>
                    <span className="text-base font-bold text-[#964747] font-mono">{data.trend.worsening_pct}%</span>
                    <span className="text-[10px] text-textSecondary block font-mono">{data.trend.worsening_count} personnel</span>
                  </div>
                </div>

                {data.trend.timeline && data.trend.timeline.length > 0 && (
                  <div className="space-y-1.5 pt-2 border-t border-surfaceHighlight">
                    <span className="text-[10px] uppercase font-mono font-semibold text-textSecondary">
                      Recent Timeline Aggregates
                    </span>
                    <div className="max-h-28 overflow-y-auto space-y-1 pr-1 font-mono text-[11px]">
                      {data.trend.timeline.slice(-5).map((pt) => (
                        <div key={pt.date} className="flex items-center justify-between p-1.5 bg-surfaceHighlight/30 rounded">
                          <span className="text-textSecondary">{pt.date}</span>
                          <span className="text-textPrimary font-semibold">Avg Risk: {pt.average_risk_score}</span>
                          <span className="text-amber-400">{pt.elevated_and_above_count} elevated</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Section 3: Welfare Factors & Alert Intelligence */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recurring Welfare Factors (Non-punitive) */}
            {data.welfare_factors && (
              <div className="p-4 bg-surfaceHighlight/20 border border-surfaceHighlight rounded-lg space-y-3">
                <div>
                  <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider flex items-center space-x-2">
                    <HeartHandshake className="w-4 h-4 text-accent" />
                    <span>Emerging Welfare Stressors & Factors</span>
                  </h3>
                  <p className="text-[11px] text-textSecondary font-mono">
                    Prevalence of workload, sleep, and recovery patterns across unit
                  </p>
                </div>

                {data.welfare_factors.factors.length === 0 ? (
                  <p className="text-xs text-textSecondary italic py-3 text-center">
                    No recurring welfare strain factors flagged in this reporting period.
                  </p>
                ) : (
                  <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                    {data.welfare_factors.factors.map((item) => (
                      <div key={item.factor} className="p-2.5 bg-surfaceHighlight/30 border border-surfaceHighlight rounded space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-textPrimary font-medium">{item.factor}</span>
                          <span className="font-mono text-accent font-semibold">{item.affected_pct}%</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-textSecondary font-mono">
                          <span>{item.affected_count} personnel affected</span>
                          <span className="uppercase text-[10px] px-1 rounded bg-surfaceHighlight">
                            Trend: {item.trend || 'STABLE'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Alert & Intervention Management */}
            {data.alerts && (
              <div className="p-4 bg-surfaceHighlight/20 border border-surfaceHighlight rounded-lg space-y-3">
                <div>
                  <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider flex items-center space-x-2">
                    <FileCheck2 className="w-4 h-4 text-amber-400" />
                    <span>Unit Alert & Intervention Posture</span>
                  </h3>
                  <p className="text-[11px] text-textSecondary font-mono">
                    Phase 37 alert status, review pipelines, and supportive check-ins
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 bg-surfaceHighlight/40 rounded border border-surfaceHighlight">
                    <span className="text-[10px] text-textSecondary font-mono block">Open</span>
                    <span className="text-sm font-bold text-amber-400 font-mono">{data.alerts.open_alerts}</span>
                  </div>
                  <div className="p-2 bg-surfaceHighlight/40 rounded border border-surfaceHighlight">
                    <span className="text-[10px] text-textSecondary font-mono block">Under Review</span>
                    <span className="text-sm font-bold text-blue-400 font-mono">{data.alerts.under_review_alerts}</span>
                  </div>
                  <div className="p-2 bg-surfaceHighlight/40 rounded border border-surfaceHighlight">
                    <span className="text-[10px] text-textSecondary font-mono block">Resolved</span>
                    <span className="text-sm font-bold text-emerald-400 font-mono">{data.alerts.resolved_alerts}</span>
                  </div>
                </div>

                {data.interventions && (
                  <div className="p-2.5 bg-surfaceHighlight/30 border border-surfaceHighlight rounded text-xs font-mono space-y-1">
                    <div className="flex justify-between text-textSecondary">
                      <span>Interventions Scheduled:</span>
                      <span className="text-textPrimary font-semibold">{data.interventions.total_interventions}</span>
                    </div>
                    <div className="flex justify-between text-textSecondary">
                      <span>Supportive Actions Completed:</span>
                      <span className="text-emerald-400 font-semibold">{data.interventions.completed}</span>
                    </div>
                    <div className="flex justify-between text-textSecondary">
                      <span>Follow-ups Pending:</span>
                      <span className="text-amber-400 font-semibold">{data.interventions.follow_up_required}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Ethical Governance Footer */}
          <div className="p-3 bg-surfaceHighlight/30 border border-surfaceHighlight rounded-lg text-[11px] text-textSecondary flex items-start space-x-2">
            <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong className="text-textPrimary">Human-in-the-Loop Welfare Intelligence:</strong> All aggregates are synthesized for supportive commander decision-support. Individual rankings or disciplinary penalties are strictly prohibited. Records analyzed: {data.data_quality.records_analyzed}.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
