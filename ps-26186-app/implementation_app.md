# implementation.md
## Soldier Wellness & Self-Assessment Application

**Purpose:** Architectural blueprint for an AI coding agent (Antigravity) to scaffold a Next.js frontend that *simulates* a native mobile app inside a web build. No application code here — folder structure, data contracts, component architecture, and sequential build prompts only.

**Relationship to the Commander & Welfare Officer Dashboard:** this app is the data-entry side of the same stress-monitoring system — soldiers log check-ins and surveys here; a welfare officer/commander would eventually see aggregated outputs on the other dashboard. The two are separate frontends against a shared conceptual backend/model; this document only covers the soldier-facing app.

---

## Phase 1: Project Setup & State

### 1.1 Folder Structure

```
/app
  layout.tsx                    # Root layout — wraps everything in MobileWrapper, hosts persistent SosButton
  globals.css                   # Tailwind base + dark/slate design tokens
  /(tabs)
    layout.tsx                  # Tab shell — TopHeader + MainScrollArea + BottomTabBar, persists across tab routes
    page.tsx                    # Home tab — today's summary
    /check-in
      page.tsx                  # Daily Check-In tab
    /assessment
      page.tsx                  # Survey tab
    /trends
      page.tsx                  # Personal Trends tab

/components
  /layout
    MobileWrapper.tsx           # Enforces the phone-frame constraint
    TopHeader.tsx
    BottomTabBar.tsx
    SosButton.tsx                # Always-mounted, floats above tab content
  /screens
    HomeScreen.tsx
    CheckInForm.tsx
    SurveyCard.tsx
    SurveyQuestion.tsx
    TrendChart.tsx
    TrendSummaryCard.tsx
  /ui
    Button.tsx
    Card.tsx
    RatingSlider.tsx             # Large touch-friendly 1-5 selector for mood/fatigue/workload
    ProgressDots.tsx             # Survey progress indicator
    ConfirmSheet.tsx             # Bottom-sheet confirmation (used by SosButton and CheckInForm submit)

/lib
  mock-data.ts
  constants.ts                  # Mood scale labels, color tokens, tab config
  utils.ts                      # cn() helper, date formatting, score-band mapping

/types
  checkin.ts
  survey.ts
  trends.ts
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

Keep dependencies minimal — this is a single-user, low-friction app. No auth library, no state manager beyond React Context; skip animation libraries unless a later polish pass specifically asks for one.

### 1.3 `MobileWrapper` and State

`MobileWrapper` is the one component every screen renders inside, and it's what makes a web build read as a phone app:

```tsx
// components/layout/MobileWrapper.tsx (structure only)
<div className="max-w-[420px] mx-auto min-h-screen bg-background relative shadow-2xl overflow-hidden">
  {children}
</div>
```

Rules for anything that overlays content (SOS confirmation sheet, toasts, modals): they must be positioned `absolute` relative to this wrapper, **never `fixed` to the viewport** — a `fixed` overlay breaks out of the phone frame on a desktop browser and defeats the simulation.

**State, no RBAC needed here** (single role: the soldier using their own device):
- `CheckInDraft` — local state in `CheckInForm` for the in-progress entry before submit.
- Survey progress — local state in `SurveyCard`: current question index, collected answers, computed score on completion.
- `SosButton` — internal two-step state machine: `idle → confirming → sent`. A large always-visible button is exactly the kind of thing that gets tapped by accident in a pocket or during handling, so it requires a deliberate second confirmation (`ConfirmSheet`) before firing — this is a UX safety requirement, not just a nice-to-have.
- Trends and history reads go through async mock fetchers in `/lib/mock-data.ts` (same pattern as the Commander dashboard) — the single seam for swapping in a real API later.

**Engineering note to carry into Phase 4:** at this mock stage, `SosButton` firing is a **UI simulation only** — it should visibly confirm "Welfare officer notified" in the mock state, but the prompts must make clear to Antigravity that no real alert is sent until this is wired to an actual backend/notification service. Don't let the agent quietly stub in a fake "success" that could be mistaken for a working safety feature later.

---

## Phase 2: Data Contracts

### 2.1 `/types/checkin.ts`

```typescript
export interface DailyCheckIn {
  checkInId: string;
  date: string;                        // ISO date
  moodScore: 1 | 2 | 3 | 4 | 5;         // 1 = very low, 5 = very good
  sleepHours: number;
  physicalFatigueLevel: 1 | 2 | 3 | 4 | 5;
  operationalWorkloadLevel: 1 | 2 | 3 | 4 | 5;
  note?: string;                        // optional, short free text
  submittedAt: string;                  // ISO timestamp
}
```

### 2.2 `/types/survey.ts`

> **Note for the engineering team (not for Antigravity to treat as final copy):** the field names below model a standard 9-item, 0–3-frequency-scale depression screening survey (PHQ-9-style), including its well-known final item that screens for thoughts of self-harm. The `promptSummary` values in the mock data are **paraphrased placeholders for UI layout only** — source the exact validated item wording and official severity-band cutoffs from a licensed clinical reference before this ships, rather than hardcoding text generated here.

```typescript
export type SurveyType = 'PHQ9_STYLE';

