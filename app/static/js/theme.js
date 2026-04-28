$(function () {
    const $html = $("html");
    const savedTheme = localStorage.getItem("theme") || "light";

    function applyTheme(theme) {
        const isDark = theme === "dark";
        $html.attr("data-bs-theme", theme);
        $html.toggleClass("dark", isDark);
        $(".theme-toggle-icon")
            .removeClass("bi-moon bi-sun")
            .addClass(isDark ? "bi-sun" : "bi-moon");
        $(".theme-toggle-label").text(isDark ? "Light mode" : "Dark mode");
        localStorage.setItem("theme", theme);
    }

    applyTheme(savedTheme);

    $(document).on("click", ".theme-toggle", function () {
        const currentTheme = $html.attr("data-bs-theme") || "light";
        applyTheme(currentTheme === "dark" ? "light" : "dark");
    });
});
