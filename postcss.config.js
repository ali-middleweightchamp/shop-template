// postcss-import инлайнит @import (themes.css) в сборку Tailwind
module.exports = {
  plugins: {
    "postcss-import": {},
    tailwindcss: {},
    autoprefixer: {},
  },
};
