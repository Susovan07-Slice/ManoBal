'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/DashboardLayout';
import RiskBadge from '@/components/dashboard/RiskBadge';
import { getPersonnelById } from '@/lib/personnel';
import {
  getPersonnelAssessments,
  runPersonnelAssessment,
  updateRecommendationStatus,
  getPersonnelTrend,
} from '@/lib/assessments';
import {
  PersonnelOut,
  StressAssessmentOut,
  AssessmentOverride,
  LongitudinalTrendResponse,
} from '@/types/api';
import { useAuth } from '@/lib/AuthContext';
import { ROLE_CONFIG } from '@/lib/rbac';
import {
  ArrowLeft,
  Activity,
  Calendar,
  Clock,
  MapPin,
  Shield,
  Briefcase,
  AlertTriangle,
  Play,
  HeartPulse,
  History,
  CheckCircle,
  FileText,
  Sliders,
  X,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';

export default function PersonnelDetailPage() {
  const params = useParams();
  const router = useRouter();
  const personnelId = Number(params.id);
  const { role } = useAuth();
  const config = ROLE_CONFIG[role] || ROLE_CONFIG.officer;

  const [personnel, setPersonnel] = useState<PersonnelOut | null>(null);
  const [assessments, setAssessments] = useState<StressAssessmentOut[]>([]);
  const [trendData, setTrendData] = useState<LongitudinalTrendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [updatingRecId, setUpdatingRecId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showOverrideModal, setShowOverrideModal] = useState(false);

  // Override modal telemetry form state
  const [overrideTelemetry, setOverrideTelemetry] = useState<AssessmentOverride>({
    duty_hours_per_week: undefined,
    night_shifts_per_month: undefined,
    consecutive_duty_days: undefined,
    leave_gap_days: undefined,
    sleep_hours: undefined,
  });

  const loadData = useCallback(async () => {
    if (!personnelId || isNaN(personnelId)) return;
    setLoading(true);
    setError(null);
    try {
      const [pRes, assRes, trendRes] = await Promise.all([
        getPersonnelById(personnelId),
        getPersonnelAssessments(personnelId),
        getPersonnelTrend(personnelId),
      ]);
      setPersonnel(pRes);
      setAssessments(assRes || []);
      setTrendData(trendRes || null);
    } catch (err: any) {
      console.error('Failed to load personnel detail:', err);
      setError(err?.message || 'Unable to retrieve personnel record.');
    } finally {
      setLoading(false);
    }
  }, [personnelId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleTriggerAssessment = async (override?: AssessmentOverride) => {
    setEvaluating(true);
    try {
      await runPersonnelAssessment(personnelId, override);
      setShowOverrideModal(false);
      await loadData();
    } catch (err: any) {
      alert(`Assessment execution failed: ${err?.message || 'Server error'}`);
    } finally {
      setEvaluating(false);
    }
  };

  const handleRecommendationStatus = async (
    recId: number,
    status: 'pending' | 'acknowledged' | 'completed' | 'dismissed'
  ) => {
    setUpdatingRecId(recId);
    try {
      await updateRecommendationStatus(recId, status);
      await loadData();
    } catch (err: any) {
      alert(`Status update failed: ${err?.message || 'Authorization error'}`);
    } finally {
      setUpdatingRecId(null);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="h-[60vh] flex flex-col justify-center items-center space-y-3">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
            Loading Service Dossier...
          </span>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !personnel) {
    return (
      <DashboardLayout>
        <div className="space-y-4">
          <Link
            href="/personnel"
            className="inline-flex items-center text-xs text-textSecondary hover:text-textPrimary"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Personnel Directory
          </Link>
          <div className="p-6 bg-surface border border-[#E8B4B4] rounded-lg text-center">
            <h2 className="text-lg font-bold text-[#C26D6D]">Record Unavailable</h2>
            <p className="text-sm text-textSecondary mt-1">{error || 'Personnel record not found.'}</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const latestAssessment = assessments[0] || null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Navigation & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/personnel"
              className="p-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 rounded text-textSecondary hover:text-textPrimary transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-textPrimary">{personnel.name}</h1>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-surfaceHighlight text-accent font-semibold">
                  {personnel.personnel_code}
                </span>
              </div>
              <p className="text-xs text-textSecondary font-mono mt-0.5">
                {personnel.job_role} • {personnel.department} • Station: {personnel.location}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowOverrideModal(true)}
              className="flex items-center space-x-1.5 px-3 py-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded text-xs font-medium transition-colors border border-surfaceHighlight"
            >
              <Sliders className="w-3.5 h-3.5 text-accent" />
              <span>Simulate Telemetry</span>
            </button>
            <button
              onClick={() => handleTriggerAssessment()}
              disabled={evaluating}
              className="flex items-center space-x-2 px-4 py-2 bg-accent hover:bg-accent/80 text-white rounded text-xs font-semibold tracking-wider uppercase transition-colors disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
              <span>{evaluating ? 'Evaluating ML Model...' : 'Run Assessment'}</span>
            </button>
          </div>
        </div>

        {/* Top Info Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Personnel Service Profile */}
          <div className="bg-surface p-5 border-military flex flex-col justify-between">
            <div>
              <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary mb-4 flex items-center space-x-2">
                <Briefcase className="w-4 h-4 text-accent" />
                <span>Operational Service Profile</span>
              </h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1 border-b border-surfaceHighlight/50">
                  <span className="text-textSecondary">Age & Gender</span>
                  <span className="text-textPrimary font-medium">{personnel.age} yrs • {personnel.gender}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-surfaceHighlight/50">
                  <span className="text-textSecondary">Service Experience</span>
                  <span className="text-textPrimary font-mono font-medium">{personnel.experience_years} years</span>
                </div>
                <div className="flex justify-between py-1 border-b border-surfaceHighlight/50">
                  <span className="text-textSecondary">Active Deployments</span>
                  <span className="text-textPrimary font-mono font-medium">{personnel.deployment_days} days / yr</span>
                </div>
                <div className="flex justify-between py-1 border-b border-surfaceHighlight/50">
                  <span className="text-textSecondary">Remote Posting</span>
                  <span className="text-textPrimary font-mono font-medium">{personnel.remote_posting}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-textSecondary">Operational Exposure</span>
                  <span className={`font-mono font-medium ${
                    personnel.operational_exposure === 'High' ? 'text-[#C26D6D]' :
                    personnel.operational_exposure === 'Medium' ? 'text-[#D99B5C]' : 'text-[#7BA083]'
                  }`}>
                    {personnel.operational_exposure}
                  </span>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-surfaceHighlight text-[10px] text-textSecondary font-mono">
              Enlisted: {new Date(personnel.created_at).toLocaleDateString()}
            </div>
          </div>

          {/* Operational Fatigue & Duty Load */}
          <div className="bg-surface p-5 border-military flex flex-col justify-between">
            <div>
              <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary mb-4 flex items-center space-x-2">
                <Clock className="w-4 h-4 text-accent" />
                <span>Duty Roster & Rest Telemetry</span>
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                  <span className="text-textSecondary text-[11px] block">Weekly Duty</span>
                  <span className="text-lg font-bold font-mono text-textPrimary">{personnel.duty_hours_per_week}h</span>
                  <span className="text-[10px] text-textSecondary block">Standard: 40-48h</span>
                </div>
                <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                  <span className="text-textSecondary text-[11px] block">Consecutive Duty</span>
                  <span className="text-lg font-bold font-mono text-textPrimary">{personnel.consecutive_duty_days}d</span>
                  <span className="text-[10px] text-textSecondary block">Without stand-down</span>
                </div>
                <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                  <span className="text-textSecondary text-[11px] block">Night Shifts</span>
                  <span className="text-lg font-bold font-mono text-textPrimary">{personnel.night_shifts_per_month}</span>
                  <span className="text-[10px] text-textSecondary block">Past 30 days</span>
                </div>
                <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                  <span className="text-textSecondary text-[11px] block">Leave Gap</span>
                  <span className="text-lg font-bold font-mono text-textPrimary">{personnel.leave_gap_days}d</span>
                  <span className="text-[10px] text-textSecondary block">Since last leave</span>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-surfaceHighlight text-[10px] text-textSecondary font-mono">
              Transfer Count: {personnel.transfer_frequency} • Training Load: {personnel.training_load}/10
            </div>
          </div>

          {/* Latest ML Assessment Card */}
          <div className="bg-surface p-5 border-military flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-accent" />
                  <span>Current AI Assessment</span>
                </h3>
                {latestAssessment && <RiskBadge level={latestAssessment.stress_level} />}
              </div>

              {latestAssessment ? (
                <div className="space-y-3">
                  <div className="flex items-baseline space-x-3">
                    <span className="text-3xl font-extrabold font-mono text-textPrimary">
                      {latestAssessment.risk_score}
                    </span>
                    <span className="text-xs text-textSecondary font-mono">/ 100 Risk Index</span>
                    <span className={`text-xs uppercase font-mono font-bold px-2 py-0.5 rounded ml-auto ${
                      latestAssessment.risk_priority === 'Priority'
                        ? 'bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]'
                        : latestAssessment.risk_priority === 'Preventive'
                        ? 'bg-[#FDF6EE] text-[#9A622A] border border-[#EACDAE]'
                        : 'bg-[#EEF6F2] text-[#3F6649] border border-[#BACFC2]'
                    }`}>
                      {latestAssessment.risk_priority}
                    </span>
                  </div>

                  {/* Confidence & Trend */}
                  <div className="grid grid-cols-2 gap-2 text-xs py-1">
                    <div className="p-1.5 bg-surfaceHighlight/40 rounded flex items-center justify-between">
                      <span className="text-[11px] text-textSecondary">Confidence:</span>
                      <span className="font-mono font-semibold text-textPrimary">
                        {latestAssessment.confidence || 'High'}
                      </span>
                    </div>
                    <div className="p-1.5 bg-surfaceHighlight/40 rounded flex items-center justify-between">
                      <span className="text-[11px] text-textSecondary">Trend:</span>
                      <span className={`font-mono font-semibold ${
                        latestAssessment.risk_trend === 'Worsening'
                          ? 'text-[#C26D6D]'
                          : latestAssessment.risk_trend === 'Improving'
                          ? 'text-[#7BA083]'
                          : 'text-textPrimary'
                      }`}>
                        {latestAssessment.risk_trend || 'Stable'}
                      </span>
                    </div>
                  </div>

                  {/* Probability Breakdown */}
                  <div className="space-y-1.5 pt-2">
                    <div className="text-[11px] text-textSecondary font-semibold uppercase tracking-wider">
                      Model Class Probabilities:
                    </div>

                    <div className="grid grid-cols-3 gap-1.5 text-center text-xs font-mono">
                      <div className="p-1.5 bg-surfaceHighlight/50 rounded">
                        <span className="text-[10px] text-textSecondary block">Low</span>
                        <span className="text-[#7BA083] font-bold">
                          {(latestAssessment.low_probability * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="p-1.5 bg-surfaceHighlight/50 rounded">
                        <span className="text-[10px] text-textSecondary block">Medium</span>
                        <span className="text-[#D99B5C] font-bold">
                          {(latestAssessment.medium_probability * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="p-1.5 bg-surfaceHighlight/50 rounded">
                        <span className="text-[10px] text-textSecondary block">High</span>
                        <span className="text-[#C26D6D] font-bold">
                          {(latestAssessment.high_probability * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-textSecondary">
                  No stress assessment recorded for this personnel.
                </div>
              )}
            </div>

            {latestAssessment && (
              <div className="mt-4 pt-3 border-t border-surfaceHighlight text-[10px] font-mono text-textSecondary">
                Model: {latestAssessment.model_version} • Evaluated: {new Date(latestAssessment.assessment_timestamp).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>

        {/* Longitudinal Welfare Intelligence Section */}
        {trendData && trendData.history.data_sufficiency !== 'INSUFFICIENT_DATA' && (
          <div className="bg-surface p-5 border-military">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary flex items-center space-x-2">
                <Activity className="w-4 h-4 text-accent" />
                <span>Longitudinal Welfare Trend Intelligence</span>
              </h3>
              <span className="text-[10px] font-mono text-textSecondary bg-surfaceHighlight px-2 py-0.5 rounded">
                Welfare Monitoring Signal
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              {/* Trend Direction */}
              <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                <span className="text-textSecondary text-[11px] block mb-1">Trend Direction</span>
                <div className="flex items-center space-x-2">
                  {trendData.trend.direction === 'WORSENING' ? (
                    <TrendingUp className="w-5 h-5 text-[#C26D6D]" />
                  ) : trendData.trend.direction === 'IMPROVING' ? (
                    <TrendingDown className="w-5 h-5 text-[#7BA083]" />
                  ) : (
                    <Minus className="w-5 h-5 text-textPrimary" />
                  )}
                  <span className={`text-sm font-bold font-mono ${
                    trendData.trend.direction === 'WORSENING' ? 'text-[#C26D6D]' :
                    trendData.trend.direction === 'IMPROVING' ? 'text-[#7BA083]' : 'text-textPrimary'
                  }`}>
                    {trendData.trend.direction}
                  </span>
                </div>
                <span className="text-[10px] text-textSecondary block mt-1">
                  Change: {trendData.trend.score_change! > 0 ? '+' : ''}{trendData.trend.score_change} pts
                </span>
              </div>

              {/* Persistence */}
              <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                <span className="text-textSecondary text-[11px] block mb-1">Risk Persistence</span>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-bold font-mono ${trendData.history.persistent_elevated_risk ? 'text-[#C26D6D]' : 'text-[#7BA083]'}`}>
                    {trendData.history.persistent_elevated_risk ? 'SUSTAINED ELEVATED' : 'NOT SUSTAINED'}
                  </span>
                </div>
                <span className="text-[10px] text-textSecondary block mt-1">
                  {trendData.history.consecutive_elevated_assessments} consecutive elevated assessments
                </span>
              </div>

              {/* Baseline Deviation */}
              <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                <span className="text-textSecondary text-[11px] block mb-1">Personal Baseline</span>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-bold font-mono ${
                    (trendData.baseline.current_deviation || 0) > 5 ? 'text-[#C26D6D]' :
                    (trendData.baseline.current_deviation || 0) < -5 ? 'text-[#7BA083]' : 'text-textPrimary'
                  }`}>
                    {(trendData.baseline.current_deviation || 0) > 0 ? '+' : ''}{trendData.baseline.current_deviation} pts
                  </span>
                </div>
                <span className="text-[10px] text-textSecondary block mt-1">
                  Historical Mean: {trendData.baseline.historical_mean}
                </span>
              </div>

              {/* Acceleration */}
              <div className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
                <span className="text-textSecondary text-[11px] block mb-1">Risk Acceleration</span>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-bold font-mono ${
                    trendData.trend.acceleration === 'INCREASING' ? 'text-[#C26D6D]' :
                    trendData.trend.acceleration === 'DECREASING' ? 'text-[#7BA083]' : 'text-textPrimary'
                  }`}>
                    {trendData.trend.acceleration}
                  </span>
                </div>
                <span className="text-[10px] text-textSecondary block mt-1">
                  Recent trajectory vs older history
                </span>
              </div>
            </div>

            {/* Repeated Factors */}
            {trendData.repeated_factors && trendData.repeated_factors.length > 0 && (
              <div className="mt-4">
                <span className="text-textSecondary text-[11px] font-semibold uppercase tracking-wider block mb-2">
                  Repeated Historical Factors
                </span>
                <div className="flex flex-wrap gap-2">
                  {trendData.repeated_factors.map((rf, idx) => (
                    <div key={idx} className={`px-2 py-1 text-[10px] font-mono rounded border ${
                      rf.type === 'risk' ? 'bg-[#FAF0F0] text-[#964747] border-[#E8B4B4]' : 'bg-[#EEF6F2] text-[#3F6649] border-[#BACFC2]'
                    }`}>
                      {rf.factor} ({rf.frequency}/{rf.total_assessments})
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <p className="text-[10px] text-textSecondary italic mt-3 text-right">
              {trendData.disclaimer}
            </p>
          </div>
        )}

        {/* Contributing Factors & Recommendations Section */}
        {latestAssessment && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Key Factors */}
            <div className="bg-surface p-5 border-military">
              <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary mb-1 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-accent" />
                <span>Factors Associated with this Model Prediction</span>
              </h3>
              <p className="text-[11px] text-textSecondary mb-4 italic">
                Identified statistical feature associations. Does not imply operational or clinical causation.
              </p>

              {latestAssessment.key_factors && latestAssessment.key_factors.length > 0 ? (
                <ul className="space-y-2.5">
                  {latestAssessment.key_factors.map((factor, i) => (
                    <li
                      key={i}
                      className="p-3 bg-surfaceHighlight/30 rounded border-l-2 border-accent text-xs text-textPrimary flex items-start space-x-2"
                    >
                      <span className="text-accent font-bold">•</span>
                      <span>{factor}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-textSecondary">No heightened risk factors extracted.</p>
              )}
            </div>

            {/* Welfare Recommendations */}
            <div className="bg-surface p-5 border-military">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary flex items-center space-x-2">
                  <HeartPulse className="w-4 h-4 text-accent" />
                  <span>Actionable Welfare Interventions</span>
                </h3>
                <span className="text-[10px] font-mono text-textSecondary bg-surfaceHighlight px-2 py-0.5 rounded">
                  Non-Punitive Decision Support
                </span>
              </div>

              {latestAssessment.recommendations && latestAssessment.recommendations.length > 0 ? (
                <div className="space-y-3">
                  {latestAssessment.recommendations.map((rec) => (
                    <div
                      key={rec.id}
                      className="p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight text-xs space-y-2"
                    >
                      <div className="flex justify-between items-start">
                        <span className="font-semibold text-accent uppercase tracking-wider text-[10px]">
                          {rec.recommendation_type}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            rec.status === 'pending'
                              ? 'bg-[#FDF6EE] text-[#9A622A]'
                              : rec.status === 'acknowledged'
                              ? 'bg-[#EBF3FB] text-[#2F6196]'
                              : rec.status === 'completed'
                              ? 'bg-[#EEF6F2] text-[#3F6649]'
                              : 'bg-surfaceHighlight text-textSecondary'
                          }`}
                        >
                          {rec.status}
                        </span>
                      </div>

                      <p className="text-textPrimary leading-relaxed">{rec.recommendation_text}</p>

                      {config.canEditStatus && (
                        <div className="pt-2 border-t border-surfaceHighlight/50 flex flex-wrap gap-1.5 justify-end">
                          {rec.status !== 'acknowledged' && rec.status !== 'completed' && (
                            <button
                              disabled={updatingRecId === rec.id}
                              onClick={() => handleRecommendationStatus(rec.id, 'acknowledged')}
                              className="px-2 py-1 bg-[#EBF3FB] hover:bg-[#D7E8F7] text-[10px] text-[#2F6196] rounded font-medium transition-colors"
                            >
                              Acknowledge
                            </button>
                          )}
                          {rec.status !== 'completed' && (
                            <button
                              disabled={updatingRecId === rec.id}
                              onClick={() => handleRecommendationStatus(rec.id, 'completed')}
                              className="px-2 py-1 bg-[#EEF6F2] hover:bg-[#DCEAE0] text-[10px] text-[#3F6649] rounded font-medium border border-[#BACFC2] transition-colors"
                            >
                              Mark Completed
                            </button>
                          )}
                          {rec.status !== 'dismissed' && rec.status !== 'completed' && (
                            <button
                              disabled={updatingRecId === rec.id}
                              onClick={() => handleRecommendationStatus(rec.id, 'dismissed')}
                              className="px-2 py-1 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-[10px] text-textSecondary rounded font-medium transition-colors"
                            >
                              Dismiss
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-textSecondary">No welfare recommendations generated for this tier.</p>
              )}
            </div>
          </div>
        )}

        {/* Assessment History Timeline */}
        <div className="bg-surface p-5 border-military">
          <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary mb-4 flex items-center space-x-2">
            <History className="w-4 h-4 text-accent" />
            <span>Chronological Stress Assessment History</span>
          </h3>

          {assessments.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surfaceHighlight/40 text-textSecondary uppercase tracking-widest text-[10px] border-b border-surfaceHighlight">
                  <tr>
                    <th className="px-3 py-2 font-medium">Timestamp</th>
                    <th className="px-3 py-2 font-medium">Stress Tier</th>
                    <th className="px-3 py-2 font-medium">Risk Score</th>
                    <th className="px-3 py-2 font-medium">Welfare Priority</th>
                    <th className="px-3 py-2 font-medium">Top Association Factor</th>
                    <th className="px-3 py-2 font-medium">Recommendations</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surfaceHighlight">
                  {assessments.map((a) => (
                    <tr key={a.id} className="hover:bg-surfaceHighlight/20">
                      <td className="px-3 py-2 font-mono text-textSecondary">
                        {new Date(a.assessment_timestamp).toLocaleString()}
                      </td>
                      <td className="px-3 py-2">
                        <RiskBadge level={a.stress_level} />
                      </td>
                      <td className="px-3 py-2 font-mono font-bold text-textPrimary">
                        {a.risk_score}
                      </td>
                      <td className="px-3 py-2 font-mono font-semibold text-accent">
                        {a.risk_priority}
                      </td>
                      <td className="px-3 py-2 text-textSecondary max-w-xs truncate">
                        {a.key_factors && a.key_factors[0] ? a.key_factors[0] : '-'}
                      </td>
                      <td className="px-3 py-2 font-mono text-textSecondary">
                        {a.recommendations?.length || 0} items
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-textSecondary">No past assessments found.</p>
          )}
        </div>
      </div>

      {/* Override Telemetry Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-surfaceHighlight max-w-md w-full rounded-lg p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-surfaceHighlight pb-3">
              <h3 className="text-sm font-semibold text-textPrimary uppercase tracking-wider">
                Simulate Personnel Telemetry
              </h3>
              <button
                onClick={() => setShowOverrideModal(false)}
                className="text-textSecondary hover:text-textPrimary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-textSecondary">
              Override operational metrics for what-if scenario testing without altering permanent records.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-textSecondary font-semibold mb-1">
                  Weekly Duty Hours (0-120)
                </label>
                <input
                  type="number"
                  placeholder={String(personnel.duty_hours_per_week)}
                  value={overrideTelemetry.duty_hours_per_week ?? ''}
                  onChange={(e) =>
                    setOverrideTelemetry({
                      ...overrideTelemetry,
                      duty_hours_per_week: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight p-2 rounded text-textPrimary outline-none focus:border-accent font-mono"
                />
              </div>

              <div>
                <label className="block text-textSecondary font-semibold mb-1">
                  Night Shifts Past Month (0-31)
                </label>
                <input
                  type="number"
                  placeholder={String(personnel.night_shifts_per_month)}
                  value={overrideTelemetry.night_shifts_per_month ?? ''}
                  onChange={(e) =>
                    setOverrideTelemetry({
                      ...overrideTelemetry,
                      night_shifts_per_month: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight p-2 rounded text-textPrimary outline-none focus:border-accent font-mono"
                />
              </div>

              <div>
                <label className="block text-textSecondary font-semibold mb-1">
                  Consecutive Duty Days (0-60)
                </label>
                <input
                  type="number"
                  placeholder={String(personnel.consecutive_duty_days)}
                  value={overrideTelemetry.consecutive_duty_days ?? ''}
                  onChange={(e) =>
                    setOverrideTelemetry({
                      ...overrideTelemetry,
                      consecutive_duty_days: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight p-2 rounded text-textPrimary outline-none focus:border-accent font-mono"
                />
              </div>

              <div>
                <label className="block text-textSecondary font-semibold mb-1">
                  Days Since Last Leave
                </label>
                <input
                  type="number"
                  placeholder={String(personnel.leave_gap_days)}
                  value={overrideTelemetry.leave_gap_days ?? ''}
                  onChange={(e) =>
                    setOverrideTelemetry({
                      ...overrideTelemetry,
                      leave_gap_days: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight p-2 rounded text-textPrimary outline-none focus:border-accent font-mono"
                />
              </div>

              <div>
                <label className="block text-textSecondary font-semibold mb-1">
                  Average Daily Sleep Hours (0-24)
                </label>
                <input
                  type="number"
                  step="0.5"
                  placeholder="e.g. 5.0"
                  value={overrideTelemetry.sleep_hours ?? ''}
                  onChange={(e) =>
                    setOverrideTelemetry({
                      ...overrideTelemetry,
                      sleep_hours: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full bg-surfaceHighlight border border-surfaceHighlight p-2 rounded text-textPrimary outline-none focus:border-accent font-mono"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-surfaceHighlight">
              <button
                onClick={() => setShowOverrideModal(false)}
                className="px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-xs text-textSecondary rounded font-medium"
              >
                Cancel
              </button>
              <button
                onClick={() => handleTriggerAssessment(overrideTelemetry)}
                disabled={evaluating}
                className="px-4 py-1.5 bg-accent hover:bg-accent/80 text-xs font-semibold text-white rounded transition-colors"
              >
                Run What-If Inference
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
