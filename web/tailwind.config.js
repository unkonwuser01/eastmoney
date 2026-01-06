/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Clean Light Palette
        background: '#f8fafc', // Slate 50
        surface: '#ffffff',    // White
        primary: {
          DEFAULT: '#2563eb', // Blue 600
          glow: '#60a5fa',    // Blue 400 (for subtle highlights)
          dark: '#1e40af',    // Blue 800
        },
        secondary: {
          DEFAULT: '#0d9488', // Teal 600
        },
        accent: '#d97706',    // Amber 600
        zinc: {
           950: '#020617', // Very dark for text
           900: '#0f172a', // Primary text
           800: '#1e293b',
           700: '#334155',
           600: '#475569',
           500: '#64748b', // Secondary text
           400: '#94a3b8',
           300: '#cbd5e1', // Borders
           200: '#e2e8f0', // Light borders
           100: '#f1f5f9', // Hover backgrounds
           50:  '#f8fafc', // Main background
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        'card': '0 0 0 1px rgba(0,0,0,0.05), 0 2px 8px rgba(0,0,0,0.05)',
      }
    },
  },
  plugins: [],
}