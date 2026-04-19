/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tg-bg': 'var(--tg-theme-bg-color)',
        'tg-text': 'var(--tg-theme-text-color)',
        'tg-hint': 'var(--tg-theme-hint-color)',
        'tg-link': 'var(--tg-theme-link-color)',
        'tg-button': 'var(--tg-theme-button-color)',
        'tg-button-text': 'var(--tg-theme-button-text-color)',
        'tg-secondary': 'var(--tg-theme-secondary-bg-color)',
        // Gaming Cyberpunk Colors
        'cyber-dark': '#0A0A0F',
        'neon-red': '#FF0033',
        'neon-cyan': '#00F0FF',
        'neon-purple': '#9D4EDD',
        'neon-gold': '#FFD700',
      },
      boxShadow: {
        'neon-red': '0 0 10px rgba(255, 0, 51, 0.5), 0 0 20px rgba(255, 0, 51, 0.3)',
        'neon-red-lg': '0 0 20px rgba(255, 0, 51, 0.6), 0 0 40px rgba(255, 0, 51, 0.4), 0 0 60px rgba(255, 0, 51, 0.2)',
        'neon-cyan': '0 0 10px rgba(0, 240, 255, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)',
        'neon-purple': '0 0 10px rgba(157, 78, 221, 0.5), 0 0 20px rgba(157, 78, 221, 0.3)',
        'neon-gold': '0 0 10px rgba(255, 215, 0, 0.5), 0 0 20px rgba(255, 215, 0, 0.3)',
        'glass': '0 8px 32px 0 rgba(255, 0, 51, 0.1)',
      },
      backdropBlur: {
        'glass': '10px',
      },
      keyframes: {
        'slide-down': {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'spin': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'pulse-glow': {
          '0%, 100%': { 
            boxShadow: '0 0 10px rgba(255, 0, 51, 0.5), 0 0 20px rgba(255, 0, 51, 0.3)',
          },
          '50%': { 
            boxShadow: '0 0 20px rgba(255, 0, 51, 0.8), 0 0 40px rgba(255, 0, 51, 0.5), 0 0 60px rgba(255, 0, 51, 0.3)',
          },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      animation: {
        'slide-down': 'slide-down 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'spin': 'spin 1s linear infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      fontFamily: {
        'gaming': ['Orbitron', 'Rajdhani', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
