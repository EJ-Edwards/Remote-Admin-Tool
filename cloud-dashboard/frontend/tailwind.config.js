/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        accent: { DEFAULT: '#059669', dark: '#047857' },
      },
    },
  },
  plugins: [],
}
