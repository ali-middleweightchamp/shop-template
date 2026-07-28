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
        // Фирменный цвет подставляется из ShopSettings через CSS-переменную
        brand: "var(--brand-color, #2563eb)",
      },
    },
  },
  plugins: [],
};