export interface SurveyQuestion {
  id: string;
  category: string;          // paraphrased category label, e.g. "Sleep difficulty"
  promptSummary: string;     // placeholder phrasing for dev/layout — replace with licensed text
  sensitive?: boolean;       // true only for the self-harm screening item
}

export interface SurveyAnswer {
  questionId: string;
  value: 0 | 1 | 2 | 3;      // "not at all" → "nearly every day"
}

export interface AssessmentSurvey {
  surveyId: string;
  type: SurveyType;
  date: string;
  answers: SurveyAnswer[];
  totalScore: number;                                                      // sum of values, 0-27
  severityBand: 'Minimal' | 'Mild' | 'Moderate' | 'Moderately Severe' | 'Severe';
  flaggedForImmediateReview: boolean;   // true if the sensitive item scored > 0
  submittedAt: string;
}
```

**Sensitive-item handling rule:** if the sensitive item's answer value is greater than 0, the UI must immediately surface support resources and a direct path to `SosButton` *inline in the survey flow itself*, not just at the end after scoring. Don't let a distressed answer sit unacknowledged until a results screen.

### 2.3 `/types/trends.ts`

```typescript
export interface TrendDay {
  date: string;
  stressIndex: number;   // 0-100, derived from check-in + survey signals
  sleepHours: number;
  moodScore: number;     // 1-5
}

export interface PersonalTrend {
  last7Days: TrendDay[];
  averageStressIndex: number;
  averageSleepHours: number;
  trendDirection: 'improving' | 'stable' | 'worsening';
}
```

### 2.4 `/lib/mock-data.ts` (sample content)

```typescript
import { DailyCheckIn } from '@/types/checkin';
import { AssessmentSurvey, SurveyQuestion } from '@/types/survey';
import { PersonalTrend } from '@/types/trends';

export const mockCheckIns: DailyCheckIn[] = [
  {
    checkInId: 'CHK-2026-09-14',
    date: '2026-09-14',
    moodScore: 3,
    sleepHours: 5.5,
    physicalFatigueLevel: 4,
    operationalWorkloadLevel: 4,
    submittedAt: '2026-09-14T07:05:00Z',
  },
  {
    checkInId: 'CHK-2026-09-13',
    date: '2026-09-13',
    moodScore: 2,
    sleepHours: 4.8,
    physicalFatigueLevel: 5,
    operationalWorkloadLevel: 5,
    note: 'Long patrol, short turnaround before next shift.',
    submittedAt: '2026-09-13T22:40:00Z',
  },
];

export const surveyQuestions: SurveyQuestion[] = [
  { id: 'q1', category: 'Interest or pleasure in activities', promptSummary: 'Little interest or pleasure in doing things' },
  { id: 'q2', category: 'Low mood', promptSummary: 'Feeling down or discouraged' },
  { id: 'q3', category: 'Sleep difficulty', promptSummary: 'Trouble falling or staying asleep, or sleeping too much' },
  { id: 'q4', category: 'Fatigue', promptSummary: 'Feeling tired or having little energy' },
  { id: 'q5', category: 'Appetite change', promptSummary: 'Poor appetite or overeating' },
  { id: 'q6', category: 'Self-worth', promptSummary: 'Feeling bad about yourself, or that you are letting people down' },
  { id: 'q7', category: 'Concentration', promptSummary: 'Trouble concentrating on tasks' },
  { id: 'q8', category: 'Psychomotor change', promptSummary: 'Moving or speaking noticeably slower, or the opposite — restless' },
  { id: 'q9', category: 'Self-harm screening', promptSummary: 'Thoughts that you would be better off not around, or of harming yourself', sensitive: true },
];

