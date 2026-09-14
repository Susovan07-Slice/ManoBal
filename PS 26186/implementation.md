# implementation.md
## Commander & Welfare Officer Dashboard — AI-Based Personnel Stress Monitoring System

**Purpose:** This is an architectural blueprint for an AI coding agent (Antigravity) to scaffold a Next.js frontend. It contains folder structure, data contracts, component architecture, and sequential build prompts — no application code is written here directly; Antigravity generates that from the prompts in Phase 4.

**Data lineage note (read before Phase 2):** This frontend is being built against **mock data only**. The real pipeline behind it trains on `FINAL_MAIN_STRESS_DATASET.csv` and validates externally on `D2_cleaned.csv` — the two are never merged. Because `D2_cleaned.csv` (the validation set) has a smaller feature set than the training set, the mock schemas in Phase 2 are deliberately anchored to the **feature subset common to both datasets** (age, department, role, weekly work/duty hours, remote-work status, sleep hours, physical activity, job/work-life satisfaction, stress level) plus a small set of military-specific operational fields present only in the training set (deployment days, duty hours, night shifts, consecutive duty days, leave-gap days, operational exposure). This means when the real model is wired in later, the UI contract won't need breaking changes — fields that only the training set has are treated as "enrichment," not required, in the type definitions below.

---

## Phase 1: Project Setup & State

### 1.1 Folder Structure

```
/app
  layout.tsx                     # Root layout, RoleProvider wraps children
  globals.css                    # Tailwind base + design tokens
  page.tsx                       # Redirects to /dashboard
  /dashboard
    page.tsx                     # Composes DashboardLayout + panels
    loading.tsx                  # Skeleton state
  /api
    /mock
      /unit-aggregates
        route.ts                 # Returns mock UnitAggregates[] (simulates future backend)
      /personnel-alerts
        route.ts                 # Returns mock PersonnelAlert[]

/components
  /layout
    DashboardLayout.tsx
    Sidebar.tsx
    Topbar.tsx
    RoleToggle.tsx
  /dashboard
    MainMetricsRow.tsx
    MetricCard.tsx
    RiskTrendChart.tsx
    UnitOverviewPanel.tsx
    AlertsTable.tsx
    AlertDetailDrawer.tsx
    RiskBadge.tsx
  /ui
    Card.tsx
    Badge.tsx
    Table.tsx
    Tabs.tsx
    Skeleton.tsx
    EmptyState.tsx

/lib
  mock-data.ts                   # Sample arrays + simulated async fetchers
  rbac.ts                        # Role → permission mapping
  constants.ts                   # Risk color map, thresholds, nav items
  utils.ts                       # cn() helper (clsx + tailwind-merge), date/number formatters

/types
  dashboard.ts                   # UnitAggregates, TrendPoint, RiskDistribution
  alerts.ts                      # PersonnelAlert, StressRiskLevel, RiskFactor
  rbac.ts                        # UserRole, RoleConfig
```

### 1.2 Dependencies

```json
{
  "dependencies": {
    "next": "^14.x",
    "react": "^18.x",
    "react-dom": "^18.x",
    "recharts": "^2.x",
    "lucide-react": "^0.4xx",
    "clsx": "^2.x",
    "tailwind-merge": "^2.x"
  },
  "devDependencies": {
    "typescript": "^5.x",
    "@types/react": "^18.x",
    "@types/node": "^20.x",
    "tailwindcss": "^3.x",
    "postcss": "^8.x",
    "autoprefixer": "^10.x",
    "eslint": "^8.x",
    "eslint-config-next": "^14.x"
  }
}
```

No global state library (Redux/Zustand) is needed at this stage — scope doesn't justify it. If a future phase adds real-time alert polling or multi-user session sync, revisit.

### 1.3 State & Role Management

