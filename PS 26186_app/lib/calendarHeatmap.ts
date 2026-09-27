import { StressAssessmentOut } from '@/types/api';

export interface CalendarDay {
  date: string; // YYYY-MM-DD
  dateObj: Date;
  dayOfWeek: number; // 0=Mon, 1=Tue, ..., 6=Sun
  dayOfMonth: number;
  month: number; // 0-11
  year: number;
  isFuture: boolean;
  hasData: boolean;
  riskScore?: number;
  stressLevel?: 'Low' | 'Medium' | 'High';
  riskPriority?: 'Routine' | 'Preventive' | 'Priority';
  riskProbability?: number;
  keyFactors?: string[];
  modelVersion?: string;
  assessmentsCount?: number;
  latestAssessment?: StressAssessmentOut;
}

export interface CalendarWeek {
  weekIndex: number;
  days: (CalendarDay | null)[]; // 7 elements (0=Mon to 6=Sun)
  monthLabel?: string; // e.g. "Jan", "Feb" if this week starts a month
}

export interface CalendarGridResult {
  weeks: CalendarWeek[];
  startDate: string;
  endDate: string;
  totalDaysWithData: number;
  averageRiskScore: number;
  maxRiskScore: number;
}

/**
 * Deterministically aggregates multiple assessments on the same calendar day.
 * Rule: The latest assessment on that calendar date (by assessment_timestamp)
 * is selected as the authoritative daily risk state.
 */
export function aggregateDailyAssessments(
  assessments: StressAssessmentOut[]
): Map<string, { latest: StressAssessmentOut; count: number }> {
  const dailyMap = new Map<string, { latest: StressAssessmentOut; count: number }>();

  if (!assessments || assessments.length === 0) {
    return dailyMap;
  }

  // Sort ascending by timestamp so that later entries override earlier ones
  const sorted = [...assessments].sort(
    (a, b) => new Date(a.assessment_timestamp).getTime() - new Date(b.assessment_timestamp).getTime()
  );

  for (const item of sorted) {
    // Extract YYYY-MM-DD using UTC representation to avoid timezone offsets
    const ts = new Date(item.assessment_timestamp);
    const y = ts.getUTCFullYear();
    const m = String(ts.getUTCMonth() + 1).padStart(2, '0');
    const d = String(ts.getUTCDate()).padStart(2, '0');
    const dateKey = `${y}-${m}-${d}`;

    const existing = dailyMap.get(dateKey);
    if (existing) {
      dailyMap.set(dateKey, {
        latest: item,
        count: existing.count + 1,
      });
    } else {
      dailyMap.set(dateKey, {
        latest: item,
        count: 1,
      });
    }
  }

  return dailyMap;
}

/**
 * Mathematically continuous color interpolation across the 0–100 risk score range:
 * Low Risk (0) → Green (rgb(16, 185, 129))
 * Moderate (50) → Yellow (rgb(234, 179, 8))
 * High (100) → Red (rgb(239, 68, 68))
 */
export function getRiskColor(riskScore: number): string {
  const clamped = Math.max(0, Math.min(100, riskScore));
  const t = clamped / 100; // 0.0 to 1.0

  let r: number, g: number, b: number;
  if (t <= 0.5) {
    const ratio = t / 0.5; // 0 to 1
    r = Math.round(16 + ratio * (234 - 16));
    g = Math.round(185 + ratio * (179 - 185));
    b = Math.round(129 + ratio * (8 - 129));
  } else {
    const ratio = (t - 0.5) / 0.5; // 0 to 1
    r = Math.round(234 + ratio * (239 - 234));
    g = Math.round(179 + ratio * (68 - 179));
    b = Math.round(8 + ratio * (68 - 8));
  }

  return `rgb(${r}, ${g}, ${b})`;
}

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

export const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/**
 * Generates a full GitHub-style contribution grid of weeks and days.
 * Ensures:
 * - 7 rows (Mon to Sun)
 * - Number of columns = weeksCount (e.g. 52 for 1 year, 26 for 6 months, 13 for 3 months)
 * - Accurate month labels placed above columns where each month begins
 * - Correct handling of month boundaries, leap years, and future days
 */
