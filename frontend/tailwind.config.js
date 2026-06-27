/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0a0b0e',
          surface: 'rgba(18, 22, 32, 0.7)',
          card: 'rgba(22, 28, 42, 0.55)',
          cardHover: 'rgba(30, 38, 56, 0.7)'
        },
        brand: {
          primary: '#6366f1',
          secondary: '#14b8a6'
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'sans-serif'],
        display: ['Outfit', 'sans-serif']
      }
    },
  },
  plugins: [],
}
