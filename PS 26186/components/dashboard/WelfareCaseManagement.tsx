'use client';

import React, { useState, useEffect, useCallback, useId } from 'react';
import {
  FolderKanban,
  Search,
  Filter,
  RefreshCw,
  Plus,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileText,
  UserCheck,
  Shield,
  Activity,
  Calendar,
  X,
  ChevronRight,
  Eye,
  Info,
  History,
  Lock,
  RotateCcw,
  Sparkles,
  HeartHandshake,
  Bell,
  Check,
} from 'lucide-react';
import {
  WelfareCaseListItemOut,
  WelfareCaseDetailOut,
  WelfareCaseSummaryStatsResponse,
  CaseStatus,
  CaseType,
  HumanDecision,
  ClosureReason,
  NoteType,
  ReviewType,
  getWelfareCases,
  getWelfareCaseDetail,
  createWelfareCase,
  recordCaseReview,
  addCaseNote,
  closeWelfareCase,
  reopenWelfareCase,
  getCaseSummaryStats,
} from '@/lib/welfareCases';

interface WelfareCaseManagementProps {
  initialPersonnelId?: number | null;
  onCaseOpened?: (caseDetail: WelfareCaseDetailOut) => void;
}

export default function WelfareCaseManagement({
  initialPersonnelId,
  onCaseOpened,
}: WelfareCaseManagementProps) {
  // Data state
  const [cases, setCases] = useState<WelfareCaseListItemOut[]>([]);
  const [stats, setStats] = useState<WelfareCaseSummaryStatsResponse | null>(null);
  const [selectedCase, setSelectedCase] = useState<WelfareCaseDetailOut | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [statsLoading, setStatsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'evidence' | 'reviews' | 'notes' | 'timeline' | 'audits'>('evidence');

  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showReviewModal, setShowReviewModal] = useState<boolean>(false);
  const [showNoteModal, setShowNoteModal] = useState<boolean>(false);
  const [showCloseModal, setShowCloseModal] = useState<boolean>(false);
  const [showReopenModal, setShowReopenModal] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Form states
  const [newCasePersonnelId, setNewCasePersonnelId] = useState<string>(initialPersonnelId ? initialPersonnelId.toString() : '');
  const [newCaseType, setNewCaseType] = useState<CaseType>('CURRENT_RISK_REVIEW');
  const [newCaseTitle, setNewCaseTitle] = useState<string>('');
  const [newCaseSummary, setNewCaseSummary] = useState<string>('');

  const [reviewType, setReviewType] = useState<ReviewType>('INITIAL_TRIAGE');
  const [reviewObservations, setReviewObservations] = useState<string>('');
  const [reviewDecision, setReviewDecision] = useState<HumanDecision>('CONTINUE_MONITORING');
  const [reviewNextStep, setReviewNextStep] = useState<string>('');
  const [reviewWindow, setReviewWindow] = useState<string>('Within 14 days');
  const [reviewStatusTransition, setReviewStatusTransition] = useState<string>('');

  const [noteType, setNoteType] = useState<NoteType>('REVIEW_NOTE');
  const [noteContent, setNoteContent] = useState<string>('');

  const [closureReason, setClosureReason] = useState<ClosureReason>('MONITORING_COMPLETED');
  const [closureNotes, setClosureNotes] = useState<string>('');

  const [reopenReason, setReopenReason] = useState<string>('');

  const searchInputId = useId();

  // Load cases list
  const loadCases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getWelfareCases({
        status: statusFilter,
        case_type: typeFilter,
        search: searchTerm.trim() || undefined,
        personnel_id: initialPersonnelId || undefined,
      });
      setCases(res.cases || []);
    } catch (err: any) {
      console.error('Failed to load welfare cases:', err);
      setError(err?.message || 'Unable to load welfare cases.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, searchTerm, initialPersonnelId]);

  // Load summary stats
  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const res = await getCaseSummaryStats();
      setStats(res);
    } catch (err) {
      console.warn('Could not load case summary stats:', err);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCases();
    loadStats();
  }, [loadCases, loadStats]);

  // Load single case detail
  const handleSelectCase = async (caseId: number) => {
    setActionLoading(true);
    setActionError(null);
    try {
      const detail = await getWelfareCaseDetail(caseId);
      setSelectedCase(detail);
      setActiveTab('evidence');
      if (onCaseOpened) onCaseOpened(detail);
    } catch (err: any) {
      console.error('Failed to load case detail:', err);
      setActionError(err?.message || 'Unable to load case details.');
    } finally {
      setActionLoading(false);
    }
  };

  // Create Case Handler
  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    const pid = parseInt(newCasePersonnelId, 10);
    if (!pid || isNaN(pid)) {
      setActionError('Valid Personnel ID is required.');
      return;
    }
    setActionLoading(true);
    setActionError(null);
    try {
      const detail = await createWelfareCase({
        personnel_id: pid,
        case_type: newCaseType,
        title: newCaseTitle.trim() || undefined,
        summary: newCaseSummary.trim() || undefined,
        trigger_source: 'MANUAL_REVIEW',
      });
      setShowCreateModal(false);
      setNewCaseTitle('');
      setNewCaseSummary('');
      setSelectedCase(detail);
      loadCases();
      loadStats();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to open case.');
    } finally {
      setActionLoading(false);
    }
  };

  // Record Review Handler
  const handleRecordReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;
    if (!reviewObservations.trim()) {
      setActionError('Observations are required for review.');
      return;
    }
    setActionLoading(true);
    setActionError(null);
    try {
      await recordCaseReview(selectedCase.id, {
        review_type: reviewType,
        observations: reviewObservations.trim(),
        decision: reviewDecision,
        next_step: reviewNextStep.trim() || undefined,
        review_window: reviewWindow || undefined,
        new_status: reviewStatusTransition ? (reviewStatusTransition as CaseStatus) : undefined,
      });
      setShowReviewModal(false);
      setReviewObservations('');
      setReviewNextStep('');
      // Reload current case
      const refreshed = await getWelfareCaseDetail(selectedCase.id);
      setSelectedCase(refreshed);
      loadCases();
      loadStats();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to record review.');
    } finally {
      setActionLoading(false);
    }
  };

  // Add Note Handler
  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;
    if (!noteContent.trim()) {
      setActionError('Note content cannot be empty.');
      return;
    }
    setActionLoading(true);
    setActionError(null);
    try {
      await addCaseNote(selectedCase.id, {
        note_type: noteType,
        content: noteContent.trim(),
      });
      setShowNoteModal(false);
      setNoteContent('');
      const refreshed = await getWelfareCaseDetail(selectedCase.id);
      setSelectedCase(refreshed);
      loadCases();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to add note.');
    } finally {
      setActionLoading(false);
    }
  };

  // Close Case Handler
  const handleCloseCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;
    setActionLoading(true);
    setActionError(null);
    try {
      const refreshed = await closeWelfareCase(selectedCase.id, {
        closure_reason: closureReason,
        closure_notes: closureNotes.trim() || undefined,
      });
      setShowCloseModal(false);
      setClosureNotes('');
      setSelectedCase(refreshed);
      loadCases();
      loadStats();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to close case.');
    } finally {
      setActionLoading(false);
    }
  };

  // Reopen Case Handler
  const handleReopenCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;
    if (!reopenReason.trim()) {
      setActionError('Reason is required to reopen a closed case.');
      return;
    }
    setActionLoading(true);
    setActionError(null);
    try {
      const refreshed = await reopenWelfareCase(selectedCase.id, {
        reopen_reason: reopenReason.trim(),
      });
      setShowReopenModal(false);
      setReopenReason('');
      setSelectedCase(refreshed);
      loadCases();
      loadStats();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to reopen case.');
    } finally {
      setActionLoading(false);
    }
  };

  // Helper for Status Badge Styling
  const getStatusBadge = (status: CaseStatus) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-950/60 text-blue-400 border-blue-800/40';
      case 'UNDER_REVIEW':
        return 'bg-amber-950/60 text-amber-400 border-amber-800/40';
      case 'SUPPORT_IN_PROGRESS':
        return 'bg-indigo-950/60 text-indigo-400 border-indigo-800/40';
      case 'AWAITING_FOLLOW_UP':
        return 'bg-purple-950/60 text-purple-400 border-purple-800/40';
      case 'MONITORING':
        return 'bg-cyan-950/60 text-cyan-400 border-cyan-800/40';
      case 'RESOLVED':
        return 'bg-emerald-950/60 text-emerald-400 border-emerald-800/40';
      case 'CLOSED':
        return 'bg-surfaceHighlight text-textSecondary border-border';
      default:
        return 'bg-surfaceHighlight text-textSecondary border-border';
    }
  };

  return (
    <div className="bg-surface border border-border rounded-xl p-5 shadow-sm space-y-6">
      {/* 1. Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border/60 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
              <FolderKanban className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-textPrimary uppercase">
                Welfare Case Management & Human Review
              </h2>
              <p className="text-xs text-textSecondary font-mono mt-0.5">
                Traceable human-review workflow layer operating over authoritative welfare signals
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80 text-white rounded-lg text-xs font-mono font-medium transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Open Welfare Case</span>
          </button>

          <button
            onClick={() => {
              loadCases();
              loadStats();
            }}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-border disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 2. Aggregate Summary Metrics Cards */}
      {stats && !stats.data_suppressed && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
            <div className="flex items-center justify-between text-textSecondary">
              <span className="text-[11px] font-mono uppercase">Total Cases</span>
              <FolderKanban className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-textPrimary font-mono mt-1">
              {stats.total_cases}
            </div>
            <div className="text-[10px] text-textSecondary font-mono mt-0.5">In unit scope</div>
          </div>

          <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
            <div className="flex items-center justify-between text-blue-400">
              <span className="text-[11px] font-mono uppercase">Open</span>
              <Clock className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-blue-400 font-mono mt-1">
              {stats.open_cases}
            </div>
            <div className="text-[10px] text-textSecondary font-mono mt-0.5">Triage pending</div>
          </div>

          <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
            <div className="flex items-center justify-between text-amber-400">
              <span className="text-[11px] font-mono uppercase">Under Review</span>
              <UserCheck className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-amber-400 font-mono mt-1">
              {stats.under_review_cases}
            </div>
            <div className="text-[10px] text-textSecondary font-mono mt-0.5">Active evaluation</div>
          </div>

          <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
            <div className="flex items-center justify-between text-cyan-400">
              <span className="text-[11px] font-mono uppercase">Monitoring</span>
              <Activity className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-cyan-400 font-mono mt-1">
              {stats.monitoring_cases}
            </div>
            <div className="text-[10px] text-textSecondary font-mono mt-0.5">Routine checks</div>
          </div>

          <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
            <div className="flex items-center justify-between text-emerald-400">
              <span className="text-[11px] font-mono uppercase">Resolved</span>
              <CheckCircle2 className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-emerald-400 font-mono mt-1">
              {stats.status_counts?.['RESOLVED'] ?? 0}
            </div>
            <div className="text-[10px] text-textSecondary font-mono mt-0.5">Goals completed</div>
          </div>

          <div className="p-3 bg-surfaceHighlight/40 border border-border/60 rounded-lg">
            <div className="flex items-center justify-between text-textSecondary">
              <span className="text-[11px] font-mono uppercase">Closed</span>
              <Lock className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-textPrimary font-mono mt-1">
              {stats.closed_cases}
            </div>
            <div className="text-[10px] text-textSecondary font-mono mt-0.5">Archived cases</div>
          </div>
        </div>
      )}

      {/* Privacy Suppression Notice if k < 5 */}
      {stats?.data_suppressed && (
        <div className="p-3 bg-amber-950/30 border border-amber-800/50 rounded-lg text-xs text-amber-200 flex items-center space-x-2">
          <Shield className="w-4 h-4 text-amber-400 shrink-0" />
          <span>{stats.suppression_reason}</span>
        </div>
      )}

      {/* 3. Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 bg-surfaceHighlight/20 border border-border/50 rounded-lg">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-textSecondary absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            id={searchInputId}
            name="caseSearch"
            type="text"
            placeholder="Search by Case Ref (WC-...), Personnel Code (PF-...), or Name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-surface border border-border rounded-lg text-xs text-textPrimary placeholder:text-textSecondary/60 focus:outline-none focus:border-accent"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-1.5 text-xs text-textSecondary font-mono">
            <Filter className="w-3.5 h-3.5" />
            <span>Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-surface border border-border rounded px-2 py-1 text-xs text-textPrimary font-mono focus:outline-none focus:border-accent"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="SUPPORT_IN_PROGRESS">Support in Progress</option>
            <option value="AWAITING_FOLLOW_UP">Awaiting Follow-up</option>
            <option value="MONITORING">Monitoring</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>

          <div className="flex items-center space-x-1.5 text-xs text-textSecondary font-mono ml-2">
            <span>Type:</span>
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-surface border border-border rounded px-2 py-1 text-xs text-textPrimary font-mono focus:outline-none focus:border-accent"
          >
            <option value="ALL">All Types</option>
            <option value="CURRENT_RISK_REVIEW">Current Risk Review</option>
            <option value="WORSENING_TREND">Worsening Trend</option>
            <option value="ACTIVE_ALERT">Active Alert</option>
            <option value="ANOMALY_REVIEW">Anomaly Review</option>
            <option value="SUPPORT_FOLLOW_UP">Support Follow-up</option>
            <option value="REPEATED_WELFARE_CONCERN">Repeated Welfare Concern</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-200 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 4. Case List Table (Unranked, Stable Ordering) */}
      <div className="overflow-x-auto border border-border/80 rounded-lg">
        <table className="w-full text-left text-xs">
          <thead className="bg-surfaceHighlight/50 border-b border-border/80 text-[11px] font-mono uppercase text-textSecondary">
            <tr>
              <th className="py-2.5 px-3">Case Reference</th>
              <th className="py-2.5 px-3">Personnel</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Risk (P34)</th>
              <th className="py-2.5 px-3">Trend (P36)</th>
              <th className="py-2.5 px-3">Signals (P37/39/40)</th>
              <th className="py-2.5 px-3">Last Review</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {loading && (
              <tr>
                <td colSpan={8} className="py-8 text-center text-textSecondary font-mono">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-accent" />
                  Loading authorized welfare cases...
                </td>
              </tr>
            )}

            {!loading && cases.length === 0 && (
              <tr>
                <td colSpan={8} className="py-8 text-center text-textSecondary font-mono">
                  No welfare cases found matching the selected filters.
                </td>
              </tr>
            )}

            {!loading &&
              cases.map((c) => {
                const isSelected = selectedCase?.id === c.id;
                const sig = c.signals_summary;
                return (
                  <tr
                    key={c.id}
                    className={`hover:bg-surfaceHighlight/30 transition-colors ${
                      isSelected ? 'bg-indigo-950/20' : ''
                    }`}
                  >
                    <td className="py-2.5 px-3 font-mono font-medium text-textPrimary">
                      <div className="flex items-center space-x-1.5">
                        <FolderKanban className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{c.case_reference}</span>
                      </div>
                      <div className="text-[10px] text-textSecondary font-normal mt-0.5">
                        {c.case_type.replace(/_/g, ' ')}
                      </div>
                    </td>

                    <td className="py-2.5 px-3">
                      <div className="font-semibold text-textPrimary">{c.personnel_name}</div>
                      <div className="text-[10px] text-textSecondary font-mono">
                        {c.personnel_code} • {c.battalion}
                      </div>
                    </td>

                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${getStatusBadge(
                          c.status
                        )}`}
                      >
                        {c.status.replace(/_/g, ' ')}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 font-mono">
                      {sig.current_risk_category ? (
                        <span
                          className={`font-semibold ${
                            sig.current_risk_category === 'High'
                              ? 'text-rose-400'
                              : sig.current_risk_category === 'Medium'
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }`}
                        >
                          {sig.current_risk_category}
                        </span>
                      ) : (
                        <span className="text-textSecondary/60">None</span>
                      )}
                    </td>

                    <td className="py-2.5 px-3 font-mono">
                      <span
                        className={
                          sig.trend_direction === 'WORSENING'
                            ? 'text-rose-400 font-semibold'
                            : sig.trend_direction === 'IMPROVING'
                            ? 'text-emerald-400 font-semibold'
                            : 'text-textPrimary'
                        }
                      >
                        {sig.trend_direction || '—'}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 font-mono text-[11px]">
                      <div className="flex items-center space-x-2">
                        {sig.has_active_alert && (
                          <span className="text-amber-400 flex items-center space-x-0.5" title="Active Alert">
                            <Bell className="w-3 h-3" />
                            <span>Alert</span>
                          </span>
                        )}
                        {sig.has_active_anomaly && (
                          <span className="text-indigo-400 flex items-center space-x-0.5" title="Active Anomaly">
                            <Activity className="w-3 h-3" />
                            <span>Anomaly</span>
                          </span>
                        )}
                        {sig.has_open_recommendation && (
                          <span className="text-blue-400 flex items-center space-x-0.5" title="Support Recommendation">
                            <HeartHandshake className="w-3 h-3" />
                            <span>Rec</span>
                          </span>
                        )}
                        {!sig.has_active_alert && !sig.has_active_anomaly && !sig.has_open_recommendation && (
                          <span className="text-textSecondary/60">Normal</span>
                        )}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 font-mono text-textSecondary text-[11px]">
                      {c.last_reviewed_at ? (
                        <div>
                          <div>{new Date(c.last_reviewed_at).toLocaleDateString()}</div>
                          <div className="text-[10px] text-textSecondary/80">by {c.last_reviewed_by_name}</div>
                        </div>
                      ) : (
                        <span className="text-amber-400/80">Pending Initial Review</span>
                      )}
                    </td>

                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleSelectCase(c.id)}
                        className="px-2.5 py-1 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded text-xs font-mono font-medium transition-colors border border-border inline-flex items-center space-x-1"
                      >
                        <Eye className="w-3 h-3 text-accent" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {/* 5. Case Detail Workspace Modal / Drawer */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-border/80 flex items-center justify-between bg-surfaceHighlight/40">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
                  <FolderKanban className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-bold text-textPrimary uppercase">
                      {selectedCase.case_reference}: {selectedCase.title}
                    </h3>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${getStatusBadge(
                        selectedCase.status
                      )}`}
                    >
                      {selectedCase.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-textSecondary font-mono mt-0.5">
                    Subject: {selectedCase.personnel_name} ({selectedCase.personnel_code}) • Battalion: {selectedCase.battalion} • Location: {selectedCase.location}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setSelectedCase(null)}
                  className="p-1.5 hover:bg-surfaceHighlight rounded-lg text-textSecondary hover:text-textPrimary transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Action Bar */}
            <div className="px-5 py-2.5 bg-surfaceHighlight/20 border-b border-border/60 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowReviewModal(true)}
                  className="flex items-center space-x-1.5 px-3 py-1 bg-accent hover:bg-accent/80 text-white rounded text-xs font-mono font-medium transition-colors shadow-sm"
                >
                  <UserCheck className="w-3.5 h-3.5" />
                  <span>Record Human Decision</span>
                </button>

                <button
                  onClick={() => setShowNoteModal(true)}
                  className="flex items-center space-x-1.5 px-3 py-1 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded text-xs font-mono font-medium transition-colors border border-border"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Add Note</span>
                </button>
              </div>

              <div className="flex items-center space-x-2">
                {selectedCase.status !== 'CLOSED' ? (
                  <button
                    onClick={() => setShowCloseModal(true)}
                    className="flex items-center space-x-1.5 px-3 py-1 bg-rose-950/40 hover:bg-rose-950/60 text-rose-300 border border-rose-800/40 rounded text-xs font-mono font-medium transition-colors"
                  >
                    <Lock className="w-3.5 h-3.5" />
                    <span>Close Case</span>
                  </button>
                ) : (
                  <button
                    onClick={() => setShowReopenModal(true)}
                    className="flex items-center space-x-1.5 px-3 py-1 bg-blue-950/40 hover:bg-blue-950/60 text-blue-300 border border-blue-800/40 rounded text-xs font-mono font-medium transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reopen Case</span>
                  </button>
                )}
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="px-5 pt-3 border-b border-border/60 flex space-x-4 text-xs font-mono">
              <button
                onClick={() => setActiveTab('evidence')}
                className={`pb-2.5 font-medium border-b-2 transition-colors ${
                  activeTab === 'evidence'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-textSecondary hover:text-textPrimary'
                }`}
              >
                1. Welfare Signals (P34–42)
              </button>
              <button
                onClick={() => setActiveTab('reviews')}
                className={`pb-2.5 font-medium border-b-2 transition-colors ${
                  activeTab === 'reviews'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-textSecondary hover:text-textPrimary'
                }`}
              >
                2. Human Reviews ({selectedCase.reviews.length})
              </button>
              <button
                onClick={() => setActiveTab('notes')}
                className={`pb-2.5 font-medium border-b-2 transition-colors ${
                  activeTab === 'notes'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-textSecondary hover:text-textPrimary'
                }`}
              >
                3. Case Notes ({selectedCase.notes.length})
              </button>
              <button
                onClick={() => setActiveTab('timeline')}
                className={`pb-2.5 font-medium border-b-2 transition-colors ${
                  activeTab === 'timeline'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-textSecondary hover:text-textPrimary'
                }`}
              >
                4. Timeline
              </button>
              <button
                onClick={() => setActiveTab('audits')}
                className={`pb-2.5 font-medium border-b-2 transition-colors ${
                  activeTab === 'audits'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-textSecondary hover:text-textPrimary'
                }`}
              >
                5. Audit Trail
              </button>
            </div>

            {/* Tab Contents */}
            <div className="p-5 overflow-y-auto space-y-6 flex-1">
              {actionError && (
                <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-200 flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>{actionError}</span>
                </div>
              )}

              {/* TAB 1: EVIDENCE & SIGNALS */}
              {activeTab === 'evidence' && (
                <div className="space-y-4">
                  <div className="p-3 bg-surfaceHighlight/30 border border-border/50 rounded-lg text-xs text-textSecondary">
                    <p className="leading-relaxed">
                      <strong>Authoritative Welfare Context:</strong> This evidence summary consolidates raw operational signals from Phases 34 through 41 without computing an arbitrary composite case score.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Phase 34 Risk Assessment */}
                    <div className="p-4 bg-surfaceHighlight/40 border border-border/60 rounded-lg space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono uppercase text-textSecondary">
                        <span>Phase 34 Authoritative Risk</span>
                        <Shield className="w-4 h-4 text-blue-400" />
                      </div>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-2xl font-bold font-mono text-textPrimary">
                          {selectedCase.evidence.current_risk.risk_score !== undefined && selectedCase.evidence.current_risk.risk_score !== null
                            ? `${selectedCase.evidence.current_risk.risk_score}`
                            : 'N/A'}
                        </span>
                        <span className="text-xs font-mono text-textSecondary">/ 100</span>
                        <span
                          className={`ml-2 text-xs font-mono font-semibold ${
                            selectedCase.evidence.current_risk.stress_level === 'High'
                              ? 'text-rose-400'
                              : selectedCase.evidence.current_risk.stress_level === 'Medium'
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }`}
                        >
                          ({selectedCase.evidence.current_risk.stress_level || 'Insufficient Data'})
                        </span>
                      </div>
                      <div className="text-[11px] text-textSecondary">
                        Priority: {selectedCase.evidence.current_risk.risk_priority || 'Routine'}
                      </div>
                      {selectedCase.evidence.current_risk.key_factors?.length > 0 && (
                        <div className="pt-2 border-t border-border/40 text-[11px]">
                          <span className="text-textSecondary">Key Factors: </span>
                          <span className="text-textPrimary font-mono">
                            {selectedCase.evidence.current_risk.key_factors.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Phase 36 Longitudinal Trend */}
                    <div className="p-4 bg-surfaceHighlight/40 border border-border/60 rounded-lg space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono uppercase text-textSecondary">
                        <span>Phase 36 Longitudinal Trend</span>
                        <Activity className="w-4 h-4 text-indigo-400" />
                      </div>
                      <div className="text-lg font-bold font-mono text-textPrimary">
                        {selectedCase.evidence.trend.trend_direction || 'INSUFFICIENT_DATA'}
                      </div>
                      <div className="text-[11px] text-textSecondary font-mono">
                        Persistence: {selectedCase.evidence.trend.persistence || 'N/A'} • Slope:{' '}
                        {selectedCase.evidence.trend.trend_slope ? `${selectedCase.evidence.trend.trend_slope} pts/day` : 'N/A'}
                      </div>
                      <div className="text-[11px] text-textSecondary">
                        Baseline Score: {selectedCase.evidence.trend.personal_baseline_score?.toFixed(1) || 'N/A'}
                      </div>
                    </div>

                    {/* Phase 37 Alerts */}
                    <div className="p-4 bg-surfaceHighlight/40 border border-border/60 rounded-lg space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono uppercase text-textSecondary">
                        <span>Phase 37 Active Alert</span>
                        <Bell className="w-4 h-4 text-amber-400" />
                      </div>
                      {selectedCase.evidence.active_alert ? (
                        <div>
                          <div className="font-semibold text-textPrimary">
                            {selectedCase.evidence.active_alert.alert_type} ({selectedCase.evidence.active_alert.severity})
                          </div>
                          <div className="text-[11px] text-textSecondary mt-1">
                            {selectedCase.evidence.active_alert.trigger_reason}
                          </div>
                          <div className="text-[10px] text-textSecondary font-mono mt-1">
                            Status: {selectedCase.evidence.active_alert.status}
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-textSecondary font-mono">No active alerts recorded.</div>
                      )}
                    </div>

                    {/* Phase 40 Recommendations */}
                    <div className="p-4 bg-surfaceHighlight/40 border border-border/60 rounded-lg space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono uppercase text-textSecondary">
                        <span>Phase 40 Support Recommendation</span>
                        <HeartHandshake className="w-4 h-4 text-blue-400" />
                      </div>
                      {selectedCase.evidence.open_recommendation ? (
                        <div>
                          <div className="font-semibold text-textPrimary">
                            {selectedCase.evidence.open_recommendation.title || selectedCase.evidence.open_recommendation.recommendation_type}
                          </div>
                          <div className="text-[11px] text-textSecondary mt-1">
                            Priority: {selectedCase.evidence.open_recommendation.priority}
                          </div>
                          <div className="text-[10px] text-textSecondary font-mono mt-1">
                            Status: {selectedCase.evidence.open_recommendation.status} (Human decision required)
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-textSecondary font-mono">No pending recommendations.</div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: HUMAN REVIEWS */}
              {activeTab === 'reviews' && (
                <div className="space-y-4">
                  <div className="p-3 bg-indigo-950/30 border border-indigo-800/40 rounded-lg text-xs text-indigo-200">
                    <strong>Distinction:</strong> Human review decisions are authoritative workflow actions recorded by authorized commanders or welfare officers. They are explicitly separated from automated system recommendations.
                  </div>

                  {selectedCase.reviews.length === 0 ? (
                    <div className="py-8 text-center text-textSecondary font-mono text-xs">
                      No formal human reviews have been recorded on this case yet. Click &quot;Record Human Decision&quot; to begin.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {selectedCase.reviews.map((rev) => (
                        <div
                          key={rev.id}
                          className="p-4 bg-surfaceHighlight/40 border border-border/70 rounded-lg space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <span className="px-2 py-0.5 bg-indigo-950/60 text-indigo-400 border border-indigo-800/40 rounded text-[10px] font-mono font-semibold">
                              {rev.review_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-[11px] font-mono text-textSecondary">
                              {new Date(rev.reviewed_at).toLocaleString()} by <strong>{rev.reviewer_name}</strong> ({rev.reviewer_role})
                            </span>
                          </div>

                          <div className="text-xs text-textPrimary leading-relaxed">
                            <strong className="text-textSecondary">Observations: </strong>
                            {rev.observations}
                          </div>

                          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-border/40 text-xs font-mono">
                            <div>
                              <span className="text-textSecondary text-[10px] uppercase block">Decision</span>
                              <span className="font-semibold text-emerald-400">{rev.decision.replace(/_/g, ' ')}</span>
                            </div>

                            {rev.next_step && (
                              <div>
                                <span className="text-textSecondary text-[10px] uppercase block">Next Step</span>
                                <span className="text-textPrimary">{rev.next_step}</span>
                              </div>
                            )}

                            <div>
                              <span className="text-textSecondary text-[10px] uppercase block">Review Window</span>
                              <span className="text-textSecondary">{rev.review_window || 'Within 14 days'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: CASE NOTES (IMMUTABLE) */}
              {activeTab === 'notes' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-textSecondary">
                      Immutable historical audit trail of human commentary.
                    </span>
                    <button
                      onClick={() => setShowNoteModal(true)}
                      className="px-2.5 py-1 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded text-xs font-mono border border-border flex items-center space-x-1"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Add Note</span>
                    </button>
                  </div>

                  {selectedCase.notes.length === 0 ? (
                    <div className="py-8 text-center text-textSecondary font-mono text-xs">
                      No notes have been added to this case history yet.
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {selectedCase.notes.map((note) => (
                        <div
                          key={note.id}
                          className="p-3 bg-surfaceHighlight/30 border border-border/60 rounded-lg space-y-1"
                        >
                          <div className="flex items-center justify-between text-[11px] font-mono">
                            <span className="px-1.5 py-0.5 bg-surfaceHighlight rounded text-textSecondary uppercase">
                              {note.note_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-textSecondary">
                              {new Date(note.created_at).toLocaleString()} • {note.author_name}
                            </span>
                          </div>
                          <p className="text-xs text-textPrimary leading-relaxed whitespace-pre-wrap mt-1">
                            {note.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: TIMELINE */}
              {activeTab === 'timeline' && (
                <div className="space-y-3">
                  <div className="text-xs text-textSecondary font-mono mb-2">
                    Unified multi-phase chronology combining telemetry system triggers and human actions.
                  </div>
                  {/* Timeline events container */}
                  <div className="border-l-2 border-border/80 ml-3 pl-4 space-y-4 py-2">
                    {/* Render timeline items */}
                    <div className="relative">
                      <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-surface" />
                      <div className="text-xs font-mono text-textSecondary">
                        {new Date(selectedCase.opened_at).toLocaleString()} • <strong className="text-emerald-400">HUMAN ACTION</strong>
                      </div>
                      <div className="font-semibold text-xs text-textPrimary mt-0.5">
                        Welfare Case Opened ({selectedCase.case_reference})
                      </div>
                      <div className="text-xs text-textSecondary mt-0.5">
                        Triggered by {selectedCase.trigger_source} • Opened by {selectedCase.opened_by_name || 'Reviewer'}
                      </div>
                    </div>

                    {selectedCase.reviews.map((rev) => (
                      <div key={rev.id} className="relative">
                        <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-indigo-500 border-2 border-surface" />
                        <div className="text-xs font-mono text-textSecondary">
                          {new Date(rev.reviewed_at).toLocaleString()} • <strong className="text-indigo-400">HUMAN ACTION</strong>
                        </div>
                        <div className="font-semibold text-xs text-textPrimary mt-0.5">
                          Human Review: {rev.decision.replace(/_/g, ' ')}
                        </div>
                        <div className="text-xs text-textSecondary mt-0.5">
                          {rev.observations}
                        </div>
                      </div>
                    ))}

                    {selectedCase.closed_at && (
                      <div className="relative">
                        <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-rose-500 border-2 border-surface" />
                        <div className="text-xs font-mono text-textSecondary">
                          {new Date(selectedCase.closed_at).toLocaleString()} • <strong className="text-rose-400">HUMAN ACTION</strong>
                        </div>
                        <div className="font-semibold text-xs text-textPrimary mt-0.5">
                          Case Closed ({selectedCase.closure_reason})
                        </div>
                        <div className="text-xs text-textSecondary mt-0.5">
                          Closed by {selectedCase.closed_by_name}. Notes: {selectedCase.closure_notes || 'None'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 5: AUDIT TRAIL */}
              {activeTab === 'audits' && (
                <div className="space-y-3">
                  <div className="text-xs text-textSecondary font-mono">
                    Append-only audit trail guaranteeing non-repudiation of all status changes and human reviews.
                  </div>
                  <div className="border border-border/80 rounded-lg overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-surfaceHighlight/50 border-b border-border/80 text-[10px] font-mono uppercase text-textSecondary">
                        <tr>
                          <th className="py-2 px-3">Timestamp</th>
                          <th className="py-2 px-3">Action</th>
                          <th className="py-2 px-3">Actor</th>
                          <th className="py-2 px-3">Transition</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60 font-mono text-[11px]">
                        {selectedCase.latest_audit && (
                          <tr>
                            <td className="py-2 px-3 text-textSecondary">
                              {new Date(selectedCase.latest_audit.timestamp).toLocaleString()}
                            </td>
                            <td className="py-2 px-3 text-textPrimary font-semibold">
                              {selectedCase.latest_audit.action}
                            </td>
                            <td className="py-2 px-3 text-textSecondary">
                              {selectedCase.latest_audit.actor_name || 'System'}
                            </td>
                            <td className="py-2 px-3 text-textSecondary">
                              {selectedCase.latest_audit.previous_status || '—'} &rarr;{' '}
                              <strong className="text-textPrimary">{selectedCase.latest_audit.new_status}</strong>
                            </td>
                          </tr>
                        )}
                        <tr>
                          <td className="py-2 px-3 text-textSecondary">
                            {new Date(selectedCase.opened_at).toLocaleString()}
                          </td>
                          <td className="py-2 px-3 text-emerald-400 font-semibold">CASE_CREATED</td>
                          <td className="py-2 px-3 text-textSecondary">{selectedCase.opened_by_name || 'System'}</td>
                          <td className="py-2 px-3 text-textSecondary">
                            None &rarr; <strong className="text-textPrimary">OPEN</strong>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* CREATE CASE MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-textPrimary uppercase">Open Welfare Case</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-mono text-textSecondary mb-1">Target Personnel ID *</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 1"
                  value={newCasePersonnelId}
                  onChange={(e) => setNewCasePersonnelId(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Case Type / Trigger Reason *</label>
                <select
                  value={newCaseType}
                  onChange={(e) => setNewCaseType(e.target.value as CaseType)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent font-mono"
                >
                  <option value="CURRENT_RISK_REVIEW">Current Risk Review (Phase 34)</option>
                  <option value="WORSENING_TREND">Worsening Trend (Phase 36)</option>
                  <option value="ACTIVE_ALERT">Active Alert (Phase 37)</option>
                  <option value="ANOMALY_REVIEW">Anomaly Review (Phase 39)</option>
                  <option value="SUPPORT_FOLLOW_UP">Support Follow-up (Phase 41)</option>
                  <option value="REPEATED_WELFARE_CONCERN">Repeated Welfare Concern</option>
                  <option value="OTHER">Other Structured Concern</option>
                </select>
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Case Title (Optional)</label>
                <input
                  type="text"
                  placeholder="Leave empty for auto-generated title"
                  value={newCaseTitle}
                  onChange={(e) => setNewCaseTitle(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Context / Explanation</label>
                <textarea
                  rows={3}
                  placeholder="Describe reasons and context for opening this case..."
                  value={newCaseSummary}
                  onChange={(e) => setNewCaseSummary(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 bg-surfaceHighlight text-textSecondary rounded font-mono hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 bg-accent hover:bg-accent/80 text-white rounded font-mono font-medium disabled:opacity-50"
                >
                  {actionLoading ? 'Opening...' : 'Open Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RECORD REVIEW MODAL */}
      {showReviewModal && selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-textPrimary uppercase">Record Human Review & Decision</h3>
              <button onClick={() => setShowReviewModal(false)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRecordReview} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-mono text-textSecondary mb-1">Review Type *</label>
                <select
                  value={reviewType}
                  onChange={(e) => setReviewType(e.target.value as ReviewType)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent font-mono"
                >
                  <option value="INITIAL_TRIAGE">Initial Triage</option>
                  <option value="PROGRESS_EVALUATION">Progress Evaluation</option>
                  <option value="INTERVENTION_REVIEW">Intervention Review</option>
                  <option value="FOLLOWUP_ASSESSMENT">Followup Assessment</option>
                  <option value="CLOSURE_REVIEW">Closure Review</option>
                  <option value="ROUTINE_MONITORING">Routine Monitoring</option>
                </select>
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Reviewer Observations *</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Record factual observations from interview, duty logs, or welfare check..."
                  value={reviewObservations}
                  onChange={(e) => setReviewObservations(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Human Decision *</label>
                <select
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value as HumanDecision)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent font-mono"
                >
                  <option value="CONTINUE_MONITORING">Continue Monitoring</option>
                  <option value="CONTACT_PERSONNEL">Contact Personnel Directly</option>
                  <option value="REVIEW_DUTY_SUPPORT">Review Duty Support / Shift Adjustment</option>
                  <option value="OFFER_SUPPORT_RESOURCE">Offer Support Resource</option>
                  <option value="SCHEDULE_FOLLOW_UP">Schedule Follow-up</option>
                  <option value="CONTINUE_EXISTING_INTERVENTION">Continue Existing Intervention</option>
                  <option value="REFER_TO_AUTHORIZED_SUPPORT">Refer to Authorized Support</option>
                  <option value="CLOSE_CASE">Close Case</option>
                  <option value="OTHER">Other Human Decision</option>
                </select>
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Next Step Action</label>
                <input
                  type="text"
                  placeholder="Specific follow-up action plan..."
                  value={reviewNextStep}
                  onChange={(e) => setReviewNextStep(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-mono text-textSecondary mb-1">Review Window</label>
                  <input
                    type="text"
                    value={reviewWindow}
                    onChange={(e) => setReviewWindow(e.target.value)}
                    className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent font-mono"
                  />
                </div>

                <div>
                  <label className="block font-mono text-textSecondary mb-1">Target Status</label>
                  <select
                    value={reviewStatusTransition}
                    onChange={(e) => setReviewStatusTransition(e.target.value)}
                    className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent font-mono"
                  >
                    <option value="">Keep Current ({selectedCase.status})</option>
                    <option value="UNDER_REVIEW">Move to UNDER_REVIEW</option>
                    <option value="SUPPORT_IN_PROGRESS">Move to SUPPORT_IN_PROGRESS</option>
                    <option value="AWAITING_FOLLOW_UP">Move to AWAITING_FOLLOW_UP</option>
                    <option value="MONITORING">Move to MONITORING</option>
                    <option value="RESOLVED">Move to RESOLVED</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowReviewModal(false)}
                  className="px-3 py-1.5 bg-surfaceHighlight text-textSecondary rounded font-mono hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 bg-accent hover:bg-accent/80 text-white rounded font-mono font-medium disabled:opacity-50"
                >
                  {actionLoading ? 'Recording...' : 'Submit Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD NOTE MODAL */}
      {showNoteModal && selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-md p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-textPrimary uppercase">Add Case Note</h3>
              <button onClick={() => setShowNoteModal(false)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddNote} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-mono text-textSecondary mb-1">Note Type *</label>
                <select
                  value={noteType}
                  onChange={(e) => setNoteType(e.target.value as NoteType)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent font-mono"
                >
                  <option value="REVIEW_NOTE">Review Note</option>
                  <option value="SUPPORT_NOTE">Support Note</option>
                  <option value="FOLLOW_UP_NOTE">Follow-up Note</option>
                  <option value="OUTCOME_NOTE">Outcome Note</option>
                  <option value="GENERAL_NOTE">General Note</option>
                </select>
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Content *</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Record detailed observation or note..."
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowNoteModal(false)}
                  className="px-3 py-1.5 bg-surfaceHighlight text-textSecondary rounded font-mono hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 bg-accent hover:bg-accent/80 text-white rounded font-mono font-medium disabled:opacity-50"
                >
                  {actionLoading ? 'Saving...' : 'Add Note'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CLOSE CASE MODAL */}
      {showCloseModal && selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-md p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-textPrimary uppercase">Close Welfare Case</h3>
              <button onClick={() => setShowCloseModal(false)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCloseCase} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-mono text-textSecondary mb-1">Closure Reason *</label>
                <select
                  value={closureReason}
                  onChange={(e) => setClosureReason(e.target.value as ClosureReason)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent font-mono"
                >
                  <option value="RESOLVED">Resolved (Goals achieved)</option>
                  <option value="MONITORING_COMPLETED">Monitoring Completed</option>
                  <option value="SUPPORT_COMPLETED">Support Completed</option>
                  <option value="NO_FURTHER_ACTION_REQUIRED">No Further Action Required</option>
                  <option value="TRANSFERRED">Transferred to New Battalion</option>
                  <option value="DUPLICATE">Duplicate Case</option>
                  <option value="OTHER">Other Reason</option>
                </select>
              </div>

              <div>
                <label className="block font-mono text-textSecondary mb-1">Closure Notes / Justification</label>
                <textarea
                  rows={3}
                  placeholder="Summarize reasons for closing this case..."
                  value={closureNotes}
                  onChange={(e) => setClosureNotes(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowCloseModal(false)}
                  className="px-3 py-1.5 bg-surfaceHighlight text-textSecondary rounded font-mono hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded font-mono font-medium disabled:opacity-50"
                >
                  {actionLoading ? 'Closing...' : 'Confirm Closure'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* REOPEN CASE MODAL */}
      {showReopenModal && selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-md p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-textPrimary uppercase">Reopen Welfare Case</h3>
              <button onClick={() => setShowReopenModal(false)} className="text-textSecondary hover:text-textPrimary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleReopenCase} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-mono text-textSecondary mb-1">Reopen Reason *</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Record mandatory operational reason for reopening..."
                  value={reopenReason}
                  onChange={(e) => setReopenReason(e.target.value)}
                  className="w-full px-3 py-1.5 bg-surfaceHighlight/50 border border-border rounded text-textPrimary focus:outline-none focus:border-accent"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowReopenModal(false)}
                  className="px-3 py-1.5 bg-surfaceHighlight text-textSecondary rounded font-mono hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 bg-accent hover:bg-accent/80 text-white rounded font-mono font-medium disabled:opacity-50"
                >
                  {actionLoading ? 'Reopening...' : 'Reopen Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