- **RBAC state:** a `RoleProvider` React Context in `/app/layout.tsx`, exposing `{ role, setRole }` where `role: 'commander' | 'welfare_officer'`. Backed by `useState`, optionally mirrored to `localStorage` client-side only (guard with `typeof window !== 'undefined'`).
- **Data fetching:** all mock reads go through async functions in `/lib/mock-data.ts` (e.g. `getUnitAggregates(): Promise<UnitAggregates[]>`) with an artificial `setTimeout` delay (300–600ms) so loading states are visibly exercised during development. These functions are the **single seam** to swap for real API calls later — components never import the mock arrays directly.
- **Alert status changes** (Acknowledge/Resolve) are held in local component state for now (no persistence) — call this out explicitly as a mock-stage limitation in code comments so Antigravity doesn't invent a fake backend for it.

---

## Phase 2: Data Contracts

### 2.1 `/types/dashboard.ts`

```typescript
export interface TrendPoint {
  date: string;               // ISO date, weekly granularity
  avgWorkloadScore: number;   // 0-10
  avgStressIndex: number;     // 0-100
}

export interface RiskDistribution {
  low: number;
  moderate: number;
  high: number;
  critical: number;
}

export interface UnitAggregates {
  unitId: string;
  unitName: string;
  personnelStrength: number;
  avgDutyHoursPerWeek: number;
  avgConsecutiveDutyDays: number;
  avgNightShiftsPerMonth: number;
  avgLeaveGapDays: number;
  annualLeaveUtilizationPct: number;              // derived: leaves taken / entitled
  operationalExposureIndex: 'Low' | 'Medium' | 'High';
  riskDistribution: RiskDistribution;
  trend: TrendPoint[];
  lastSyncedAt: string;                            // ISO timestamp
}
```

### 2.2 `/types/alerts.ts`

```typescript
export type StressRiskLevel = 'Low' | 'Moderate' | 'High' | 'Critical';

export interface RiskFactor {
  factor: string;         // human-readable, e.g. "Consecutive duty days 40% above unit average"
  contribution: number;   // relative weight 0-1, from model explainability output
}

export interface PersonnelAlert {
  alertId: string;
  serviceId: string;       // masked service identifier — see RBAC note in Phase 3
  unitId: string;
  role: string;            // duty role, e.g. "Section Commander", "Constable"
  stressRiskLevel: StressRiskLevel;
  riskScore: number;       // 0-100 model output
  riskExplanation: RiskFactor[];
  welfareRecommendation: string[];
  contributingMetrics: {
    dutyHoursPerWeek: number;
    consecutiveDutyDays: number;
    nightShiftsPerMonth: number;
    leaveGapDays: number;
    sleepHours: number;
    workLifeBalanceScore: number;   // 1-4 scale
  };
  flaggedAt: string;        // ISO timestamp
  status: 'New' | 'Acknowledged' | 'Under Review' | 'Resolved';
}
```

### 2.3 `/types/rbac.ts`

```typescript
export type UserRole = 'commander' | 'welfare_officer';

export interface RoleConfig {
  role: UserRole;
  label: string;
  canViewFullExplanation: boolean;   // welfare_officer only
  canViewServiceIdentity: boolean;   // welfare_officer only
  canEditStatus: boolean;            // both, but scoped differently
}
```

### 2.4 `/lib/mock-data.ts` (sample content)

