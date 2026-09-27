'use client';

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { StressAssessmentOut } from '@/types/api';
import {
  generateCalendarGrid,
  aggregateDailyAssessments,
  getRiskColor,
  CalendarDay,
  WEEKDAY_LABELS,
} from '@/lib/calendarHeatmap';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Info,
  ShieldAlert,
  X,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';

interface RiskCalendarHeatmapProps {
  assessments: StressAssessmentOut[];
  onRefresh?: () => void;
  className?: string;
}

export function RiskCalendarHeatmap({
  assessments,
  onRefresh,
  className = '',
}: RiskCalendarHeatmapProps) {
  // State for time range duration: 52 weeks (1 year), 26 weeks (6 months), 13 weeks (3 months)
  const [weeksCount, setWeeksCount] = useState<number>(52);
  // Period offset in number of periods (0 = current, 1 = previous period, etc.)
  const [periodOffset, setPeriodOffset] = useState<number>(0);

  // Selected cell for persistent inspection (mobile friendly tap card)
  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null);

  // Hovered cell for quick desktop tooltip
  const [hoveredDay, setHoveredDay] = useState<CalendarDay | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // 1. Deterministically aggregate assessments by calendar day (Latest daily assessment rule)
  const dailyMap = useMemo(() => {
    return aggregateDailyAssessments(assessments);
  }, [assessments]);

  // 2. Compute reference date based on periodOffset
  const referenceDate = useMemo(() => {
    const d = new Date();
    if (periodOffset > 0) {
      d.setDate(d.getDate() - periodOffset * weeksCount * 7);
    }
    return d;
  }, [periodOffset, weeksCount]);

  // 3. Generate calendar grid
  const gridResult = useMemo(() => {
    return generateCalendarGrid(referenceDate, weeksCount, dailyMap);
  }, [referenceDate, weeksCount, dailyMap]);

  // Scroll to the far right (most recent days) on initial load or range change
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollLeft = scrollContainerRef.current.scrollWidth;
    }
  }, [weeksCount, periodOffset]);

  const handleCellMouseEnter = (day: CalendarDay, e: React.MouseEvent) => {
    if (day.isFuture) return;
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const containerRect = containerRef.current?.getBoundingClientRect();

    if (containerRect) {
      setTooltipPos({
        x: rect.left - containerRect.left + rect.width / 2,
        y: rect.top - containerRect.top - 8,
      });
    }
    setHoveredDay(day);
  };

  const handleCellMouseLeave = () => {
    setHoveredDay(null);
    setTooltipPos(null);
  };

  const handleCellClick = (day: CalendarDay) => {
    if (day.isFuture) return;
    setHoveredDay(null);
    setTooltipPos(null);
    setSelectedDay(selectedDay?.date === day.date ? null : day);
  };

  const handleKeyDown = (day: CalendarDay, e: React.KeyboardEvent) => {
    if (day.isFuture) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setHoveredDay(null);
      setTooltipPos(null);
      setSelectedDay(selectedDay?.date === day.date ? null : day);
    }
  };

  const formatDateLabel = (dateStr: string) => {
    const [y, m, d] = dateStr.split('-').map(Number);
    const date = new Date(y, m - 1, d);
    return date.toLocaleDateString(undefined, {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div
      ref={containerRef}
      className={`relative w-full bg-mb-glass-strong backdrop-blur-xl p-4 sm:p-6 rounded-3xl shadow-[0_8px_30px_rgba(0,0,0,0.2)] border border-mb-glass-border flex flex-col gap-4 ${className}`}
    >
      {/* Top Header: Title */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs sm:text-sm font-bold text-mb-text-primary uppercase tracking-wider">
              Risk Trends Heatmap
            </h3>
            <span className="text-[10px] text-mb-text-muted font-mono block">
              Continuous 0&ndash;100 Risk Intensity
            </span>
          </div>
        </div>
      </div>

      {/* Controls Row: Period Date Range & Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-white/5">
        <span className="text-[11px] font-medium text-mb-text-secondary">
          {formatDateLabel(gridResult.startDate)} &ndash; {formatDateLabel(gridResult.endDate)}
        </span>

        {/* Range & Navigation Controls */}
        <div className="flex items-center gap-1.5">
          {/* Duration Pills */}
          <div className="flex items-center bg-black/25 p-0.5 rounded-xl border border-mb-glass-border text-[11px] font-medium">
            <button
              type="button"
              onClick={() => {
                setWeeksCount(52);
                setPeriodOffset(0);
              }}
              className={`px-2 py-0.5 rounded-lg transition-all ${
                weeksCount === 52
                  ? 'bg-mb-accent text-mb-text-dark font-bold shadow'
                  : 'text-mb-text-secondary hover:text-white'
              }`}
            >
              12 Mo
            </button>
            <button
              type="button"
              onClick={() => {
                setWeeksCount(26);
                setPeriodOffset(0);
              }}
              className={`px-2 py-0.5 rounded-lg transition-all ${
                weeksCount === 26
                  ? 'bg-mb-accent text-mb-text-dark font-bold shadow'
                  : 'text-mb-text-secondary hover:text-white'
              }`}
            >
              6 Mo
            </button>
            <button
              type="button"
              onClick={() => {
                setWeeksCount(13);
                setPeriodOffset(0);
              }}
              className={`px-2 py-0.5 rounded-lg transition-all ${
                weeksCount === 13
                  ? 'bg-mb-accent text-mb-text-dark font-bold shadow'
                  : 'text-mb-text-secondary hover:text-white'
              }`}
            >
              3 Mo
            </button>
          </div>

          {/* Period Arrows */}
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setPeriodOffset((prev) => prev + 1)}
              className="p-1.5 rounded-lg bg-black/20 hover:bg-black/40 text-mb-text-secondary hover:text-white border border-mb-glass-border transition"
              title="Previous period"
              aria-label="Previous historical period"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            {periodOffset > 0 ? (
              <button
                type="button"
                onClick={() => setPeriodOffset(0)}
                className="px-1.5 py-0.5 text-[9px] font-bold uppercase rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 transition"
              >
                Today
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => setPeriodOffset((prev) => Math.max(0, prev - 1))}
              disabled={periodOffset === 0}
              className={`p-1.5 rounded-lg border border-mb-glass-border transition ${
                periodOffset === 0
                  ? 'opacity-30 cursor-not-allowed bg-black/10 text-mb-text-muted'
                  : 'bg-black/20 hover:bg-black/40 text-mb-text-secondary hover:text-white'
              }`}
              title="Next period"
              aria-label="Next historical period"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-3 gap-2 py-2 px-3 bg-black/25 rounded-2xl border border-mb-glass-border/60 text-xs">
        <div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted block">
            Days Tracked
          </span>
          <span className="text-sm font-semibold text-mb-text-primary">
            {gridResult.totalDaysWithData}{' '}
            <span className="text-[10px] font-normal text-mb-text-secondary">active entries</span>
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted block">
            Avg Risk
          </span>
          <span className="text-sm font-semibold text-mb-text-primary">
            {gridResult.totalDaysWithData > 0 ? `${gridResult.averageRiskScore} / 100` : '&mdash;'}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted block">
            Peak Risk
          </span>
          <span className="text-sm font-semibold text-mb-text-primary">
            {gridResult.totalDaysWithData > 0 ? `${gridResult.maxRiskScore} / 100` : '&mdash;'}
          </span>
        </div>
      </div>

      {/* Main Calendar Heatmap Matrix */}
      <div
        ref={scrollContainerRef}
        className="w-full overflow-x-auto pb-3 pt-1 scrollbar-thin select-none"
        role="region"
        aria-label="Calendar Heatmap of Risk Scores"
      >
        <div className="inline-flex flex-col gap-1 min-w-max">
          {/* Month Labels Header Row */}
          <div className="flex text-[10px] font-mono font-semibold text-mb-text-secondary mb-1 pl-8">
            {gridResult.weeks.map((week, wIdx) => (
              <div
                key={`m-label-${wIdx}`}
                className="w-3.5 sm:w-4 text-center shrink-0"
              >
                {week.monthLabel ? (
                  <span className="text-[10px] text-mb-accent font-bold uppercase tracking-wider -translate-x-1 block whitespace-nowrap">
                    {week.monthLabel}
                  </span>
                ) : null}
              </div>
            ))}
          </div>

          {/* 7 Rows for Weekdays (Mon to Sun) */}
          <div className="flex flex-col gap-1" role="grid" aria-label="Risk contribution calendar">
            {WEEKDAY_LABELS.map((dayLabel, dayIndex) => (
              <div
                key={`weekday-${dayLabel}`}
                className="flex items-center gap-1.5"
                role="row"
              >
                {/* Weekday Label */}
                <span className="w-6 text-[10px] font-mono text-mb-text-secondary font-medium text-left shrink-0">
                  {dayIndex % 2 === 0 ? dayLabel : ''}
                </span>

                {/* Weekday Cells Across All Week Columns */}
                <div className="flex gap-1 sm:gap-1.5">
                  {gridResult.weeks.map((week) => {
                    const day = week.days[dayIndex];
                    if (!day) return null;

                    const isSelected = selectedDay?.date === day.date;
                    const hasData = day.hasData;
                    const isFuture = day.isFuture;

                    // Color determination
                    let cellBg = 'rgba(255, 255, 255, 0.08)'; // Neutral for No Data
                    let cellBorder = 'rgba(255, 255, 255, 0.10)';

                    if (isFuture) {
                      cellBg = 'transparent';
                      cellBorder = 'rgba(255, 255, 255, 0.04)';
                    } else if (hasData && day.riskScore !== undefined) {
                      cellBg = getRiskColor(day.riskScore);
                      cellBorder = cellBg;
                    }

                    const ariaLabel = isFuture
                      ? `${formatDateLabel(day.date)} (Upcoming)`
                      : hasData
                      ? `${formatDateLabel(day.date)}: Risk Score ${day.riskScore?.toFixed(1)} out of 100, ${day.stressLevel} stress level`
                      : `${formatDateLabel(day.date)}: No assessment data`;

                    return (
                      <button
                        key={day.date}
                        type="button"
                        role="gridcell"
                        tabIndex={isFuture ? -1 : 0}
                        aria-label={ariaLabel}
                        onClick={() => handleCellClick(day)}
                        onKeyDown={(e) => handleKeyDown(day, e)}
                        onMouseEnter={(e) => handleCellMouseEnter(day, e)}
                        onMouseLeave={handleCellMouseLeave}
                        disabled={isFuture}
                        style={{
                          backgroundColor: cellBg,
                          borderColor: cellBorder,
                        }}
                        className={`w-3 h-3 sm:w-3.5 sm:h-3.5 rounded-[3px] border transition-transform duration-150 focus:outline-none ${
                          isFuture
                            ? 'cursor-default opacity-20 border-dashed'
                            : 'cursor-pointer hover:scale-125 hover:z-20 hover:shadow-md hover:ring-1 hover:ring-white/60'
                        } ${
                          isSelected
                            ? 'ring-2 ring-white scale-125 z-20 shadow-lg'
                            : ''
                        }`}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Floating Hover Tooltip */}
      {hoveredDay && tooltipPos && (
        <div
          style={{
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y}px`,
            transform: 'translate(-50%, -100%)',
          }}
          className="absolute z-50 pointer-events-none bg-slate-950/95 backdrop-blur-md border border-white/20 text-white rounded-xl py-2 px-3 shadow-2xl text-xs max-w-xs transition-opacity duration-150"
        >
          <div className="font-semibold text-gray-200 text-[11px] mb-1">
            {formatDateLabel(hoveredDay.date)}
          </div>
          {hoveredDay.hasData ? (
            <div className="space-y-1">
              <div className="flex items-center justify-between gap-3">
                <span className="text-gray-400 text-[10px] uppercase">Risk Score</span>
                <span
                  style={{ color: getRiskColor(hoveredDay.riskScore ?? 0) }}
                  className="font-bold text-xs"
                >
                  {hoveredDay.riskScore?.toFixed(1)} / 100
                </span>
              </div>
              <div className="flex items-center justify-between gap-3 text-[10px]">
                <span className="text-gray-400">Level &bull; Priority</span>
                <span className="font-medium text-emerald-400">
                  {hoveredDay.stressLevel} &bull; {hoveredDay.riskPriority}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3 text-[10px]">
                <span className="text-gray-400">Calibrated Prob</span>
                <span className="font-mono text-gray-300">
                  {((hoveredDay.riskProbability ?? 0) * 100).toFixed(1)}%
                </span>
              </div>
              {hoveredDay.assessmentsCount && hoveredDay.assessmentsCount > 1 ? (
                <div className="text-[9px] text-amber-400/90 font-mono pt-0.5 border-t border-white/10">
                  Latest of {hoveredDay.assessmentsCount} daily assessments
                </div>
              ) : null}
            </div>
          ) : (
            <div className="text-[11px] text-gray-400">No assessment recorded</div>
          )}
        </div>
      )}

      {/* Selected Day Expanded Detail Card (Tap / Click View) */}
      {selectedDay && (
        <div className="p-4 bg-black/40 backdrop-blur-lg rounded-2xl border border-mb-glass-border animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-mb-accent" />
              <span className="text-xs font-bold text-mb-text-primary">
                {formatDateLabel(selectedDay.date)}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setSelectedDay(null)}
              className="p-1 text-mb-text-secondary hover:text-white rounded-lg transition"
              title="Close details"
              aria-label="Close details"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {selectedDay.hasData ? (
            <div className="pt-3 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted block">
                    Calculated Risk Score
                  </span>
                  <div className="flex items-baseline gap-2 mt-0.5">
                    <span
                      style={{ color: getRiskColor(selectedDay.riskScore ?? 0) }}
                      className="text-2xl font-black"
                    >
                      {selectedDay.riskScore?.toFixed(1)}
                    </span>
                    <span className="text-xs text-mb-text-muted">/ 100</span>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    style={{
                      backgroundColor: `${getRiskColor(selectedDay.riskScore ?? 0)}20`,
                      color: getRiskColor(selectedDay.riskScore ?? 0),
                      borderColor: `${getRiskColor(selectedDay.riskScore ?? 0)}40`,
                    }}
                    className="inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border"
                  >
                    {selectedDay.stressLevel} Risk
                  </span>
                  <span className="block text-[10px] text-mb-text-secondary mt-1">
                    Priority: <strong className="text-white">{selectedDay.riskPriority}</strong>
                  </span>
                </div>
              </div>

              {/* Contributing factors if present */}
              {selectedDay.keyFactors && selectedDay.keyFactors.length > 0 && (
                <div className="pt-2 border-t border-white/5">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted block mb-1.5">
                    Contributing Stress Factors
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedDay.keyFactors.map((factor, fIdx) => (
                      <span
                        key={fIdx}
                        className="px-2 py-0.5 bg-white/5 rounded-md border border-white/10 text-[10px] text-mb-text-secondary"
                      >
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Model version & Timestamp */}
              <div className="flex items-center justify-between text-[10px] text-mb-text-muted pt-2 border-t border-white/5 font-mono">
                <span>Model: {selectedDay.modelVersion || 'ensemble_v33'}</span>
                <span>
                  {selectedDay.assessmentsCount && selectedDay.assessmentsCount > 1
                    ? `Latest of ${selectedDay.assessmentsCount} submissions`
                    : '1 assessment'}
                </span>
              </div>
            </div>
          ) : (
            <div className="pt-3 text-center text-xs text-mb-text-secondary py-2">
              <Info className="w-4 h-4 mx-auto mb-1 text-mb-text-muted" />
              <span>No assessment was completed on this date.</span>
            </div>
          )}
        </div>
      )}

      {/* Bottom Footer: Clean GitHub/LeetCode Style Legend */}
      <div className="pt-2 border-t border-mb-glass-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        {/* No Data Legend Item */}
        <div className="flex items-center gap-2">
          <div
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              borderColor: 'rgba(255, 255, 255, 0.10)',
            }}
            className="w-3.5 h-3.5 rounded-[3px] border"
          />
          <span className="text-[11px] text-mb-text-secondary font-medium">
            No assessment data
          </span>
        </div>

        {/* Continuous Gradient Swatch Bar */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-mb-text-secondary font-medium">Less Risk</span>
          <div className="flex items-center gap-1">
            {[0, 25, 50, 75, 100].map((score) => (
              <div
                key={score}
                style={{
                  backgroundColor: getRiskColor(score),
                  borderColor: getRiskColor(score),
                }}
                className="w-3.5 h-3.5 rounded-[3px] border"
                title={`Score ${score}`}
              />
            ))}
          </div>
          <span className="text-[11px] text-mb-text-secondary font-medium">More Risk</span>
        </div>
      </div>
    </div>
  );
}
