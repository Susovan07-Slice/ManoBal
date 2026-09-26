"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { HomeScreen } from "@/components/screens/HomeScreen";
import { useAuth } from "@/lib/AuthContext";
import { getAssessmentHistory, getAssessmentScheduleStatus } from "@/lib/assessment";
import { getMyWelfareRequests } from "@/lib/welfare";
import { computePersonalTrend } from "@/lib/trends";
import { PersonalTrend } from "@/types/trends";
import { StressAssessmentOut, AssessmentScheduleStatus, WelfareRequestOut } from "@/types/api";
import { ShieldAlert, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";

export default function HomeRoute() {
  const { user } = useAuth();
  const router = useRouter();

  const [trend, setTrend] = useState<PersonalTrend | null>(null);
  const [latestAssessment, setLatestAssessment] = useState<StressAssessmentOut | null>(null);
  const [scheduleStatus, setScheduleStatus] = useState<AssessmentScheduleStatus | null>(null);
  const [welfareRequests, setWelfareRequests] = useState<WelfareRequestOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const autoRedirectedRef = useRef(false);

  const loadHomeData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (user?.personnel_id) {
        // Fetch server-authoritative 24-hour schedule status, assessment history & welfare requests
        const [statusRes, historyRes, welfareRes] = await Promise.all([
          getAssessmentScheduleStatus(user.personnel_id).catch((err) => {
            console.warn("Could not retrieve schedule status:", err);
            return null;
          }),
          getAssessmentHistory(user.personnel_id).catch((err) => {
            console.warn("Could not retrieve assessment history:", err);
            return [];
          }),
          getMyWelfareRequests().catch((err) => {
            console.warn("Could not retrieve welfare requests:", err);
            return [];
          }),
        ]);

        setScheduleStatus(statusRes);
        setWelfareRequests(welfareRes || []);

        const assessments = historyRes || [];
        if (assessments.length > 0) {
          setLatestAssessment(assessments[0]);
        } else {
          setLatestAssessment(null);
        }

        const computed = computePersonalTrend(assessments);
        setTrend(computed);

        // Server-backed 24-hour assessment rule (Sections 6, 7, 8, 9, 10)
        // Case 1: No previous assessment exists -> assessment_due = true -> auto-open
        // Case 2: Age < 24 hours -> assessment_due = false -> do NOT auto-open
        // Case 3: Age >= 24 hours -> assessment_due = true -> auto-open
        if (statusRes && statusRes.assessment_due && !autoRedirectedRef.current) {
          // Check if user already dismissed or navigated in this session
          const sessionDismissed = sessionStorage.getItem(`assessment_dismissed_${user.personnel_id}`);
          if (!sessionDismissed) {
            autoRedirectedRef.current = true;
            router.push(
              !statusRes.has_assessment
                ? "/assessment?reason=initial"
                : "/assessment?reason=due_24h"
            );
            return;
          }
        }
      } else {
        setLatestAssessment(null);
        setScheduleStatus(null);
        setTrend({
          last7Days: [],
          averageStressIndex: 0,
          averageSleepHours: 0,
          trendDirection: "stable",
        });
      }
    } catch (err: any) {
      console.error("Failed to load home dashboard telemetry:", err);
      setError(err?.message || "Failed to load dashboard data");
      setTrend({
        last7Days: [],
        averageStressIndex: 0,
        averageSleepHours: 0,
        trendDirection: "stable",
      });
    } finally {
      setLoading(false);
    }
  }, [user, router]);

  useEffect(() => {
    loadHomeData();

    const handleWelfareCreated = () => {
      loadHomeData();
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('manobal:welfare_created', handleWelfareCreated);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('manobal:welfare_created', handleWelfareCreated);
      }
    };
  }, [loadHomeData]);

  if (loading) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-mb-text-secondary p-6 text-center">
        <div className="w-8 h-8 border-2 border-mb-accent border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-mb-text-secondary">Synchronizing Health Telemetry...</p>
        <span className="text-xs text-mb-text-muted font-mono mt-1">
          Evaluating 24-hour schedule status & LightGBM history
        </span>
      </div>
    );
  }

  if (error && !trend) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-mb-text-secondary p-6 text-center">
        <p className="text-sm text-mb-text-secondary mb-2">Could not synchronize dashboard telemetry.</p>
        <button
          onClick={loadHomeData}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 text-mb-accent text-xs rounded-lg hover:bg-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 h-full flex flex-col justify-between">
      <div>
        <HomeScreen
          username={user?.username}
          latestAssessment={latestAssessment}
          scheduleStatus={scheduleStatus}
          trend={
            trend || {
              last7Days: [],
              averageStressIndex: 0,
              averageSleepHours: 0,
              trendDirection: "stable",
            }
          }
          welfareRequests={welfareRequests}
          onRefresh={loadHomeData}
        />
      </div>

      {/* Prototype Notice */}
      <div className="mt-6 mb-16 p-3 bg-slate-900/40 border border-slate-800/60 rounded-xl flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-mb-accent/70 shrink-0 mt-0.5" />
        <p className="text-[11px] text-mb-text-secondary leading-relaxed">
          <strong>Prototype Notice:</strong> Synthetically augmented operational demonstration. Stress
          indicators are decision-support metrics and not medical diagnoses.
        </p>
      </div>
    </div>
  );
}


