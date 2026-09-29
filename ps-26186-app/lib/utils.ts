import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { AssessmentScheduleStatus } from "@/types/api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Safely parse a date string that may or may not include timezone info.
 * Since backend timestamps are stored in UTC (e.g. from SQLite as "YYYY-MM-DD HH:MM:SS"
 * or ISO strings without 'Z'), parsing them directly via new Date(str) in browsers
 * treats them as local time, causing significant timezone skew (e.g., 5.5 hours in IST).
 * This helper normalizes them as UTC unless an explicit offset or 'Z' is already present.
 */
export function parseUtcDate(dateStr: string | null | undefined): Date | null {
  if (!dateStr) return null;
  let s = String(dateStr).trim();
  if (!s) return null;
  // If already ends in Z or has explicit offset like +05:30 or -04:00, parse directly
  if (!s.endsWith("Z") && !/[+-]\d{2}(:\d{2})?$/.test(s)) {
    s = s.replace(" ", "T") + "Z";
  }
  const d = new Date(s);
  return isNaN(d.getTime()) ? new Date(dateStr) : d;
}

/**
 * Formats an assessment timestamp in localized human-readable form (e.g., "Sep 28, 10:28 PM")
 * accurately converted from UTC into the user's local timezone.
 */
export function formatAssessmentDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "None";
  const d = parseUtcDate(dateStr);
  if (!d || isNaN(d.getTime())) return "None";
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Formats the countdown or remaining time until the next assessment is due.
 * Converts raw decimal hours into clean, natural format: e.g. "22h 38m remaining",
 * "45m remaining", or "Due now".
 */
export function formatAssessmentCountdown(
  scheduleStatus: AssessmentScheduleStatus | null | undefined,
  nowMs: number = Date.now()
): string {
  if (!scheduleStatus) return "Now";
  if (!scheduleStatus.has_assessment || scheduleStatus.assessment_due) {
    return "Due now";
  }

  // 1. Preferred: Calculate exact remaining time from next_assessment_due_at
  if (scheduleStatus.next_assessment_due_at) {
    const dueTime = parseUtcDate(scheduleStatus.next_assessment_due_at)?.getTime();
    if (dueTime) {
      const diffMs = dueTime - nowMs;
      if (diffMs <= 0) return "Due now";

      const totalMinutes = Math.floor(diffMs / 60000);
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;

      if (hours > 0 && minutes > 0) return `${hours}h ${minutes}m remaining`;
      if (hours > 0) return `${hours}h remaining`;
      if (minutes > 0) return `${minutes}m remaining`;
      return "Under 1m remaining";
    }
  }

  // 2. Fallback: Convert hours_since_last_assessment decimal into hours and minutes
  if (scheduleStatus.hours_since_last_assessment != null) {
    const remainingHours = Math.max(0, 24 - scheduleStatus.hours_since_last_assessment);
    if (remainingHours <= 0) return "Due now";

    const totalMinutes = Math.round(remainingHours * 60);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    if (hours > 0 && minutes > 0) return `${hours}h ${minutes}m remaining`;
    if (hours > 0) return `${hours}h remaining`;
    if (minutes > 0) return `${minutes}m remaining`;
    return "Under 1m remaining";
  }

  return "Due now";
}
