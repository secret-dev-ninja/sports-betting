/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',  // Make sure to include your component paths as well
    './components/**/*.{js,ts,jsx,tsx}', // Include components directory
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}