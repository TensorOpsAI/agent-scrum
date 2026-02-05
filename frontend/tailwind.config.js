/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'backlog': '#6B7280',
        'ready': '#3B82F6',
        'in-progress': '#F59E0B',
        'review': '#8B5CF6',
        'qa': '#EC4899',
        'done': '#10B981',
      },
    },
  },
  plugins: [],
}