```typescript
import { UnitAggregates } from '@/types/dashboard';
import { PersonnelAlert } from '@/types/alerts';

export const mockUnitAggregates: UnitAggregates[] = [
  {
    unitId: 'UNIT-07B',
    unitName: '7th Battalion, Bravo Company',
    personnelStrength: 214,
    avgDutyHoursPerWeek: 52.4,
    avgConsecutiveDutyDays: 9,
    avgNightShiftsPerMonth: 6,
    avgLeaveGapDays: 143,
    annualLeaveUtilizationPct: 41,
    operationalExposureIndex: 'High',
    riskDistribution: { low: 138, moderate: 51, high: 19, critical: 6 },
    trend: [
      { date: '2026-08-03', avgWorkloadScore: 6.1, avgStressIndex: 44 },
      { date: '2026-08-10', avgWorkloadScore: 6.5, avgStressIndex: 47 },
      { date: '2026-08-17', avgWorkloadScore: 7.0, avgStressIndex: 52 },
      { date: '2026-08-24', avgWorkloadScore: 6.8, avgStressIndex: 50 },
    ],
    lastSyncedAt: '2026-09-14T06:00:00Z',
  },
  {
    unitId: 'UNIT-12A',
    unitName: '12th Battalion, Alpha Company',
    personnelStrength: 189,
    avgDutyHoursPerWeek: 46.1,
    avgConsecutiveDutyDays: 5,
    avgNightShiftsPerMonth: 3,
    avgLeaveGapDays: 88,
    annualLeaveUtilizationPct: 67,
    operationalExposureIndex: 'Medium',
    riskDistribution: { low: 151, moderate: 29, high: 7, critical: 2 },
    trend: [
      { date: '2026-08-03', avgWorkloadScore: 4.8, avgStressIndex: 31 },
      { date: '2026-08-10', avgWorkloadScore: 4.9, avgStressIndex: 32 },
      { date: '2026-08-17', avgWorkloadScore: 5.1, avgStressIndex: 33 },
      { date: '2026-08-24', avgWorkloadScore: 4.7, avgStressIndex: 30 },
    ],
    lastSyncedAt: '2026-09-14T06:00:00Z',
  },
];

export const mockPersonnelAlerts: PersonnelAlert[] = [
  {
    alertId: 'ALT-10492',
    serviceId: 'CRPF-77213-B',
    unitId: 'UNIT-07B',
    role: 'Section Commander',
    stressRiskLevel: 'Critical',
    riskScore: 91,
    riskExplanation: [
      { factor: 'Consecutive duty days 40% above unit average', contribution: 0.34 },
      { factor: 'Leave gap of 187 days since last sanctioned leave', contribution: 0.29 },
      { factor: 'Average sleep 4.6 hrs/night over trailing 4 weeks', contribution: 0.22 },
      { factor: 'Three night shifts in the last 7 days', contribution: 0.15 },
    ],
    welfareRecommendation: [
      'Schedule welfare interview within 48 hours',
      'Recommend sanctioned leave block (5+ days) within 2 weeks',
      'Flag for rotation out of night-shift roster next cycle',
    ],
    contributingMetrics: {
      dutyHoursPerWeek: 61,
      consecutiveDutyDays: 14,
      nightShiftsPerMonth: 9,
      leaveGapDays: 187,
      sleepHours: 4.6,
      workLifeBalanceScore: 1,
    },
    flaggedAt: '2026-09-13T21:15:00Z',
    status: 'New',
  },
  {
    alertId: 'ALT-10488',
    serviceId: 'CRPF-51042-C',
    unitId: 'UNIT-07B',
    role: 'Constable',
    stressRiskLevel: 'High',
    riskScore: 74,
    riskExplanation: [
      { factor: 'Duty hours 22% above unit average', contribution: 0.31 },
      { factor: 'Work-life balance self-report at lowest band', contribution: 0.27 },
      { factor: 'Two transfers in the last 12 months', contribution: 0.19 },
    ],
    welfareRecommendation: [
      'Peer-support check-in this week',
      'Review transfer cadence with unit HR',
    ],
    contributingMetrics: {
      dutyHoursPerWeek: 58,
      consecutiveDutyDays: 8,
      nightShiftsPerMonth: 5,
      leaveGapDays: 96,
      sleepHours: 5.4,
      workLifeBalanceScore: 2,
    },
    flaggedAt: '2026-09-12T09:40:00Z',
    status: 'Acknowledged',
  },
];

// Simulated async fetchers — swap the body for a real API call later.
// Component code should never import the arrays above directly.
export async function getUnitAggregates(): Promise<UnitAggregates[]> {
  await new Promise((r) => setTimeout(r, 400));
  return mockUnitAggregates;
}

export async function getPersonnelAlerts(): Promise<PersonnelAlert[]> {
  await new Promise((r) => setTimeout(r, 500));
  return mockPersonnelAlerts;
}
```

---

## Phase 3: Component Architecture

### 3.1 Hierarchy

