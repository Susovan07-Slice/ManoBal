import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

function parseUtcDate(dateStr) {
  if (!dateStr) return null;
  let s = String(dateStr).trim();
  if (!s) return null;
  if (!s.endsWith('Z') && !/[+-]\d{2}(:\d{2})?$/.test(s)) {
    s = s.replace(' ', 'T') + 'Z';
  }
  const d = new Date(s);
  return isNaN(d.getTime()) ? new Date(dateStr) : d;
}

function formatAssessmentCountdown(scheduleStatus, nowMs = Date.now()) {
  if (!scheduleStatus) return 'Now';
  if (!scheduleStatus.has_assessment || scheduleStatus.assessment_due) {
    return 'Due now';
  }

  if (scheduleStatus.next_assessment_due_at) {
    const dueTime = parseUtcDate(scheduleStatus.next_assessment_due_at)?.getTime();
    if (dueTime) {
      const diffMs = dueTime - nowMs;
      if (diffMs <= 0) return 'Due now';

      const totalMinutes = Math.floor(diffMs / 60000);
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;

      if (hours > 0 && minutes > 0) return `${hours}h ${minutes}m remaining`;
      if (hours > 0) return `${hours}h remaining`;
      if (minutes > 0) return `${minutes}m remaining`;
      return 'Under 1m remaining';
    }
  }

  if (scheduleStatus.hours_since_last_assessment != null) {
    const remainingHours = Math.max(0, 24 - scheduleStatus.hours_since_last_assessment);
    if (remainingHours <= 0) return 'Due now';

    const totalMinutes = Math.round(remainingHours * 60);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    if (hours > 0 && minutes > 0) return `${hours}h ${minutes}m remaining`;
    if (hours > 0) return `${hours}h remaining`;
    if (minutes > 0) return `${minutes}m remaining`;
    return 'Under 1m remaining';
  }

  return 'Due now';
}

describe('Assessment Timer & Timezone Utils', () => {
  it('1. parseUtcDate parses naive SQLite string as UTC', () => {
    const d = parseUtcDate('2026-09-28 16:58:39.025456');
    assert.ok(d instanceof Date);
    assert.strictEqual(d.toISOString(), '2026-09-28T16:58:39.025Z');
  });

  it('2. parseUtcDate parses ISO without Z as UTC', () => {
    const d = parseUtcDate('2026-09-28T16:58:39.025456');
    assert.ok(d instanceof Date);
    assert.strictEqual(d.toISOString(), '2026-09-28T16:58:39.025Z');
  });

  it('3. parseUtcDate preserves timestamps that already have Z', () => {
    const d = parseUtcDate('2026-09-28T16:58:39.025456Z');
    assert.ok(d instanceof Date);
    assert.strictEqual(d.toISOString(), '2026-09-28T16:58:39.025Z');
  });

  it('4. formatAssessmentCountdown eliminates raw decimal hours (e.g. 22.64h)', () => {
    const status = {
      has_assessment: true,
      assessment_due: false,
      hours_since_last_assessment: 1.36,
      next_assessment_due_at: null,
    };
    // 24 - 1.36 = 22.64h = 22h 38m
    const formatted = formatAssessmentCountdown(status);
    assert.strictEqual(formatted, '22h 38m remaining');
    assert.ok(!formatted.includes('.'), 'Countdown must not contain unformatted decimal points');
  });

  it('5. formatAssessmentCountdown handles exactly 0 minutes (round hours)', () => {
    const status = {
      has_assessment: true,
      assessment_due: false,
      hours_since_last_assessment: 4.0,
      next_assessment_due_at: null,
    };
    const formatted = formatAssessmentCountdown(status);
    assert.strictEqual(formatted, '20h remaining');
  });

  it('6. formatAssessmentCountdown handles under 1 hour remaining', () => {
    const status = {
      has_assessment: true,
      assessment_due: false,
      hours_since_last_assessment: 23.25,
      next_assessment_due_at: null,
    };
    const formatted = formatAssessmentCountdown(status);
    assert.strictEqual(formatted, '45m remaining');
  });

  it('7. formatAssessmentCountdown displays "Due now" when assessment is due', () => {
    const statusDue = {
      has_assessment: true,
      assessment_due: true,
      hours_since_last_assessment: 24.5,
      next_assessment_due_at: null,
    };
    assert.strictEqual(formatAssessmentCountdown(statusDue), 'Due now');

    const statusInitial = {
      has_assessment: false,
      assessment_due: true,
      hours_since_last_assessment: null,
      next_assessment_due_at: null,
    };
    assert.strictEqual(formatAssessmentCountdown(statusInitial), 'Due now');
  });

  it('8. formatAssessmentCountdown calculates remaining time from next_assessment_due_at against nowMs', () => {
    const baseNow = new Date('2026-09-28T18:00:00Z').getTime();
    const status = {
      has_assessment: true,
      assessment_due: false,
      hours_since_last_assessment: 2.5,
      next_assessment_due_at: '2026-09-29T15:30:00Z', // 21h 30m in future
    };
    const formatted = formatAssessmentCountdown(status, baseNow);
    assert.strictEqual(formatted, '21h 30m remaining');
  });

  it('9. formatAssessmentCountdown returns "Due now" when next_assessment_due_at is in the past', () => {
    const baseNow = new Date('2026-09-29T16:00:00Z').getTime();
    const status = {
      has_assessment: true,
      assessment_due: false,
      hours_since_last_assessment: 25.0,
      next_assessment_due_at: '2026-09-29T15:30:00Z', // 30m in past
    };
    const formatted = formatAssessmentCountdown(status, baseNow);
    assert.strictEqual(formatted, 'Due now');
  });
});
