/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        iris: {
          blue: '#4a90d9',
          brown: '#8b6914',
          green: '#5a8f5a',
        }
      }
    },
  },
  plugins: [],
}
