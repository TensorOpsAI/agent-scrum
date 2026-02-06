/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    // Pipeline column background colors
    'bg-gray-600',
    'bg-blue-600',
    'bg-blue-500',
    'bg-purple-600',
    'bg-yellow-600',
    'bg-pink-600',
    'bg-green-600',
    'bg-indigo-600',
    'bg-red-600',
    'bg-orange-600',
    // Pipeline column border-left colors (derived from bg)
    'border-l-gray-600',
    'border-l-blue-600',
    'border-l-blue-500',
    'border-l-purple-600',
    'border-l-yellow-600',
    'border-l-pink-600',
    'border-l-green-600',
    'border-l-indigo-600',
    'border-l-red-600',
    'border-l-orange-600',
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
