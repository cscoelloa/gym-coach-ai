(function () {
  "use strict";

  var CLAVE = "gym-tema";
  var CLAVE_VIEJA = "forja-theme";
  var raiz = document.documentElement;
  var oscuro = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  var BARRA = { light: "#f2f2f7", dark: "#000000" };

  function valida(valor) {
    return valor === "system" || valor === "light" || valor === "dark";
  }

  function leer() {
    try {
      var guardado = localStorage.getItem(CLAVE);
      if (valida(guardado)) return guardado;

      var viejo = localStorage.getItem(CLAVE_VIEJA);
      if (viejo === "light" || viejo === "dark") {
        localStorage.setItem(CLAVE, viejo);
        localStorage.removeItem(CLAVE_VIEJA);
        return viejo;
      }
    } catch (e) {
    }
    return "system";
  }

  function resolver(preferencia) {
    if (preferencia === "light" || preferencia === "dark") return preferencia;
    return oscuro && oscuro.matches ? "dark" : "light";
  }

  function aplicar(preferencia) {
    var tema = resolver(preferencia);
    raiz.setAttribute("data-theme", tema);
    raiz.setAttribute("data-theme-pref", preferencia);

    document.querySelectorAll('meta[name="theme-color"]').forEach(function (meta) {
      var suyo = meta.getAttribute("media") || "";
      var esquema = suyo.indexOf("dark") !== -1 ? "dark" : "light";
      meta.setAttribute("content", BARRA[preferencia === "system" ? esquema : tema]);
    });
  }

  window.getThemePreference = function () {
    return raiz.getAttribute("data-theme-pref") || "system";
  };

  window.setTheme = function (preferencia) {
    if (!valida(preferencia)) return;
    try {
      localStorage.setItem(CLAVE, preferencia);
    } catch (e) {
    }
    aplicar(preferencia);
  };

  if (oscuro) {
    var alCambiar = function () {
      if (window.getThemePreference() === "system") aplicar("system");
    };
    if (oscuro.addEventListener) oscuro.addEventListener("change", alCambiar);
    else if (oscuro.addListener) oscuro.addListener(alCambiar);
  }

  window.addEventListener("storage", function (evento) {
    if (evento.key === CLAVE && valida(evento.newValue)) aplicar(evento.newValue);
  });

  aplicar(leer());
})();
