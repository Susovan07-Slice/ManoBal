# Frontend UI/UX Audit Report: ManoBal Mobile App

**Scope:** `PS 26186_app` (Jawan Mobile Web App)
**Date:** September 28, 2026

---

## 1. Application-wide Design System
The application utilizes a **Military/Tactical Glassmorphism** design language. It is optimized for mobile screens and relies heavily on scenic, full-screen background images (e.g., `login-bg.png`). The primary visual theme combines translucent dark "glass" overlays with stark white or heavily contrasted dark text, accented with a vibrant teal (`mb-accent`).

## 2. Navigation
- **TopHeader (`TopHeader.tsx`):** 
  - Sticky top alignment (`sticky top-0 z-40`), height of 80px (`h-20`).
  - Dark glass background (`bg-black/25 backdrop-blur-2xl`) with a subtle white bottom border (`border-b border-white/10`) and drop shadow.
  - Left side: ManoBal logo (scaled in an 80x80px container) and the page title.
  - Right side: User information aligned right (username, and a pill-shaped battalion/location badge in emerald green) alongside a minimalist logout button (`bg-white/10 hover:bg-white/20`).
- **BottomTabBar (`BottomTabBar.tsx`):**
  - Floating pill-shaped navigation bar, absolute positioned near the bottom (`bottom-5`).
  - Dimensions: Fixed max-width of 320px, height of 60px.
  - Background: `bg-black/40 backdrop-blur-2xl` with a thin border (`border-white/15`) and rounded corners (`rounded-2xl`), featuring a prominent shadow.
  - Contains three tabs: **Home**, **Assessment**, **Trends**.
  - Active state: Icon scales up (`scale-110`), text turns bright white (`text-white/90`), and a glowing teal dot (`bg-mb-accent`) appears below the label. Inactive state: Faded text/icons (`text-white/40`).

## 3. Layout & Spacing
- **Mobile-First Layout:** The app is constrained within a mobile wrapper (`MobileWrapper.tsx`), utilizing `max-w-md w-full mx-auto` to maintain a phone-like aspect ratio and layout even on larger screens.
- **Grids & Spacing:** Extensive use of CSS grids for forms (`grid-cols-2`) with 12px gaps (`gap-3`). Padding on main containers is typically 20px (`p-5`).
- **Positioning:** Relies heavily on absolute positioning for fixed elements like the background (`absolute inset-0 z-20 overflow-y-auto`), the floating SOS button, and the bottom tab bar.

