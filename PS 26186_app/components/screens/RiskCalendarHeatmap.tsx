'use client';

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { StressAssessmentOut } from '@/types/api';
import {
  generateCalendarGrid,
  aggregateDailyAssessments,
  getRiskColor as originalGetRiskColor, // Keeping the import to not break anything
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

// New brand colors for the heatmap from UI redesign prompt
const HEATMAP_COLORS = ['#E6EFF4', '#7ED9B5', '#F3D36B', '#F5A25B', '#EF5A6F'];

// Helper to map continuous 0-100 score to the 5 distinct buckets
function getDiscreteRiskColor(score: number): string {
  if (score < 20) return HEATMAP_COLORS[0];
  if (score < 40) return HEATMAP_COLORS[1];
  if (score < 60) return HEATMAP_COLORS[2];
  if (score < 80) return HEATMAP_COLORS[3];
  return HEATMAP_COLORS[4];
}

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
  const [weeksCount, setWeeksCount] = useState<number>(52);
  const [periodOffset, setPeriodOffset] = useState<number>(0);
  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null);
  const [hoveredDay, setHoveredDay] = useState<CalendarDay | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const dailyMap = useMemo(() => {
    return aggregateDailyAssessments(assessments);
  }, [assessments]);

  const referenceDate = useMemo(() => {
    const d = new Date();
    if (periodOffset > 0) {
      d.setDate(d.getDate() - periodOffset * weeksCount * 7);
    }
    return d;
  }, [periodOffset, weeksCount]);

  const gridResult = useMemo(() => {
    return generateCalendarGrid(referenceDate, weeksCount, dailyMap);
  }, [referenceDate, weeksCount, dailyMap]);

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
      className={`relative w-full glass-card p-5 sm:p-6 flex flex-col gap-5 ${className}`}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-500">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-[14px] font-bold text-ink uppercase tracking-wider">
              Risk Trends Heatmap
            </h3>
            <span className="text-[11px] text-ink-3 font-medium block">
              Continuous 0&ndash;100 Risk Intensity
            </span>
          </div>
        </div>
      </div>

      {/* Controls Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-sky-200/50">
        <span className="text-[11px] font-semibold text-ink-2">
          {formatDateLabel(gridResult.startDate)} &ndash; {formatDateLabel(gridResult.endDate)}
        </span>

        {/* Range & Navigation Controls */}
        <div className="flex items-center gap-2">
          {/* Duration Segmented Control */}
          <div className="flex items-center bg-sky-50 p-1 rounded-2xl border border-sky-200 text-[11px] font-semibold">
            <button
              type="button"
              onClick={() => {
                setWeeksCount(52);
                setPeriodOffset(0);
              }}
              className={`px-2.5 py-1 rounded-xl transition-all ${
                weeksCount === 52
                  ? 'bg-white text-ink shadow-sm border border-brand-500/20 font-bold'
                  : 'text-ink-3 hover:text-ink hover:bg-white/50'
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
              className={`px-2.5 py-1 rounded-xl transition-all ${
                weeksCount === 26
                  ? 'bg-white text-ink shadow-sm border border-brand-500/20 font-bold'
                  : 'text-ink-3 hover:text-ink hover:bg-white/50'
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
              className={`px-2.5 py-1 rounded-xl transition-all ${
                weeksCount === 13
                  ? 'bg-white text-ink shadow-sm border border-brand-500/20 font-bold'
                  : 'text-ink-3 hover:text-ink hover:bg-white/50'
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
              className="w-7 h-7 flex items-center justify-center rounded-full bg-white hover:bg-sky-50 text-ink-3 hover:text-ink border border-sky-200 shadow-sm transition"
              title="Previous period"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {periodOffset > 0 ? (
              <button
                type="button"
                onClick={() => setPeriodOffset(0)}
                className="px-2 py-1 text-[10px] font-bold uppercase rounded-full bg-brand-100 text-brand-600 transition"
              >
                Today
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => setPeriodOffset((prev) => Math.max(0, prev - 1))}
              disabled={periodOffset === 0}
              className={`w-7 h-7 flex items-center justify-center rounded-full border border-sky-200 shadow-sm transition ${
                periodOffset === 0
                  ? 'opacity-50 cursor-not-allowed bg-sky-50 text-ink-3'
                  : 'bg-white hover:bg-sky-50 text-ink-3 hover:text-ink'
              }`}
              title="Next period"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Strip - Compact White Tiles */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-white p-3 rounded-2xl border border-white/80 shadow-[0_4px_20px_rgba(31,110,140,0.06)] flex flex-col justify-center items-center text-center">
          <span className="eyebrow block mb-1">
            Days Tracked
          </span>
          <span className="text-[18px] font-semibold text-ink leading-none tabular-nums">
            {gridResult.totalDaysWithData}
          </span>
        </div>
        <div className="bg-white p-3 rounded-2xl border border-white/80 shadow-[0_4px_20px_rgba(31,110,140,0.06)] flex flex-col justify-center items-center text-center">
          <span className="eyebrow block mb-1">
            Avg Risk
          </span>
          <span className="text-[18px] font-semibold text-ink leading-none tabular-nums">
            {gridResult.totalDaysWithData > 0 ? gridResult.averageRiskScore : '-'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-2xl border border-white/80 shadow-[0_4px_20px_rgba(31,110,140,0.06)] flex flex-col justify-center items-center text-center">
          <span className="eyebrow block mb-1">
            Peak Risk
          </span>
          <span className="text-[18px] font-semibold text-ink leading-none tabular-nums">
            {gridResult.totalDaysWithData > 0 ? gridResult.maxRiskScore : '-'}
          </span>
        </div>
      </div>

      {/* Main Calendar Heatmap Matrix */}
      <div
        ref={scrollContainerRef}
        className="w-full overflow-x-auto pb-3 scrollbar-thin select-none"
        role="region"
      >
        <div className="inline-flex flex-col gap-1 min-w-max">
          {/* Month Labels Header Row */}
          <div className="flex text-[10px] font-semibold text-ink-2 mb-1 pl-8">
            {gridResult.weeks.map((week, wIdx) => (
              <div
                key={`m-label-${wIdx}`}
                className="w-3.5 sm:w-4 text-center shrink-0"
              >
                {week.monthLabel ? (
                  <span className="text-[11px] text-brand-600 font-bold tracking-wider -translate-x-1 block whitespace-nowrap">
                    {week.monthLabel}
                  </span>
                ) : null}
              </div>
            ))}
          </div>

          {/* 7 Rows for Weekdays */}
          <div className="flex flex-col gap-1" role="grid">
            {WEEKDAY_LABELS.map((dayLabel, dayIndex) => (
              <div
                key={`weekday-${dayLabel}`}
                className="flex items-center gap-1.5"
                role="row"
              >
                {/* Weekday Label */}
                <span className="w-6 text-[10px] font-semibold text-ink-3 text-left shrink-0">
                  {dayIndex % 2 === 0 ? dayLabel : ''}
                </span>

                {/* Cells */}
                <div className="flex gap-1 sm:gap-1.5">
                  {gridResult.weeks.map((week) => {
                    const day = week.days[dayIndex];
                    if (!day) return null;

                    const isSelected = selectedDay?.date === day.date;
                    const hasData = day.hasData;
                    const isFuture = day.isFuture;

                    // Color determination using new 5-color palette
                    let cellBg = '#F1F9FC'; // Very subtle sky for empty
                    let cellBorder = 'transparent';

                    if (isFuture) {
                      cellBg = 'transparent';
                      cellBorder = 'rgba(31,110,140,0.1)';
                    } else if (hasData && day.riskScore !== undefined) {
                      cellBg = getDiscreteRiskColor(day.riskScore);
                      cellBorder = cellBg;
                    }

                    const ariaLabel = isFuture
                      ? `${formatDateLabel(day.date)} (Upcoming)`
                      : hasData
                      ? `${formatDateLabel(day.date)}: Risk Score ${day.riskScore?.toFixed(1)} out of 100`
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
                        className={`w-3 h-3 sm:w-3.5 sm:h-3.5 rounded-[4px] border transition-all duration-200 focus:outline-none ${
                          isFuture
                            ? 'cursor-default opacity-30 border-dashed'
                            : 'cursor-pointer hover:scale-125 hover:z-20 hover:shadow-sm'
                        } ${
                          isSelected
                            ? 'ring-2 ring-brand-500 ring-offset-1 scale-125 z-20'
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

      {/* Floating Hover Tooltip (Light Theme) */}
      {hoveredDay && tooltipPos && (
        <div
          style={{
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y}px`,
            transform: 'translate(-50%, -100%)',
          }}
          className="absolute z-50 pointer-events-none bg-white/95 backdrop-blur-xl border border-white shadow-[0_16px_40px_rgba(31,110,140,0.15)] text-ink rounded-2xl py-2 px-3 text-[11px] min-w-[140px] transition-opacity duration-150"
        >
          <div className="font-bold text-ink-2 mb-1.5 border-b border-sky-200/50 pb-1">
            {formatDateLabel(hoveredDay.date)}
          </div>
          {hoveredDay.hasData ? (
            <div className="space-y-1">
              <div className="flex items-center justify-between gap-3">
                <span className="text-ink-3 uppercase font-semibold text-[10px]">Risk Score</span>
                <span
                  style={{ color: getDiscreteRiskColor(hoveredDay.riskScore ?? 0) }}
                  className="font-bold tabular-nums text-[12px]"
                >
                  {hoveredDay.riskScore?.toFixed(1)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3 text-[10px]">
                <span className="text-ink-3 font-semibold">Priority</span>
                <span className="font-semibold text-ink">
                  {hoveredDay.riskPriority}
                </span>
              </div>
              {hoveredDay.assessmentsCount && hoveredDay.assessmentsCount > 1 ? (
                <div className="text-[9px] text-ink-3 font-medium pt-1 mt-1 border-t border-sky-200/50">
                  Latest of {hoveredDay.assessmentsCount} daily assessments
                </div>
              ) : null}
            </div>
          ) : (
            <div className="text-[11px] text-ink-3 font-medium">No assessment recorded</div>
          )}
        </div>
      )}

      {/* Selected Day Expanded Detail Card (Light Theme) */}
      {selectedDay && (
        <div className="p-4 bg-white rounded-[20px] shadow-[0_10px_30px_rgba(31,110,140,0.08)] border border-white/80 animate-fade-up">
          <div className="flex items-center justify-between pb-3 border-b border-sky-200/50">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center">
                <CalendarIcon className="w-4 h-4 text-brand-500" />
              </div>
              <span className="text-[13px] font-bold text-ink">
                {formatDateLabel(selectedDay.date)}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setSelectedDay(null)}
              className="w-8 h-8 rounded-full bg-sky-50 hover:bg-sky-100 text-ink-3 hover:text-ink transition flex items-center justify-center"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {selectedDay.hasData ? (
            <div className="pt-3 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="eyebrow block">
                    Calculated Risk
                  </span>
                  <div className="flex items-baseline gap-1 mt-0.5">
                    <span
                      style={{ color: getDiscreteRiskColor(selectedDay.riskScore ?? 0) }}
                      className="text-3xl font-bold tabular-nums"
                    >
                      {selectedDay.riskScore?.toFixed(1)}
                    </span>
                    <span className="text-[12px] text-ink-3 font-medium">/ 100</span>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    style={{
                      backgroundColor: `${getDiscreteRiskColor(selectedDay.riskScore ?? 0)}20`,
                      color: getDiscreteRiskColor(selectedDay.riskScore ?? 0),
                      borderColor: `${getDiscreteRiskColor(selectedDay.riskScore ?? 0)}40`,
                    }}
                    className="inline-block px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border"
                  >
                    {selectedDay.stressLevel} Risk
                  </span>
                  <span className="block text-[11px] text-ink-3 mt-1.5 font-medium">
                    Priority: <strong className="text-ink font-semibold">{selectedDay.riskPriority}</strong>
                  </span>
                </div>
              </div>

              {/* Contributing factors */}
              {selectedDay.keyFactors && selectedDay.keyFactors.length > 0 && (
                <div className="pt-3 border-t border-sky-200/50">
                  <span className="eyebrow block mb-2">
                    Key Factors
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {selectedDay.keyFactors.map((factor, fIdx) => (
                      <span
                        key={fIdx}
                        className="px-3 py-1.5 bg-sky-50 rounded-full border border-sky-200 text-[11px] font-medium text-ink-2"
                      >
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="pt-4 text-center text-[12px] font-medium text-ink-3 pb-2 flex flex-col items-center">
              <Info className="w-5 h-5 mb-2 text-ink-3/50" />
              <span>No assessment was completed on this date.</span>
            </div>
          )}
        </div>
      )}

      {/* Legend Footer */}
      <div className="pt-3 border-t border-sky-200/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div
            className="w-3.5 h-3.5 rounded-[4px] bg-[#F1F9FC]"
          />
          <span className="text-[11px] text-ink-3 font-semibold">
            No Data
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          <span className="text-[11px] text-ink-3 font-semibold">Less Risk</span>
          <div className="flex items-center gap-1">
            {HEATMAP_COLORS.map((color, i) => (
              <div
                key={i}
                style={{ backgroundColor: color }}
                className="w-3.5 h-3.5 rounded-[4px]"
              />
            ))}
          </div>
          <span className="text-[11px] text-ink-3 font-semibold">More Risk</span>
        </div>
      </div>
    </div>
  );
}
