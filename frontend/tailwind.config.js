/** @type {import('tailwindcss').Config} */
import animate from 'tailwindcss-animate';

export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  safelist: [
    // Pipeline column dots / accents (new palette)
    'bg-zinc-400',
    'bg-blue-500',
    'bg-purple-500',
    'bg-amber-500',
    'bg-pink-500',
    'bg-emerald-500',
    'bg-indigo-500',
    'bg-red-500',
    'bg-orange-500',
    // Legacy mapping kept (config returns "bg-blue-600" etc — we still parse)
    'bg-gray-600',
    'bg-blue-600',
    'bg-purple-600',
    'bg-yellow-600',
    'bg-pink-600',
    'bg-green-600',
    'bg-indigo-600',
    'bg-red-600',
    'bg-orange-600',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: { '2xl': '1400px' },
    },
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        // Legacy semantic colors (kept for backward compat)
        backlog: '#a1a1aa',
        ready: '#3b82f6',
        'in-progress': '#f59e0b',
        review: '#8b5cf6',
        qa: '#ec4899',
        done: '#10b981',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
      },
      keyframes: {
        'accordion-down': {
          from: { height: 0 },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: 0 },
        },
        'fade-in': {
          from: { opacity: 0, transform: 'translateY(2px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
        'pulse-active': {
          '0%, 100%': { boxShadow: '0 0 0 0 hsl(var(--primary) / 0.45)' },
          '50%':      { boxShadow: '0 0 0 6px hsl(var(--primary) / 0)' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.18s ease-out',
        'pulse-active': 'pulse-active 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [animate],
};
