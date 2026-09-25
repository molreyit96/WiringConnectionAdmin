(function () {
    var THEME_KEY = "wc-theme";
    var root = document.documentElement;

    function applyTheme(theme) {
        if (theme === "dark") {
            root.setAttribute("data-theme", "dark");
        } else {
            root.removeAttribute("data-theme");
        }
    }

    function currentTheme() {
        return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
    }

    function updateToggleIcon() {
        var btn = document.getElementById("theme-toggle");
        if (!btn) return;
        var sun = btn.querySelector(".icon-theme-sun");
        var moon = btn.querySelector(".icon-theme-moon");
        var dark = currentTheme() === "dark";
        if (sun) sun.style.display = dark ? "none" : "inline";
        if (moon) moon.style.display = dark ? "inline" : "none";
    }

    applyTheme(localStorage.getItem(THEME_KEY) || "light");

    document.addEventListener("DOMContentLoaded", function () {
        updateToggleIcon();
        var btn = document.getElementById("theme-toggle");
        if (btn) {
            btn.addEventListener("click", function () {
                var next = currentTheme() === "dark" ? "light" : "dark";
                localStorage.setItem(THEME_KEY, next);
                applyTheme(next);
                updateToggleIcon();
            });
        }
    });
})();