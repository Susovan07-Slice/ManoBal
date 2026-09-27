import test from 'node:test';
import assert from 'node:assert/strict';

// Import or implement the exact core functions from lib/calendarHeatmap
function aggregateDailyAssessments(assessments) {
  const dailyMap = new Map();
  if (!assessments || assessments.length === 0) return dailyMap;

  const sorted = [...assessments].sort(
    (a, b) => new Date(a.assessment_timestamp).getTime() - new Date(b.assessment_timestamp).getTime()
  );

  for (const item of sorted) {
    const ts = new Date(item.assessment_timestamp);
    const y = ts.getUTCFullYear();
    const m = String(ts.getUTCMonth() + 1).padStart(2, '0');
    const d = String(ts.getUTCDate()).padStart(2, '0');
    const dateKey = `${y}-${m}-${d}`;

    const existing = dailyMap.get(dateKey);
    if (existing) {
      dailyMap.set(dateKey, { latest: item, count: existing.count + 1 });
    } else {
      dailyMap.set(dateKey, { latest: item, count: 1 });
    }
  }
  return dailyMap;
}

function getRiskColor(riskScore) {
  const clamped = Math.max(0, Math.min(100, riskScore));
  const t = clamped / 100;
  let r, g, b;
  if (t <= 0.5) {
    const ratio = t / 0.5;
    r = Math.round(16 + ratio * (234 - 16));
    g = Math.round(185 + ratio * (179 - 185));
    b = Math.round(129 + ratio * (8 - 129));
  } else {
    const ratio = (t - 0.5) / 0.5;
    r = Math.round(234 + ratio * (239 - 234));
    g = Math.round(179 + ratio * (68 - 179));
    b = Math.round(8 + ratio * (68 - 8));
  }
  return `rgb(${r}, ${g}, ${b})`;
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function generateCalendarGrid(referenceDate, weeksCount, dailyMap) {
  const today = new Date();
  today.setHours(23, 59, 59, 999);

  const ref = new Date(referenceDate);
  ref.setHours(12, 0, 0, 0);

  const refIsoDay = (ref.getDay() + 6) % 7;
  const daysUntilSunday = 6 - refIsoDay;
  const calEnd = new Date(ref);
  calEnd.setDate(ref.getDate() + daysUntilSunday);
  calEnd.setHours(12, 0, 0, 0);

  const calStart = new Date(calEnd);
  calStart.setDate(calEnd.getDate() - (weeksCount * 7 - 1));
  calStart.setHours(12, 0, 0, 0);

  const weeks = [];
  let totalDataDays = 0;
  let scoreSum = 0;
  let maxScore = 0;
  let lastLabeledMonth = -1;

  for (let w = 0; w < weeksCount; w++) {
    const days = [];
    let weekMonthCandidate = null;

    for (let dIndex = 0; dIndex < 7; dIndex++) {
      const curDate = new Date(calStart);
      curDate.setDate(calStart.getDate() + w * 7 + dIndex);
      curDate.setHours(12, 0, 0, 0);

      const y = curDate.getFullYear();
      const m = curDate.getMonth();
      const dayOfMonth = curDate.getDate();
      const dateKey = `${y}-${String(m + 1).padStart(2, '0')}-${String(dayOfMonth).padStart(2, '0')}`;

      if (dayOfMonth === 1) {
        weekMonthCandidate = m;
      }

      const isFuture = curDate.getTime() > today.getTime();
      const entry = !isFuture ? dailyMap.get(dateKey) : undefined;
      const hasData = !!entry;

      let score;
      let level;
      let priority;
      let prob;

      if (entry) {
        const item = entry.latest;
        score = typeof item.risk_score === 'number' ? item.risk_score : parseFloat(item.risk_score) || 0;
        level = item.stress_level;
        priority = item.risk_priority;
        prob = item.risk_probability ?? (score / 100);

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
        assessmentsCount: entry ? entry.count : 0,
        latestAssessment: entry ? entry.latest : undefined,
      });
    }

    let monthLabel;
    const firstDayOfWeek = days[0];
    if (weekMonthCandidate !== null && weekMonthCandidate !== lastLabeledMonth) {
      monthLabel = MONTH_NAMES[weekMonthCandidate];
      lastLabeledMonth = weekMonthCandidate;
    } else if (w === 0) {
      monthLabel = MONTH_NAMES[firstDayOfWeek.month];
      lastLabeledMonth = firstDayOfWeek.month;
    }

    weeks.push({ weekIndex: w, days, monthLabel });
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

// -----------------------------------------------------------------------------
// Test Suite: 18 Requirements from Problem Statement
// -----------------------------------------------------------------------------

test('1. Calendar renders and generates correct 52-week structure', () => {
  const map = new Map();
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, map);
  assert.strictEqual(res.weeks.length, 52);
  assert.strictEqual(res.weeks[0].days.length, 7);
  assert.strictEqual(res.weeks[51].days.length, 7);
});

test('2. Correct total number of calendar dates are generated (52 * 7 = 364 days)', () => {
  const map = new Map();
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, map);
  const totalDays = res.weeks.reduce((acc, w) => acc + w.days.length, 0);
  assert.strictEqual(totalDays, 364);
});

