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
        brand: "var(--brand, #2563eb)",
        ink: "#1C1B17", // тёплый почти-чёрный для текста
        paper: "#F6F5F1", // тёплая бумага — фон страницы
        line: "#E6E4DC", // волосяные разделители
        muted: "#7A776D", // второстепенный текст
        stock: "#2FA36B", // индикатор «в наличии»
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
        card: "0 1px 2px rgba(28,27,23,0.04), 0 8px 24px -16px rgba(28,27,23,0.18)",
        tape: "0 -8px 24px -12px rgba(28,27,23,0.25)",
      },
      maxWidth: {
        shell: "1200px",
      },
    },
  },
  plugins: [],
};
