# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/devnex-shop/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Devnex Shop (переиспользуемый шаблон интернет-каталога)
**Generated:** 2026-07-28 · adapted for Uzbekistan wholesale/stationery, mobile-first
**Category:** E-commerce каталог · приоритет плотности и скорости сканирования

> Адаптировано вручную под проект. Ключевые отличия от сырого вывода скилла:
> нейтральная палитра + **динамический акцент** из `ShopSettings`, шрифты с
> кириллицей и узбекской латиницей (локальные файлы, не CDN), **плотная**
> сетка вместо декоративной «много воздуха».

---

## Global Rules

### Color Palette

**Правило:** акцентный цвет НЕ хардкодится. Это шаблон под любого клиента.
Акцент приходит из `ShopSettings.primary_color` через CSS-переменную
`--shop-primary` (см. `base.html`: `style="--shop-primary: {{ shop.primary_color }}"`).
В дизайн-системе фиксируем **только нейтраль**.

| Role | Hex | CSS Variable | Notes |
|------|-----|--------------|-------|
| Background (бумага) | `#F6F5F1` | `--color-bg` | тёплый нейтральный фон страницы |
| Surface (карточка) | `#FFFFFF` | `--color-surface` | поверхность товара |
| Surface sunken | `#EFEEE9` | `--color-surface-2` | подложка фото, чипы |
| Border (волосяная) | `#E6E4DC` | `--color-border` | разделители, рамки карточек |
| Foreground (чернила) | `#1C1B17` | `--color-fg` | основной текст, цены |
| Muted | `#7A776D` | `--color-muted` | артикул, единицы, второстепенное |
| In stock | `#2FA36B` | `--color-instock` | индикатор наличия |
| Destructive | `#DC2626` | `--color-danger` | ошибки, удаление |

**Динамический акцент (не хранить hex здесь):**

| Role | CSS Variable | Источник |
|------|--------------|----------|
| Accent / CTA | `--shop-primary` | `ShopSettings.primary_color` |
| On accent | `--shop-on-primary` (`#FFFFFF`) | текст на кнопке-акценте |
| Focus ring | `--shop-primary` | видимый фокус клавиатуры |

> `--brand` оставлен как алиас `var(--shop-primary)` для обратной совместимости
> с уже написанными утилитами. Канонический источник — `--shop-primary`.

### Typography

**Замена относительно вывода скилла.** Скилл предложил **Rubik + Nunito Sans**.
Проблема: **Nunito Sans не содержит кириллицы**, а нам нужны и кириллица, и
узбекская латиница (`oʻ`, `gʻ`, `sh`, `ch`). Заменяем на пару с полным
покрытием обоих алфавитов:

- **Заголовки:** **Onest** — гротеск с кириллицей и Latin Extended, плотный,
  хорошо читается в мелком размере (нам важна плотность, а не декоративность).
- **Текст/интерфейс/цены:** **Manrope** — кириллица + латиница, отличные
  табличные цифры (`tnum`).

**Подключение — локальными файлами, НЕ через Google Fonts CDN** (из Узбекистана
CDN грузится медленно). `@font-face` с `font-display: swap`, файлы в
`static/src/fonts/`, отдаются с сервера:

```css
@font-face {
  font-family: "Onest";
  src: url("/static/fonts/Onest-Variable.woff2") format("woff2");
  font-weight: 400 800; font-display: swap;
}
@font-face {
  font-family: "Manrope";
  src: url("/static/fonts/Manrope-Variable.woff2") format("woff2");
  font-weight: 400 800; font-display: swap;
}
```

- Все числовые значения (цены, количество, итог): `font-variant-numeric: tabular-nums`.
- Заголовки — вес 700–800, плотный трекинг. Тело — 400–600.

### Spacing Scale (density-first)

**Только эти значения. Промежуточных не существует.**

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | `4px` | микро-зазоры внутри чипа/счётчика |
| `--space-2` | `8px` | падинг фото, зазор иконка↔текст |
| `--space-3` | `12px` | gap сетки на мобильном, падинг карточки |
| `--space-4` | `16px` | gap сетки на десктопе, падинг секции |
| `--space-6` | `24px` | отступы между блоками |
| `--space-8` | `32px` | крупные секции |
| `--space-12` | `48px` | максимум — только герой/подвал |

> Приоритет — **плотность и скорость сканирования**. Покупатель собирает 10–20
> позиций с телефона: нужно видеть много товаров сразу и легко попадать по «+».
> Крупные декоративные карточки и щедрые отступы (48px+ между товарами) —
> **запрещены** в товарной сетке.

### Radius & Shadow

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-card` | `14px` | карточка товара, крупные блоки |
| `--radius-control`| `10px` | кнопки, инпуты, счётчик, чипы |
| `--shadow-card` | `0 1px 2px rgba(28,27,23,.04), 0 8px 24px -16px rgba(28,27,23,.18)` | карточки |
| `--shadow-tape` | `0 -8px 24px -12px rgba(28,27,23,.25)` | плавающая панель корзины |

---

## Component Specs

### Button (CTA)
```css
.btn-primary {
  background: var(--shop-primary);
  color: var(--shop-on-primary, #fff);
  min-height: 44px;              /* тач-таргет */
  padding: 10px 16px;
  border-radius: var(--radius-control);
  font-weight: 700;
  transition: filter 150ms ease;
  cursor: pointer;
}
.btn-primary:hover { filter: brightness(0.95); }
```

### Card (товар) — базовые правила, детали в `pages/catalog.md`
```css
.product-card {
  display: flex; flex-direction: column; height: 100%;
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
```

### Input / Search
```css
.input {
  min-height: 44px; padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-control);
  font-size: 16px;               /* iOS не зумит при фокусе */
}
.input:focus { border-color: var(--shop-primary); outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--shop-primary) 18%, transparent); }
```

---

## Style Direction

**Не** «Vibrant & Block-based» из сырого вывода. Наш ориентир —
**utility retail / dense catalog**: тихая нейтральная база, единственный
акцент — фирменный цвет на кнопках заказа и активном счётчике. Смысл несёт
структура и числа (цены, количество, итог), а не декор.

---

## Anti-Patterns (Do NOT Use)

- ❌ **Хардкод акцентного цвета** — только `var(--shop-primary)`.
- ❌ **Хардкод названия магазина, телефонов, адреса** — только из `ShopSettings` (`shop`).
- ❌ **Крупные декоративные карточки и отступы 48px+** в товарной сетке.
- ❌ **Цветной фон** (мятный/акцентный) под каталогом — мешает сканировать.
- ❌ **Эмодзи как иконки** — только SVG (inline).
- ❌ **Layout-shifting hover** (scale, сдвигающий соседей).
- ❌ **Низкий контраст** (< 4.5:1 для текста).
- ❌ **Тач-таргет < 44px**.
- ❌ **Шрифты без кириллицы** или подключение через внешний CDN.

---

## Pre-Delivery Checklist

- [ ] Акцент только через `--shop-primary`; цвета/название/контакты — из `ShopSettings`.
- [ ] Нет горизонтальной прокрутки на 390px.
- [ ] Все кликабельные элементы ≥ 44×44px.
- [ ] Виден фокус с клавиатуры.
- [ ] Контраст текста ≥ 4.5:1.
- [ ] `prefers-reduced-motion` учтён; транзишены 150–300ms.
- [ ] Иконки — SVG, не эмодзи.
- [ ] Проверено на 390 / 768 / 1024 / 1440px.