export const mockSurvey: AssessmentSurvey = {
  surveyId: 'SUR-2026-09-10',
  type: 'PHQ9_STYLE',
  date: '2026-09-10',
  answers: [
    { questionId: 'q1', value: 1 }, { questionId: 'q2', value: 1 }, { questionId: 'q3', value: 2 },
    { questionId: 'q4', value: 2 }, { questionId: 'q5', value: 0 }, { questionId: 'q6', value: 1 },
    { questionId: 'q7', value: 1 }, { questionId: 'q8', value: 0 }, { questionId: 'q9', value: 0 },
  ],
  totalScore: 8,
  severityBand: 'Mild',
  flaggedForImmediateReview: false,
  submittedAt: '2026-09-10T20:15:00Z',
};

export const mockTrend: PersonalTrend = {
  last7Days: [
    { date: '2026-09-08', stressIndex: 38, sleepHours: 6.2, moodScore: 4 },
    { date: '2026-09-09', stressIndex: 41, sleepHours: 5.9, moodScore: 3 },
    { date: '2026-09-10', stressIndex: 47, sleepHours: 5.3, moodScore: 3 },
    { date: '2026-09-11', stressIndex: 52, sleepHours: 5.0, moodScore: 3 },
    { date: '2026-09-12', stressIndex: 55, sleepHours: 4.9, moodScore: 2 },
    { date: '2026-09-13', stressIndex: 58, sleepHours: 4.8, moodScore: 2 },
    { date: '2026-09-14', stressIndex: 53, sleepHours: 5.5, moodScore: 3 },
  ],
  averageStressIndex: 49,
  averageSleepHours: 5.4,
  trendDirection: 'worsening',
};

// Simulated async fetchers — swap the body for a real API call later.
export async function getRecentCheckIns(): Promise<DailyCheckIn[]> {
  await new Promise((r) => setTimeout(r, 300));
  return mockCheckIns;
}

export async function getSurveyQuestions(): Promise<SurveyQuestion[]> {
  await new Promise((r) => setTimeout(r, 200));
  return surveyQuestions;
}

export async function getPersonalTrend(): Promise<PersonalTrend> {
  await new Promise((r) => setTimeout(r, 350));
  return mockTrend;
}
```

*(Note the mock survey's sensitive item is deliberately scored `0` — sample/seed data for a screen that may surface crisis-support UI shouldn't itself depict an endorsed self-harm item.)*

---

## Phase 3: Component Architecture

### 3.1 Hierarchy

```
app/layout.tsx
 └─ MobileWrapper
     ├─ SosButton                          { onTrigger }                — always mounted, floats top-level
     └─ (tabs)/layout.tsx
         ├─ TopHeader                      { title, showBack? }
         ├─ MainScrollArea                 { children }
         │    ├─ HomeScreen                { checkIns, trend }
         │    │    └─ TrendSummaryCard      { trend: PersonalTrend }
         │    ├─ CheckInForm               { onSubmit }
         │    │    └─ RatingSlider × 3      { label, value, onChange }
         │    ├─ SurveyCard                { questions, onComplete }
         │    │    ├─ ProgressDots          { current, total }
         │    │    └─ SurveyQuestion × N    { question, value, onAnswer }
         │    └─ TrendChart                { data: TrendDay[] }
         └─ BottomTabBar                   { activeTab, onTabChange }   — Home / Check-In / Assessment / Trends
