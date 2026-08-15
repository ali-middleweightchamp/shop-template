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
        // Шрифты — из темы (themes.css), пресет может их менять
        sans: ['var(--font-sans)'],
        display: ['var(--font-display)'],
      },
      borderRadius: {
        // Скругления — из темы: emerald мягкие, sunset острые
        card: "var(--radius-card)",
        control: "var(--radius-control)",
        pill: "var(--radius-pill)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
      },
      maxWidth: {
        shell: "1440px",
      },
    },
  },
  plugins: [],
};
