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
        // 1. Background Colors (60% of UI)
        background: '#F1F7F4',        // Soft Mint main app background
        surface: '#FAFAFC',           // Soft off-white for elevated surfaces, cards, modals (No pure #FFFFFF)
        surfaceHighlight: '#E8F0EC',  // Lighter tint of background for subtle rows/containers
        surfaceMuted: '#E2EBE5',
        surfaceBorder: '#D5E2D9',     // Accessible soft border

        // 2. Typography (Text Colors) - No pure black (#000000)
        textPrimary: '#2D3748',       // Soft dark slate gray (primary headings & body)
        textSecondary: '#64748B',     // Lighter muted gray (captions & placeholders)
        textMuted: '#8292A2',

        // 3. Secondary & Accent Colors (30% and 10% of UI)
        accent: {
          DEFAULT: '#7BA083',         // Muted Sage (Primary brand color)
          hover: '#698D71',
          light: 'rgba(123, 160, 131, 0.12)', // Subtle highlight & secondary background
          subtle: 'rgba(123, 160, 131, 0.22)',
          border: 'rgba(123, 160, 131, 0.38)',
        },

        // Muted Sage extended palette
        sage: {
          50: '#F4F7F5',
          100: '#E6EFE8',
          200: '#D0E1D4',
          300: '#B5CFBB',
          400: '#97BA9E',
          500: '#7BA083', // Muted Sage
          600: '#64886C',
          700: '#4F6E56',
          800: '#3D5443',
          900: '#2C3E31',
        },

        // 4. Low-Stress Anxiety-Safe Risk & Alert Colors (No harsh or saturated reds)
        risk: {
          low: '#60987A',      // Calming sage green
          moderate: '#D99B5C', // Soft warm amber
          high: '#CB7A5C',     // Soft coral
          critical: '#C26D6D', // Muted dusty rose
        },

        alert: {
          rose: '#C26D6D',
          roseBg: '#FAF0F0',
          roseBorder: '#E8B4B4',
          roseText: '#964747',
          coral: '#CB7A5C',
          coralBg: '#FDF2EC',
          coralBorder: '#F1C5B3',
          coralText: '#8F4B33',
          amber: '#D99B5C',
          amberBg: '#FDF6EE',
          amberBorder: '#F3D2AE',
          amberText: '#8E5B23',
          sage: '#60987A',
          sageBg: '#EEF6F2',
          sageBorder: '#BBD9C7',
          sageText: '#2D6346',
          slate: '#5B88A5',
          slateBg: '#EEF4F8',
          slateBorder: '#BCD3E3',
          slateText: '#3E6580',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains-mono)', 'monospace'],
      },
      borderRadius: {
        none: '0px',
        sm: '4px',
        DEFAULT: '8px',
        md: '10px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
        '3xl': '24px',
        full: '9999px',
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(45, 55, 72, 0.05), 0 1px 2px -1px rgba(45, 55, 72, 0.03)',
        elevated: '0 4px 16px -2px rgba(45, 55, 72, 0.07), 0 2px 6px -1px rgba(45, 55, 72, 0.04)',
      },
    },
  },
  plugins: [],
};
export default config;
