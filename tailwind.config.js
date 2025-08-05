/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./ui/**/*.{html,js,jsx,ts,tsx}",
    "./agents/**/templates/**/*.{html,js}",
    "./shared/**/*.{html,js}",
  ],
  theme: {
    extend: {
      colors: {
        'brainsait-blue': '#1e40af',
        'brainsait-green': '#059669',
        'saudi-green': '#006c35',
        'arabic-gold': '#d4af37',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
