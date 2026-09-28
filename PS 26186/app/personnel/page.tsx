'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/DashboardLayout';
import RiskBadge from '@/components/dashboard/RiskBadge';
import { getPersonnel, PersonnelFilters } from '@/lib/personnel';
import { PersonnelOut } from '@/types/api';
import { Users, Filter, ChevronLeft, ChevronRight, Search, Eye, ShieldAlert } from 'lucide-react';
import EmptyState from '@/components/ui/EmptyState';

export default function PersonnelDirectoryPage() {
  const [personnelList, setPersonnelList] = useState<PersonnelOut[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [pageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [department, setDepartment] = useState<string>('');
  const [location, setLocation] = useState<string>('');
  const [riskPriority, setRiskPriority] = useState<string>('');
  const [stressLevel, setStressLevel] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const fetchPersonnel = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const filters: PersonnelFilters = {
        page,
        size: pageSize,
        department: department || undefined,
        location: location || undefined,
        risk_priority: riskPriority || undefined,
        stress_level: stressLevel || undefined,
      };

      const res = await getPersonnel(filters);
      setPersonnelList(res.items || []);
      setTotal(res.total || 0);
      setPages(res.pages || 1);
    } catch (err: any) {
      console.error('Failed to load personnel directory:', err);
      setError(err?.message || 'Error loading personnel records.');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, department, location, riskPriority, stressLevel]);

  useEffect(() => {
    fetchPersonnel();
  }, [fetchPersonnel]);

  // Client-side quick filter by search term (code or name)
  const displayedPersonnel = searchTerm
    ? personnelList.filter(
        p =>
          p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.personnel_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.job_role.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : personnelList;

  const resetFilters = () => {
    setDepartment('');
    setLocation('');
    setRiskPriority('');
    setStressLevel('');
    setSearchTerm('');
    setPage(1);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-textPrimary uppercase">
            Personnel Directory & Service Registry
          </h1>
          <p className="text-xs text-textSecondary mt-1 font-mono">
            Active force roster with calibrated operational strain telemetry
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="bg-surface p-4 border border-surfaceHighlight rounded-lg space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-textSecondary" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by name, rank/role, or service code..."
                className="w-full bg-surfaceHighlight border border-surfaceHighlight focus:border-accent text-sm rounded pl-9 pr-3 py-2 text-textPrimary outline-none font-mono"
              />
            </div>

            {/* Department Filter */}
            <select
              value={department}
              onChange={(e) => { setDepartment(e.target.value); setPage(1); }}
              className="bg-surfaceHighlight border border-surfaceHighlight text-xs rounded px-3 py-2 text-textPrimary outline-none focus:border-accent"
            >
              <option value="">All Departments</option>
              <option value="Operations">Operations</option>
              <option value="Communications">Communications</option>
              <option value="HR">HR & Admin</option>
              <option value="Engineering">Engineering</option>
              <option value="Marketing">Marketing / Public Affairs</option>
            </select>

            {/* Base Location Filter */}
            <select
              value={location}
              onChange={(e) => { setLocation(e.target.value); setPage(1); }}
              className="bg-surfaceHighlight border border-surfaceHighlight text-xs rounded px-3 py-2 text-textPrimary outline-none focus:border-accent"
            >
              <option value="">All Locations</option>
              <option value="Srinagar">Srinagar</option>
              <option value="Leh">Leh</option>
              <option value="Dantewada">Dantewada</option>
              <option value="Sukma">Sukma</option>
              <option value="Delhi">Delhi</option>
              <option value="Guwahati">Guwahati</option>
            </select>

            {/* Risk Priority Filter */}
            <select
              value={riskPriority}
              onChange={(e) => { setRiskPriority(e.target.value); setPage(1); }}
              className="bg-surfaceHighlight border border-surfaceHighlight text-xs rounded px-3 py-2 text-textPrimary outline-none focus:border-accent"
            >
              <option value="">All Welfare Tiers</option>
              <option value="Routine">Routine (&lt;40)</option>
              <option value="Preventive">Preventive (40-69)</option>
              <option value="Priority">Priority (≥70)</option>
            </select>

            {/* Stress Level Filter */}
            <select
              value={stressLevel}
              onChange={(e) => { setStressLevel(e.target.value); setPage(1); }}
              className="bg-surfaceHighlight border border-surfaceHighlight text-xs rounded px-3 py-2 text-textPrimary outline-none focus:border-accent"
            >
              <option value="">All Stress Tiers</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>

            {(department || location || riskPriority || stressLevel || searchTerm) && (
              <button
                onClick={resetFilters}
                className="px-3 py-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-xs text-textSecondary hover:text-textPrimary rounded font-medium transition-colors"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="p-3 bg-[#FAF0F0] border border-[#E8B4B4] rounded text-[#964747] text-xs">
            {error}
          </div>
        )}

        {/* Directory Table and Mobile Cards */}
        <div className="bg-surface border border-surfaceHighlight rounded-lg flex flex-col overflow-hidden">
          <div className="overflow-x-auto hidden md:block">
            <table className="w-full text-left text-sm">
              <thead className="bg-surfaceHighlight/50 text-textSecondary uppercase tracking-widest text-xs border-b border-surfaceHighlight">
                <tr>
                  <th className="px-4 py-3 font-medium">Service Code</th>
                  <th className="px-4 py-3 font-medium">Personnel Name</th>
                  <th className="px-4 py-3 font-medium">Role & Section</th>
                  <th className="px-4 py-3 font-medium">Station</th>
                  <th className="px-4 py-3 font-medium">Duty / Nights</th>
                  <th className="px-4 py-3 font-medium">Leave Gap</th>
                  <th className="px-4 py-3 font-medium">Latest Stress</th>
                  <th className="px-4 py-3 font-medium">Risk Score</th>
                  <th className="px-4 py-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surfaceHighlight bg-surface">
                {loading ? (
                  [...Array(6)].map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td colSpan={9} className="px-4 py-3">
                        <div className="h-4 bg-surfaceHighlight rounded w-full" />
                      </td>
                    </tr>
                  ))
                ) : displayedPersonnel.length > 0 ? (
                  displayedPersonnel.map((p) => (
                    <tr
                      key={p.id}
                      className="hover:bg-surfaceHighlight/30 transition-colors"
                    >
                      <td className="px-4 py-3 font-mono text-accent font-semibold">
                        {p.personnel_code}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-textPrimary">{p.name}</div>
                        <div className="text-[11px] text-textSecondary">{p.age} yrs • {p.gender}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-textPrimary">{p.job_role}</div>
                        <div className="text-[11px] text-textSecondary">{p.department}</div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-textSecondary">
                        {p.location}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">
                        <div className="text-textPrimary">{p.duty_hours_per_week}h/wk</div>
                        <div className="text-textSecondary text-[10px]">{p.night_shifts_per_month} nights/mo</div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-textSecondary">
                        {p.leave_gap_days} days
                      </td>
                      <td className="px-4 py-3">
                        {p.latest_stress_level ? (
                          <RiskBadge level={p.latest_stress_level} />
                        ) : (
                          <span className="text-xs text-textSecondary italic">Unassessed</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono">
                        {p.latest_risk_score !== null && p.latest_risk_score !== undefined ? (
                          <span className={`font-bold ${
                            p.latest_risk_score >= 70 ? 'text-[#C26D6D]' :
                            p.latest_risk_score >= 40 ? 'text-[#D99B5C]' : 'text-[#7BA083]'
                          }`}>
                            {p.latest_risk_score}
                          </span>
                        ) : (
                          <span className="text-textSecondary">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/personnel/${p.id}`}
                          className="inline-flex items-center space-x-1 px-2.5 py-1 bg-surfaceHighlight hover:bg-accent hover:text-white rounded text-xs font-medium text-accent transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Inspect</span>
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="p-0 border-none">
                      <div className="h-64">
                        <EmptyState
                          icon={Users}
                          title="No Personnel Found"
                          description="No records match your selected operational filters."
                        />
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Mobile & Tablet Card Layout (Prevents Horizontal Overflow) */}
          <div className="md:hidden divide-y divide-surfaceHighlight p-3 space-y-3">
            {loading ? (
              [...Array(4)].map((_, i) => (
                <div key={i} className="p-4 bg-surfaceHighlight/20 rounded-lg animate-pulse h-28" />
              ))
            ) : displayedPersonnel.length > 0 ? (
              displayedPersonnel.map((p) => (
                <div
                  key={p.id}
                  className="p-3.5 bg-surfaceHighlight/20 rounded-lg border border-surfaceHighlight space-y-3"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-mono text-xs text-accent font-semibold">{p.personnel_code}</span>
                      <h4 className="font-bold text-sm text-textPrimary">{p.name}</h4>
                      <p className="text-xs text-textSecondary">{p.job_role} • {p.department}</p>
                    </div>
                    <div className="text-right">
                      {p.latest_stress_level ? (
                        <RiskBadge level={p.latest_stress_level} />
                      ) : (
                        <span className="text-[11px] text-textSecondary italic">Unassessed</span>
                      )}
                      {p.latest_risk_score !== null && p.latest_risk_score !== undefined && (
                        <div className="text-xs font-mono font-bold text-[#C26D6D] mt-1">
                          Risk {p.latest_risk_score}/100
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono py-1 bg-surfaceHighlight/30 rounded p-1.5">
                    <div>
                      <span className="text-[10px] text-textSecondary block">Weekly</span>
                      <span className="text-textPrimary font-semibold">{p.duty_hours_per_week}h</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-textSecondary block">Night Shifts</span>
                      <span className="text-textPrimary font-semibold">{p.night_shifts_per_month}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-textSecondary block">Leave Gap</span>
                      <span className="text-textPrimary font-semibold">{p.leave_gap_days}d</span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center pt-1 border-t border-surfaceHighlight/40 text-xs">
                    <span className="text-textSecondary font-mono text-[11px]">Station: {p.location}</span>
                    <Link
                      href={`/personnel/${p.id}`}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 bg-accent hover:bg-accent/80 text-white rounded text-xs font-medium transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect Dossier</span>
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12">
                <EmptyState
                  icon={Users}
                  title="No Personnel Found"
                  description="No records match your selected operational filters."
                />
              </div>
            )}
          </div>

          {/* Pagination Footer */}
          <div className="p-4 border-t border-surfaceHighlight bg-surfaceHighlight/20 flex items-center justify-between text-xs text-textSecondary">
            <span>
              Showing {displayedPersonnel.length} of {total} personnel
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1 || loading}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="p-1 rounded bg-surfaceHighlight hover:bg-surfaceHighlight/80 disabled:opacity-30 disabled:cursor-not-allowed text-textPrimary"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-mono text-textPrimary">
                Page {page} of {pages || 1}
              </span>
              <button
                disabled={page >= pages || loading}
                onClick={() => setPage(p => Math.min(pages, p + 1))}
                className="p-1 rounded bg-surfaceHighlight hover:bg-surfaceHighlight/80 disabled:opacity-30 disabled:cursor-not-allowed text-textPrimary"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

