/** @type {import('tailwindcss').Config} */
module.exports = {
  // Сканируем шаблоны и JS, чтобы Tailwind оставил только используемые классы
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./static/src/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // Все цвета — только через семантические переменные тем (themes.css).
        bg: "var(--bg)",
        paper: "var(--bg)", // алиас для существующих bg-paper
        surface: "var(--surface)",
        sunken: "var(--surface-sunken)",
        ink: "var(--text)",
        muted: "var(--text-muted)",
        line: "var(--border-input)",
        accent: "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        "on-accent": "var(--on-accent)",
        brand: "var(--accent)", // акцент; primary_color перебивает через inline --accent
        stock: "var(--accent)",
        danger: "var(--danger)",
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        display: ['Onest', 'Manrope', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: "14px",
        control: "10px",
      },
      boxShadow: {
        card: "var(--shadow-card)",
      },
      maxWidth: {
        shell: "1200px",
      },
    },
  },
  plugins: [],
};