```
app/dashboard/page.tsx
 └─ DashboardLayout                         { role, children }
     ├─ Sidebar                             { role, activeRoute }
     ├─ Topbar                              { role, unitName, onRoleChange }
     │    └─ RoleToggle                     { role, onChange }
     ├─ MainMetricsRow                      { aggregates: UnitAggregates[] }
     │    └─ MetricCard × N                 { label, value, delta?, icon }
     ├─ RiskTrendChart                      { trend: TrendPoint[], unitName }
     ├─ UnitOverviewPanel                   { aggregates: UnitAggregates[] }
     ├─ AlertsTable                         { alerts: PersonnelAlert[], role, onSelectAlert }
     │    └─ RiskBadge                      { level: StressRiskLevel }
     └─ AlertDetailDrawer                   { alert: PersonnelAlert | null, role, onClose, onStatusChange }
```

### 3.2 Component Contracts

| Component | Props | Responsibility |
|---|---|---|
| `DashboardLayout` | `role: UserRole`, `children: ReactNode` | Page shell — sidebar + topbar + content grid |
| `Sidebar` | `role: UserRole`, `activeRoute: string` | Nav; item set may differ per role (e.g. Welfare Officer gets a "Case Log" item Commander doesn't) |
| `Topbar` | `role: UserRole`, `unitName: string`, `onRoleChange: (r: UserRole) => void` | Header bar, hosts `RoleToggle` |
| `RoleToggle` | `role: UserRole`, `onChange: (r: UserRole) => void` | Explicit Commander / Welfare Officer switch — this is a **view mode switch for demo/dev purposes**; production auth would derive role from login, not a UI toggle |
| `MainMetricsRow` | `aggregates: UnitAggregates[]` | Summary strip: total strength, active alerts, avg risk trend delta |
| `MetricCard` | `label: string`, `value: string \| number`, `delta?: number`, `icon: LucideIcon` | Single stat tile |
| `RiskTrendChart` | `trend: TrendPoint[]`, `unitName: string` | Recharts line chart, workload vs. stress index over time |
| `UnitOverviewPanel` | `aggregates: UnitAggregates[]` | Per-unit risk distribution bars, comparative view across units |
| `AlertsTable` | `alerts: PersonnelAlert[]`, `role: UserRole`, `onSelectAlert: (a: PersonnelAlert) => void` | Sortable/filterable alert list; **column set and cell content branch on `role`** (see 3.3) |
| `RiskBadge` | `level: StressRiskLevel` | Color-coded pill, maps level → Tailwind class via `/lib/constants.ts` |
| `AlertDetailDrawer` | `alert: PersonnelAlert \| null`, `role: UserRole`, `onClose: () => void`, `onStatusChange: (id: string, status: PersonnelAlert['status']) => void` | Slide-over detail; full `riskExplanation` + `welfareRecommendation` only when `role === 'welfare_officer'` |

### 3.3 RBAC Rendering Rule (important)

Role-based differences must be **conditional rendering in the component tree, not CSS-hidden**. If `AlertsTable` renders `serviceId` and `riskExplanation` into the DOM and merely hides them with `display: none` for the Commander role, that data is still readable via dev tools/inspect — a real privacy leak in a system handling personnel welfare data. Concretely:

- **Commander view:** `AlertsTable` shows unit, role, `stressRiskLevel`, `riskScore`, `status` — no `serviceId`, no `riskExplanation` detail. `AlertDetailDrawer` shows a summarized `welfareRecommendation` count only ("3 actions recommended"), not the list itself.
- **Welfare Officer view:** full row including masked-but-present `serviceId`, and the drawer renders full `riskExplanation` and `welfareRecommendation`.
- Encode this as a lookup table in `/lib/rbac.ts` (`ROLE_CONFIG: Record<UserRole, RoleConfig>`) that components read from, rather than scattering `role === 'commander'` checks throughout the tree.

---

## Phase 4: Execution Prompts

Feed these to Antigravity **in order**, one per turn, after it has read this file.

**Prompt 1 — Build the Layout Shell**
```
Using implementation.md as the source of truth, scaffold the Next.js App Router project structure exactly as defined in Phase 1.1. Install the dependencies from 1.2. Configure Tailwind with a high-contrast, dark, military-grade theme: near-black background, off-white primary text, a single desaturated accent (steel blue), sharp corners (minimal border-radius), and a monospace font for IDs/timestamps. Build DashboardLayout, Sidebar, Topbar, and a stub RoleToggle (no logic yet — just the visual switch). Do not build any data-driven components yet. Leave clear TODO comments where Phase 2 data will plug in.
```

**Prompt 2 — Implement the Dashboard Data Contracts & Mock Data**
```
Implement /types/dashboard.ts, /types/alerts.ts, and /types/rbac.ts exactly as specified in implementation.md Phase 2. Then implement /lib/mock-data.ts with the sample UnitAggregates and PersonnelAlert arrays given there, plus the async getUnitAggregates() and getPersonnelAlerts() functions with simulated delay. Do not build UI components yet — just the typed data layer, and confirm it compiles with `tsc --noEmit`.
```

**Prompt 3 — Build MainMetricsRow and RiskTrendChart**
```
Build MainMetricsRow, MetricCard, and RiskTrendChart per the props contracts in implementation.md Phase 3.2. Use Recharts for RiskTrendChart (LineChart, two lines: avgWorkloadScore and avgStressIndex against date). Wire these into the dashboard page using getUnitAggregates() from lib/mock-data.ts, with a loading skeleton while the promise resolves. Use lucide-react icons on MetricCard (e.g. Users, Activity, TrendingUp, ShieldAlert).
```

**Prompt 4 — Build AlertsTable, RiskBadge, and AlertDetailDrawer with RBAC**
```
Implement /lib/rbac.ts with the ROLE_CONFIG lookup described in implementation.md 3.3. Build RiskBadge (color per risk level — use amber/orange/red tones, never rely on color alone, pair with a short label). Build AlertsTable and AlertDetailDrawer, strictly following the RBAC rendering rule in 3.3: role-gated fields must be conditionally rendered, not CSS-hidden. Wire both into the dashboard page using getPersonnelAlerts(), with the RoleToggle from Prompt 1 now live and actually switching which fields render.
```

**Prompt 5 — RBAC Context, Polish, and Empty/Loading States**
```
Wrap the app in a RoleProvider (React Context) in app/layout.tsx as described in implementation.md 1.3, replacing the local RoleToggle state from Prompt 4 with context-driven state. Add UnitOverviewPanel for cross-unit comparison. Add loading.tsx skeleton states, an EmptyState component for zero-alert scenarios, and make the layout responsive down to tablet width. Do a pass for visual consistency against the design guidelines in implementation.md (spacing, contrast, iconography).
```

---

## Design Guidelines Reference

- **Palette:** near-black base (`#0B0E11`–`#12161B` range), off-white text (`#E8EAED`), single steel-blue accent for interactive elements, desaturated amber/orange/red reserved *only* for risk signaling — never used decoratively elsewhere so risk states stay visually distinct.
- **Risk color + label pairing (never color alone):** Low → green + "Low", Moderate → amber + "Moderate", High → orange + "High", Critical → red + "Critical", each with an icon (e.g. `ShieldCheck`, `AlertTriangle`, `AlertOctagon`) for colorblind-safe reading.
- **Typography:** system sans for body/UI copy; monospace for service IDs, unit codes, and timestamps to reinforce an operational/technical register.
- **Density:** favor information density over whitespace-heavy consumer-app styling — this is an operations tool, not a marketing page. Tables and metric rows should read like a command console.
- **Shape language:** minimal border-radius (2–4px), thin 1px borders over heavy shadows, no gradients.
- **Icons:** lucide-react throughout for consistency — `ShieldAlert`, `Users`, `Activity`, `TrendingUp`, `Clock`, `Moon` (night shifts), `CalendarX` (leave gap).

---

## Appendix: Data Lineage (for engineering context, not for Antigravity to build against)

- `FINAL_MAIN_STRESS_DATASET.csv` — main model development dataset (EDA, feature engineering, train/test split, training, cross-validation, model selection). Synthetically augmented prototype data, not real personnel records.
- `D2_cleaned.csv` — independent external validation set only. Never merged with the main dataset; never used for training, tuning, feature selection, or model selection. Used exclusively, after the model is finalized on the main dataset, to check generalization.
- The mock schemas above intentionally use only the feature subset both datasets share (plus training-only operational fields marked as enrichment), so the frontend contract is stable once the real model output replaces `/lib/mock-data.ts`.
