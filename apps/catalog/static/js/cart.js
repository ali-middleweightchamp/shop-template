/* ------------------------------------------------------------------ *
 * Корзина на localStorage (ключ cart_v1). Alpine-стор доступен как
 * $store.cart во всех шаблонах. Переживает перезагрузку и закрытие вкладки.
 * На этапе 6 сюда добавится формирование текста заказа для Telegram.
 * ------------------------------------------------------------------ */
const CART_KEY = "cart_v1";

// Формат суммы «240 000» (пробел-разделитель тысяч) — привычно для сумов
function formatMoney(n) {
  return Math.round(Number(n) || 0)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}
window.formatMoney = formatMoney;

// Переключатель темы. Начальное значение уже выставлено inline-скриптом в <head>.
function toggleTheme() {
  var html = document.documentElement;
  var next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  try {
    localStorage.setItem("theme", next);
  } catch (e) {}
}
window.toggleTheme = toggleTheme;

document.addEventListener("alpine:init", () => {
  Alpine.store("cart", {
    items: {},

    init() {
      try {
        this.items = JSON.parse(localStorage.getItem(CART_KEY)) || {};
      } catch (e) {
        this.items = {};
      }
    },

    persist() {
      localStorage.setItem(CART_KEY, JSON.stringify(this.items));
    },

    qty(sku) {
      return this.items[sku] ? this.items[sku].qty : 0;
    },

    // product: {sku, name, price, unit}
    add(product) {
      const cur = this.items[product.sku];
      if (cur) {
        cur.qty += 1;
      } else {
        this.items[product.sku] = {
          name: product.name,
          price: Number(product.price) || 0,
          unit: product.unit || "",
          qty: 1,
        };
      }
      this.persist();
    },

    inc(sku) {
      if (this.items[sku]) {
        this.items[sku].qty += 1;
        this.persist();
      }
    },

    dec(sku) {
      const cur = this.items[sku];
      if (!cur) return;
      cur.qty -= 1;
      if (cur.qty <= 0) delete this.items[sku];
      this.persist();
    },

    remove(sku) {
      delete this.items[sku];
      this.persist();
    },

    get count() {
      return Object.values(this.items).reduce((s, i) => s + i.qty, 0);
    },

    get total() {
      return Object.values(this.items).reduce((s, i) => s + i.qty * i.price, 0);
    },

    get lines() {
      return Object.entries(this.items).map(([sku, i]) => ({ sku, ...i }));
    },
  });
});
