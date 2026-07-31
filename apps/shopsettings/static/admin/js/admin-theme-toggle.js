/* Простой тумблер темы (солнце/луна) в шапке админки — как на витрине.
   Использует тот же ключ localStorage, что и jazzmin, поэтому начальный режим
   применяется без вспышки (jazzmin выставляет data-bs-theme ещё в <head>). */
(function () {
  var KEY = "jazzmin-theme-mode";
  var MOON =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>';
  var SUN =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';

  function current() {
    return document.documentElement.getAttribute("data-bs-theme") === "dark" ? "dark" : "light";
  }
  function updateIcon(btn) {
    // Показываем иконку того, ВО ЧТО переключим (солнце в тёмной, луна в светлой)
    btn.innerHTML = current() === "dark" ? SUN : MOON;
  }
  function build() {
    if (document.getElementById("adm-theme-toggle")) return;
    var ul =
      document.querySelector(".app-header .navbar-nav.ms-auto") ||
      document.querySelector(".navbar-nav.ms-auto");
    if (!ul) return;
    var li = document.createElement("li");
    li.className = "nav-item";
    var btn = document.createElement("button");
    btn.id = "adm-theme-toggle";
    btn.type = "button";
    btn.className = "nav-link";
    btn.title = "Светлая / тёмная тема";
    btn.style.cssText = "border:0;background:none;cursor:pointer;padding:.5rem .75rem;";
    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-bs-theme", next);
      try {
        localStorage.setItem(KEY, next);
      } catch (e) {}
      updateIcon(btn);
    });
    updateIcon(btn);
    li.appendChild(btn);
    ul.insertBefore(li, ul.firstChild);
  }
  if (document.readyState !== "loading") build();
  else document.addEventListener("DOMContentLoaded", build);
})();
