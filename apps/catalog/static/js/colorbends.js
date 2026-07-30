/* ------------------------------------------------------------------ *
 * ColorBends — лёгкий анимированный фон: мягкие диагональные полосы
 * акцентного цвета. Аналог React-компонента, но на чистом canvas под
 * наш стек. Дёшево (паттерн + 2 заливки на кадр), учитывает тему
 * (--accent) и prefers-reduced-motion (тогда статичный кадр).
 *
 * Параметры читаются с data-* канвы (см. base.html):
 *   data-speed, data-frequency, data-band-width, data-rotation,
 *   data-fade-top, data-intensity, data-noise
 * ------------------------------------------------------------------ */
(function () {
  const canvas = document.getElementById("bg-bends");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const P = {
    speed: parseFloat(canvas.dataset.speed) || 0.2,
    frequency: parseFloat(canvas.dataset.frequency) || 1.0,
    bandWidth: parseFloat(canvas.dataset.bandWidth) || 0.14,
    rotation: parseFloat(canvas.dataset.rotation) || 90,
    fadeTop: parseFloat(canvas.dataset.fadeTop) || 0.75,
    intensity: parseFloat(canvas.dataset.intensity) || 1.3,
    noise: parseFloat(canvas.dataset.noise) || 0.15,
  };

  let dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  let W = 0, H = 0, offset = 0, tile = null, tileW = 0;

  // Текущий акцент из темы (пересчитывается при смене темы)
  function accent() {
    const c = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
    return c || "#10B981";
  }

  // Плитка одной полосы: прозрачно → акцент → прозрачно, мягкие края
  function buildTile() {
    const color = accent();
    tileW = Math.max(60, Math.round(220 / P.frequency));
    const t = document.createElement("canvas");
    t.width = tileW; t.height = 2;
    const tc = t.getContext("2d");
    const g = tc.createLinearGradient(0, 0, tileW, 0);
    const half = P.bandWidth / 2;
    g.addColorStop(0.0, hexA(color, 0));
    g.addColorStop(Math.max(0.001, 0.5 - half), hexA(color, 0));
    g.addColorStop(0.5, hexA(color, 1));
    g.addColorStop(Math.min(0.999, 0.5 + half), hexA(color, 0));
    g.addColorStop(1.0, hexA(color, 0));
    tc.fillStyle = g;
    tc.fillRect(0, 0, tileW, 2);
    tile = tc.createPattern ? t : t; // храним сам canvas-плитку
  }

  // #RRGGBB + alpha → rgba()
  function hexA(hex, a) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map((x) => x + x).join("");
    const n = parseInt(hex, 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const pattern = ctx.createPattern(tile, "repeat");
    // Полосы под нужным углом + сдвиг во времени + лёгкая «шумовая» волна
    const wobble = Math.sin(offset * 0.03) * P.noise * tileW;
    const m = new DOMMatrix()
      .rotate(P.rotation)
      .scale(1, Math.max(W, H) * 2) // растянуть полосу на весь экран по высоте
      .translate(offset + wobble, 0);
    pattern.setTransform(m);
    ctx.globalAlpha = 1;
    ctx.fillStyle = pattern;
    ctx.fillRect(-W, -H, W * 3, H * 3);

    // Вертикальное затухание сверху (fadeTop): маскируем
    ctx.globalCompositeOperation = "destination-in";
    const fade = ctx.createLinearGradient(0, 0, 0, H);
    fade.addColorStop(0, `rgba(0,0,0,${1 - P.fadeTop})`);
    fade.addColorStop(0.55, "rgba(0,0,0,1)");
    fade.addColorStop(1, "rgba(0,0,0,1)");
    ctx.fillStyle = fade;
    ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "source-over";
  }

  // Итоговая прозрачность фона задаётся через CSS opacity канвы,
  // intensity лишь слегка усиливает (см. base.html style).
  function frame() {
    offset += P.speed;
    draw();
    raf = requestAnimationFrame(frame);
  }

  let raf = null;
  function start() {
    buildTile(); resize(); draw();
    if (!reduce) { cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); }
  }

  window.addEventListener("resize", () => { resize(); if (reduce) draw(); });
  // Пересобрать плитку при смене темы (акцент меняется)
  new MutationObserver(() => { buildTile(); if (reduce) draw(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "data-preset", "style"] });

  start();
})();