## 4. Colors & Backgrounds
Defined centrally in `app/globals.css` and via Tailwind classes:
- **Primary Backgrounds:** Translucent dark glass (`bg-black/40`, `bg-black/25`).
- **Military Core:** `military-900` (#0a110e), `military-800` (#101c18), `military-700` (#1e332c), `olive-500` (#4a5c40).
- **Accents:** 
  - Teal / `mb-accent`: `#00A896` (Primary action color)
  - Saffron / `mb-saffron`: `#D98A2B` (Warning/Attention)
  - Green / `mb-green`: `#3F6B47` (Success)
  - Danger / `mb-danger`: `#D94A4A` (Errors/Alerts)
- **Text Palette:** `mb-text-primary` (#000000), `mb-text-secondary` (#1a202c), `mb-text-muted` (#4a5568).
- **Glass Borders:** Subtle white transparency (`rgba(255, 255, 255, 0.12)`).

## 5. Typography
- **Font Family:** System UI sans-serif stack (`ui-sans-serif, system-ui, -apple-system, ...`).
- **Hierarchy:** 
  - Main titles: `text-2xl font-bold tracking-wider`.
  - Subtitles/Labels: Small, uppercase, monospace, and widely tracked (`text-xs uppercase tracking-widest font-mono font-semibold`).
  - Body/Inputs: Clean, readable `text-sm font-medium`.
  - Bottom Tabs: Extremely small labels (`text-[10px] tracking-wide`).

## 6. Cards & Containers
- **Shapes & Radii:** Extensive use of highly rounded corners (`rounded-xl` / 12px, `rounded-2xl` / 16px).
- **Shadows & Blurs:** Heavy backdrop filters (`backdrop-blur-2xl`) combined with deep drop shadows (e.g., `shadow-[0_8px_40px_rgba(0,0,0,0.25)]`).
- **Borders:** Thin, barely visible borders on containers to enhance the glassmorphism effect (`border-white/10`, `border-white/15`).

## 7. Buttons & Controls
- **Standard Action Buttons:** Full width, rounded-lg (`rounded-lg`), bold text (`py-3 font-bold`), colored in solid Teal (`bg-mb-accent`) with dark text (`text-mb-text-dark`).
- **SOS / Welfare Support Button (`SosButton.tsx`):**
  - Floating button placed above the bottom tab bar (`bottom-20 right-4`).
  - Default state: Teal box with a subtle shadow (`bg-[#00a896]`), vertically stacked text, and a `HeartPulse` icon.
  - Active/Sent state: Transitions into a white button with an emerald green border (`border-2 border-emerald-500 text-emerald-600`) and a checkmark icon. It utilizes an active scale down interaction (`active:scale-95`).
- **Rating Slider (`RatingSlider.tsx`):** Custom CSS slider in `globals.css` featuring a large white circular thumb (20x20px) with a 2px teal border. The track is dark and semi-transparent.

## 8. Forms & Inputs
- **Text Inputs & Selects:** 
  - Background: Slightly opaque white (`bg-white/90`).
  - Border: Gray border (`border-gray-300`) that changes to teal on focus (`focus:border-mb-accent`).
  - Text: Dark gray text (`text-gray-900`) with medium font weight, padding (`px-3 py-2.5`), and rounded edges (`rounded-lg`).
- **Labels:** Strictly uppercase, small, and bold (`text-xs uppercase tracking-wider font-bold`).
- **Icons in Inputs:** Left-aligned absolute icons (e.g., Lucide `User`, `Lock`) wrapped inside a relative container.
- **SearchableSelect:** A custom combobox component for choosing complex data like Battalions or Locations.

## 9. Dashboard
- Layout is constructed via `HomeScreen.tsx`. 
- Incorporates multiple block-level components stacked vertically within the `MobileWrapper`.
- Major elements include a fast check-in module (`CheckInForm.tsx`), pending surveys (`SurveyCard.tsx`), and a top-level summary of trends (`TrendSummaryCard.tsx`).

## 10. Assessment/Welfare Features
- **Survey Interface:** Utilizes `SurveyQuestion.tsx` for prompt display, paired with `RatingSlider.tsx` for capturing responses.
- **Progress Tracking:** Managed visually by a dot-indicator component (`ProgressDots.tsx`).
- **Welfare Support Sheet (`WelfareSupportSheet.tsx`):** An overlay/sheet component acting as a confirmation modal when the SOS button is triggered.

## 11. Charts & Data Visualization
- **Risk Calendar:** `RiskCalendarHeatmap.tsx` implements a heatmap visualization to plot historical stress/risk data across a calendar view.
- **Trend Charts:** `TrendChart.tsx` leverages the `recharts` library for line/area visualizations of wellness trends over time.

## 12. Individual Screens/Pages
- **Login (`/login`):** Centered logo, primary brand name, and subtitle over a full-screen background image. Contains the login form and a distinct "Quick Demo Access" fallback button styled in a dark slate.
- **Sign Up (`/signup`):** A lengthy, scrollable form utilizing two-column grids for compact data entry (Age, Gender, Department, Rank). It features an informational "Role Policy Notice" box at the bottom.
- **Trends (`/trends`):** dedicated to rendering the `TrendChart` and `RiskCalendarHeatmap`.
- **Assessment (`/assessment`):** Dedicated workflow for completing wellness surveys.

## 13. Images, Icons & Decorative Elements
- **Iconography:** Universally utilizes the `lucide-react` library (e.g., `Shield`, `Lock`, `User`, `HeartPulse`, `Building2`, `MapPin`, `LogOut`).
- **Images:** Relies heavily on `/logo.png` for branding (often featuring a drop-shadow) and `/login-bg.png` for atmospheric depth.
- **Badges:** Small pill-shaped badges (e.g., for battalion location) use thin borders and deeply tinted backgrounds (e.g., `bg-emerald-950/50 border-emerald-500/30 text-emerald-400/90`).

## 14. Responsive Behavior
- **Fixed Width paradigm:** Uses `max-w-md` (`~448px`) across the application to force a mobile-app experience, centering the content on wider screens. 
- Bottom navigation and floating action buttons are fixed relative to the viewport/container.

## 15. Animations & Interactions
- **Micro-interactions:** 
  - Standard transition class (`transition-all duration-300`) applied universally to buttons and links.
  - Hover states on slider thumbs expand the thumb size (`transform: scale(1.15)`).
  - Bottom tab icons scale up on active (`scale-110`).
- **Slide-In Alerts:** Notifications utilize Tailwind animations (`animate-in slide-in-from-top-4`) to gracefully enter the screen.

## 16. Frontend Technologies/Libraries
- **Framework:** Next.js (version 16.3.5) with React 19 App Router.
- **Styling:** Tailwind CSS v4 (utilizing the new `@import "tailwindcss";` and `@theme` API syntax).
- **Components:** Uses `clsx` and `tailwind-merge` for dynamic class assignment.
- **Charting:** `recharts` (version 3.10.1).
- **Icons:** `lucide-react`.

## 17. Component Inventory
- **UI Base Components:** `Button.tsx`, `Card.tsx`, `ConfirmSheet.tsx`, `ProgressDots.tsx`, `RatingSlider.tsx`, `SearchableSelect.tsx`.
- **Layout Shell:** `BottomTabBar.tsx`, `MobileWrapper.tsx`, `SosButton.tsx`, `TopHeader.tsx`.
- **Screen Fragments:** `CheckInForm.tsx`, `HomeScreen.tsx`, `RiskCalendarHeatmap.tsx`, `SurveyCard.tsx`, `SurveyQuestion.tsx`, `TrendChart.tsx`, `TrendSummaryCard.tsx`, `WelfareSupportSheet.tsx`.