```

### 3.2 Component Contracts

| Component | Props | Responsibility |
|---|---|---|
| `MobileWrapper` | `children: ReactNode` | Enforces the phone-frame constraint; the one place that class string lives |
| `SosButton` | `onTrigger: () => void` | Persistent floating button, two-step confirm via `ConfirmSheet`, shows "notified" state after confirm |
| `TopHeader` | `title: string`, `showBack?: boolean` | Screen title bar within the tab shell |
| `BottomTabBar` | `activeTab: TabKey`, `onTabChange: (t: TabKey) => void` | 4 fixed tabs, large icon+label touch targets |
| `HomeScreen` | `checkIns: DailyCheckIn[]`, `trend: PersonalTrend` | Landing view — today's status + quick links into Check-In/Assessment |
| `TrendSummaryCard` | `trend: PersonalTrend` | One-glance stress/sleep summary with direction indicator |
| `CheckInForm` | `onSubmit: (c: Omit<DailyCheckIn,'checkInId'\|'submittedAt'>) => void` | Mood/sleep/fatigue/workload entry, mostly slider taps, minimal typing |
| `RatingSlider` | `label: string`, `value: number`, `onChange: (v: number) => void`, `min`, `max` | Large touch-friendly 1-5 (or hour) selector |
| `SurveyCard` | `questions: SurveyQuestion[]`, `onComplete: (a: SurveyAnswer[]) => void` | One-question-at-a-time flow; surfaces support resources inline the moment the sensitive item is answered > 0 |
| `SurveyQuestion` | `question: SurveyQuestion`, `value: number \| null`, `onAnswer: (v: number) => void` | Single question, 4-option 0-3 tap scale |
| `ProgressDots` | `current: number`, `total: number` | Visual survey progress |
| `TrendChart` | `data: TrendDay[]` | Recharts line chart — stressIndex and sleepHours over the last 7 days |
| `ConfirmSheet` | `open: boolean`, `message: string`, `onConfirm`, `onCancel` | Bottom-sheet confirm pattern, reused by `SosButton` and check-in submit |

---

## Phase 4: Execution Prompts

Feed these to Antigravity **in order**, one per turn, after it has read this file.

**Prompt 1 — Build the Mobile Wrapper and Navigation**
```
Using implementation.md as the source of truth, scaffold the Next.js App Router structure from Phase 1.1, including the (tabs) route group. Build MobileWrapper exactly with the class string given in 1.3 — every screen must render inside it, and nothing in the app should use position: fixed relative to the viewport (use absolute positioning relative to MobileWrapper instead). Build TopHeader and BottomTabBar with 4 tabs (Home, Check-In, Assessment, Trends), large touch targets (minimum 44x44px), and a dark, low-glare slate/navy theme with soft rounded corners — this must feel calm, not clinical or alarming. Add a stub SosButton (visual only, no logic yet) that floats persistently above tab content but stays within the wrapper bounds. Do not build any data-driven screens yet.
```

**Prompt 2 — Build the Data Contracts & Mock State**
```
Implement /types/checkin.ts, /types/survey.ts, and /types/trends.ts exactly as specified in implementation.md Phase 2. Then implement /lib/mock-data.ts with the sample data and async fetchers given there — including the sensitive-item flag on the survey's final question. Keep the mock survey's sensitive item answered at 0 as specified; don't change the seed data. Confirm it compiles with `tsc --noEmit`. No UI work yet.
```

**Prompt 3 — Build the Daily Check-In & Survey UI**
```
Build CheckInForm with RatingSlider for mood, sleep, fatigue, and workload — favor large tap targets over typing, per implementation.md's design guidelines for use after exhausting shifts. Build SurveyCard, SurveyQuestion, and ProgressDots for the one-question-at-a-time assessment flow. Implement the sensitive-item handling rule from Phase 2.2: the moment the self-harm screening question is answered with a value greater than 0, immediately show inline support resources and a direct path to the SOS flow, before the survey proceeds — do not wait until a results screen. Wire both forms into their tab routes using the mock fetchers from Prompt 2.
```

**Prompt 4 — Build the Personal Dashboard & SOS Button**
```
Build HomeScreen with TrendSummaryCard and TrendChart (Recharts, stressIndex and sleepHours over data.last7Days) using getPersonalTrend(). Make SosButton fully functional per implementation.md 1.3 and 3.2: tap opens ConfirmSheet, confirming moves it to a visibly distinct "sent" state reading something like "Welfare officer notified." Add a clear code comment (and, if there's a dev/debug panel, a visible note) that this is a UI simulation only and not wired to a real alerting backend yet. Add loading and empty states across all four tabs and do a final pass against the design guidelines (contrast, spacing, icon consistency via lucide-react).
```

---

## Design Guidelines Reference

- **Palette:** dark, low-glare slate/navy (e.g. `#141A22` base, `#1C2530` cards) — noticeably softer than a command-console theme; this app is used by an exhausted person winding down, not running an operation.
- **Reserve high-contrast warm color for one thing only:** the `SosButton`. Everywhere else stays muted (soft teal/blue accents) so the one urgent-color element is unmistakable when it matters.
- **Touch targets:** minimum 44×44px, generous spacing between tappable elements, sliders and tap-scales preferred over free text entry.
- **Shape language:** soft rounded corners (`rounded-xl`+), gentle shadows — calming, not sharp/military like the companion Commander dashboard.
- **Motion:** subtle, slow transitions only — nothing jarring or attention-grabbing except the SOS confirm state itself.
- **Icons:** lucide-react — `Moon` (sleep), `Battery`/`BatteryLow` (fatigue), `Activity` (workload), `Smile`/`Frown`/`Meh` (mood), `HeartPulse` or `LifeBuoy` (SOS), `TrendingUp`/`TrendingDown` (trend direction).
- **Copy tone:** plain, warm, non-clinical language throughout — this is talking to a tired person, not filling out a form for HR.