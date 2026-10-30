/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          deep: '#101C35',
          dark: '#172846',
        },
        corp: {
          blue: '#2457A6',
          hover: '#1A4482',
        },
      },
      animation: {
        'subtle-sway': 'subtleSway 2s ease-in-out infinite',
        'fadeIn': 'fadeIn 150ms ease-in-out',
      },
      keyframes: {
        subtleSway: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-2px)' },
        },
        fadeIn: {
          'from': { opacity: '0', transform: 'scale(0.98)' },
          'to': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
