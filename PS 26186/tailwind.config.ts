import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0E11', // Near-black base
        surface: '#12161B',    // Slightly lighter for cards
        surfaceHighlight: '#1A1F26',
        textPrimary: '#E8EAED', // Off-white
        textSecondary: '#9AA0A6',
        accent: '#4A6D8C', // Steel blue interactive elements
        // Risk colors (reserved only for signaling)
        risk: {
          low: '#10B981',      // Emerald/Green
          moderate: '#F59E0B', // Amber
          high: '#F97316',     // Orange
          critical: '#EF4444', // Red
        }
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains-mono)', 'monospace'],
      },
      borderRadius: {
        none: '0px',
        sm: '2px',
        DEFAULT: '4px',
        md: '6px',
        lg: '8px',
        full: '9999px',
      },
      boxShadow: {
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
      }
    },
  },
  plugins: [],
};
export default config;