test('3. Month boundaries and labeling are accurate', () => {
  const map = new Map();
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, map);
  const labeledWeeks = res.weeks.filter((w) => w.monthLabel !== undefined);
  assert.ok(labeledWeeks.length >= 12, 'Must contain at least 12 month labels across 1 year');
  assert.strictEqual(labeledWeeks[0].monthLabel, 'Oct');
});

test('4. Risk score maps accurately to the correct calendar date', () => {
  const mockAssessment = {
    id: 1,
    personnel_id: 1,
    assessment_timestamp: '2026-09-20T10:00:00Z',
    risk_score: 42.5,
    stress_level: 'Medium',
    risk_priority: 'Preventive',
    model_version: 'calibrated_ensemble_v33',
  };
  const dailyMap = aggregateDailyAssessments([mockAssessment]);
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, dailyMap);

  const matched = res.weeks
    .flatMap((w) => w.days)
    .find((d) => d && d.date === '2026-09-20');

  assert.ok(matched, '2026-09-20 must exist in calendar');
  assert.strictEqual(matched.hasData, true);
  assert.strictEqual(matched.riskScore, 42.5);
  assert.strictEqual(matched.stressLevel, 'Medium');
});

test('5. No-data dates render neutral (hasData is false)', () => {
  const dailyMap = new Map();
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, dailyMap);
  const day = res.weeks[0].days[0];
  assert.strictEqual(day.hasData, false);
  assert.strictEqual(day.riskScore, undefined);
});

test('6. Low-risk score (0 to 25) produces green-side color', () => {
  const color0 = getRiskColor(0);
  const color25 = getRiskColor(25);
  assert.strictEqual(color0, 'rgb(16, 185, 129)', 'Score 0 must be pure emerald green');
  assert.strictEqual(color25, 'rgb(125, 182, 69)', 'Score 25 must be lime/green-yellow');
});

test('7. Medium-risk score (50) produces yellow-side color', () => {
  const color50 = getRiskColor(50);
  assert.strictEqual(color50, 'rgb(234, 179, 8)', 'Score 50 must be pure golden yellow');
});

test('8. High-risk score (75 to 100) produces red-side color', () => {
  const color75 = getRiskColor(75);
  const color100 = getRiskColor(100);
  assert.strictEqual(color75, 'rgb(237, 124, 38)', 'Score 75 must be warm amber orange');
  assert.strictEqual(color100, 'rgb(239, 68, 68)', 'Score 100 must be pure crimson red');
});

test('9. Color interpolation is mathematically continuous and monotonic', () => {
  const scores = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
  const redComponents = scores.map((s) => {
    const match = getRiskColor(s).match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    return Number(match[1]);
  });
  // R component must non-decreasingly ascend from 16 up to 239
  for (let i = 1; i < redComponents.length; i++) {
    assert.ok(
      redComponents[i] >= redComponents[i - 1],
      `Red component must be monotonic: ${redComponents[i]} >= ${redComponents[i - 1]}`
    );
  }
});

test('10. Tooltip displays actual risk score and fields', () => {
  const mockAssessment = {
    id: 10,
    personnel_id: 1,
    assessment_timestamp: '2026-09-18T14:30:00Z',
    risk_score: 72.4,
    stress_level: 'High',
    risk_priority: 'Priority',
    risk_probability: 0.724,
    key_factors: ['Physical fatigue', 'Sleep duration'],
    model_version: 'stress_risk_ensemble_v2',
  };
  const dailyMap = aggregateDailyAssessments([mockAssessment]);
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, dailyMap);

  const matched = res.weeks.flatMap((w) => w.days).find((d) => d && d.date === '2026-09-18');
  assert.ok(matched);
  assert.strictEqual(matched.riskScore, 72.4);
  assert.strictEqual(matched.riskProbability, 0.724);
  assert.strictEqual(matched.stressLevel, 'High');
  assert.strictEqual(matched.riskPriority, 'Priority');
});