export function generateCalendarGrid(
  referenceDate: Date,
  weeksCount: number = 52,
  dailyMap: Map<string, { latest: StressAssessmentOut; count: number }>
): CalendarGridResult {
  const today = new Date();
  today.setHours(23, 59, 59, 999);

  // Set reference to noon UTC to prevent DST transitions
  const ref = new Date(referenceDate);
  ref.setHours(12, 0, 0, 0);

  // Find Sunday of the reference week (ISO day 6: Mon=0, Sun=6)
  const refIsoDay = (ref.getDay() + 6) % 7;
  const daysUntilSunday = 6 - refIsoDay;
  const calEnd = new Date(ref);
  calEnd.setDate(ref.getDate() + daysUntilSunday);
  calEnd.setHours(12, 0, 0, 0);

  // Start date is exactly (weeksCount * 7 - 1) days prior (always a Monday)
  const calStart = new Date(calEnd);
  calStart.setDate(calEnd.getDate() - (weeksCount * 7 - 1));
  calStart.setHours(12, 0, 0, 0);

  const weeks: CalendarWeek[] = [];
  let totalDataDays = 0;
  let scoreSum = 0;
  let maxScore = 0;
  let lastLabeledMonth = -1;

  for (let w = 0; w < weeksCount; w++) {
    const days: (CalendarDay | null)[] = [];
    let weekMonthCandidate: number | null = null;

    for (let dIndex = 0; dIndex < 7; dIndex++) {
      const curDate = new Date(calStart);
      curDate.setDate(calStart.getDate() + w * 7 + dIndex);
      curDate.setHours(12, 0, 0, 0);

      const y = curDate.getFullYear();
      const m = curDate.getMonth();
      const dayOfMonth = curDate.getDate();
      const dateKey = `${y}-${String(m + 1).padStart(2, '0')}-${String(dayOfMonth).padStart(2, '0')}`;

      // Check if this day is the 1st of a month
      if (dayOfMonth === 1) {
        weekMonthCandidate = m;
      }

      const isFuture = curDate.getTime() > today.getTime();
      const entry = !isFuture ? dailyMap.get(dateKey) : undefined;
      const hasData = !!entry;

      let score: number | undefined;
      let level: 'Low' | 'Medium' | 'High' | undefined;
      let priority: 'Routine' | 'Preventive' | 'Priority' | undefined;
      let prob: number | undefined;
      let factors: string[] | undefined;
      let model: string | undefined;

      if (entry) {
        const item = entry.latest;
        score = typeof item.risk_score === 'number' ? item.risk_score : parseFloat(item.risk_score as any) || 0;
        level = item.stress_level;
        priority = item.risk_priority;
        prob = item.risk_probability ?? (score / 100);
        factors = item.key_factors;
        model = item.model_version;

        totalDataDays++;
        scoreSum += score;
        if (score > maxScore) maxScore = score;
      }

      days.push({
        date: dateKey,
        dateObj: curDate,
        dayOfWeek: dIndex,
        dayOfMonth,
        month: m,
        year: y,
        isFuture,
        hasData,
        riskScore: score,
        stressLevel: level,
        riskPriority: priority,
        riskProbability: prob,
        keyFactors: factors,
        modelVersion: model,
        assessmentsCount: entry ? entry.count : 0,
        latestAssessment: entry ? entry.latest : undefined,
      });
    }

    // Determine month label for this week column
    let monthLabel: string | undefined;
    const firstDayOfWeek = days[0]!;
    if (weekMonthCandidate !== null && weekMonthCandidate !== lastLabeledMonth) {
      monthLabel = MONTH_NAMES[weekMonthCandidate];
      lastLabeledMonth = weekMonthCandidate;
    } else if (w === 0) {
      // First column shows the current month
      monthLabel = MONTH_NAMES[firstDayOfWeek.month];
      lastLabeledMonth = firstDayOfWeek.month;
    }

    weeks.push({
      weekIndex: w,
      days,
      monthLabel,
    });
  }

  const startDateStr = weeks[0]?.days[0]?.date || '';
  const lastWeek = weeks[weeks.length - 1];
  const endDateStr = lastWeek?.days[6]?.date || '';

  return {
    weeks,
    startDate: startDateStr,
    endDate: endDateStr,
    totalDaysWithData: totalDataDays,
    averageRiskScore: totalDataDays > 0 ? parseFloat((scoreSum / totalDataDays).toFixed(1)) : 0,
    maxRiskScore: parseFloat(maxScore.toFixed(1)),
  };
}