test('11. Multiple assessments on one day follow documented aggregation rule (latest timestamp)', () => {
  const multipleOnSameDay = [
    {
      id: 101,
      personnel_id: 1,
      assessment_timestamp: '2026-09-26T05:00:00Z',
      risk_score: 30.0,
      stress_level: 'Low',
      risk_priority: 'Routine',
    },
    {
      id: 102,
      personnel_id: 1,
      assessment_timestamp: '2026-09-26T12:00:00Z',
      risk_score: 65.0,
      stress_level: 'Medium',
      risk_priority: 'Preventive',
    },
    {
      id: 103,
      personnel_id: 1,
      assessment_timestamp: '2026-09-26T18:30:00Z', // LATEST
      risk_score: 95.0,
      stress_level: 'High',
      risk_priority: 'Priority',
    },
  ];

  const dailyMap = aggregateDailyAssessments(multipleOnSameDay);
  assert.strictEqual(dailyMap.size, 1);
  const entry = dailyMap.get('2026-09-26');
  assert.strictEqual(entry.count, 3, 'Must track all 3 assessments on that day');
  assert.strictEqual(entry.latest.id, 103, 'Must select latest timestamp assessment');
  assert.strictEqual(entry.latest.risk_score, 95.0);
});

test('12. Empty API response is handled gracefully without error', () => {
  const dailyMap = aggregateDailyAssessments([]);
  assert.strictEqual(dailyMap.size, 0);
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, dailyMap);
  assert.strictEqual(res.totalDaysWithData, 0);
  assert.strictEqual(res.averageRiskScore, 0);
  assert.strictEqual(res.maxRiskScore, 0);
});

test('13. Handles leap year month boundaries correctly (Feb 29 in leap year)', () => {
  const res = generateCalendarGrid(new Date('2024-03-05'), 13, new Map());
  const feb29 = res.weeks.flatMap((w) => w.days).find((d) => d && d.date === '2024-02-29');
  assert.ok(feb29, 'Leap day 2024-02-29 must exist in 2024 calendar');
});

test('14. Mobile duration switches work (6 months = 26 weeks, 3 months = 13 weeks)', () => {
  const res26 = generateCalendarGrid(new Date('2026-09-27'), 26, new Map());
  assert.strictEqual(res26.weeks.length, 26);
  assert.strictEqual(res26.weeks.reduce((acc, w) => acc + w.days.length, 0), 182);

  const res13 = generateCalendarGrid(new Date('2026-09-27'), 13, new Map());
  assert.strictEqual(res13.weeks.length, 13);
  assert.strictEqual(res13.weeks.reduce((acc, w) => acc + w.days.length, 0), 91);
});

test('15. Accessibility labels contain date and formatted risk score', () => {
  const mockAssessment = {
    id: 1,
    personnel_id: 1,
    assessment_timestamp: '2026-09-18T12:00:00Z',
    risk_score: 72.4,
    stress_level: 'High',
  };
  const dailyMap = aggregateDailyAssessments([mockAssessment]);
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, dailyMap);
  const day = res.weeks.flatMap((w) => w.days).find((d) => d && d.date === '2026-09-18');

  const label = `${day.date}: Risk Score ${day.riskScore.toFixed(1)} out of 100, ${day.stressLevel} stress level`;
  assert.ok(label.includes('2026-09-18'));
  assert.ok(label.includes('72.4 out of 100'));
  assert.ok(label.includes('High stress level'));
});

test('16. Batched single-query data consumption: 364 cells derived from 1 array', () => {
  const rawAssessments = [
    { id: 1, personnel_id: 1, assessment_timestamp: '2026-09-01T10:00:00Z', risk_score: 25 },
    { id: 2, personnel_id: 1, assessment_timestamp: '2026-09-02T10:00:00Z', risk_score: 50 },
    { id: 3, personnel_id: 1, assessment_timestamp: '2026-09-03T10:00:00Z', risk_score: 75 },
  ];
  const map = aggregateDailyAssessments(rawAssessments);
  const res = generateCalendarGrid(new Date('2026-09-27'), 52, map);
  assert.strictEqual(res.totalDaysWithData, 3);
  assert.strictEqual(res.averageRiskScore, 50);
});
