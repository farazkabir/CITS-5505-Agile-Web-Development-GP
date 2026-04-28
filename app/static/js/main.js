$(function () {
    $('[data-bs-toggle="tooltip"]').each(function () {
        new bootstrap.Tooltip(this);
    });

    $(".alert.alert-dismissible").each(function () {
        const $alert = $(this);
        setTimeout(function () {
            bootstrap.Alert.getOrCreateInstance($alert[0]).close();
        }, 5000);
    });

    $('a[href^="#"]').on("click", function (event) {
        const targetId = $(this).attr("href");
        if (targetId.length > 1) {
            const $target = $(targetId);
            if ($target.length) {
                event.preventDefault();
                $("html, body").animate({ scrollTop: $target.offset().top - 80 }, 300);
            }
        }
    });

    $(window).on("scroll", function () {
        const $nav = $(".navbar");
        $nav.toggleClass("shadow-sm", $(window).scrollTop() > 4);
    });

    $(".post-card").on("click", ".vote-btn", function () {
        const $btn = $(this);
        const $card = $btn.closest(".post-card");
        const isUp = $btn.hasClass("upvote");
        const wasActive = $btn.hasClass("active");

        $card.find(".vote-btn").removeClass("active");
        if (!wasActive) {
            $btn.addClass("active");
        }

        $card.find(".vote-count").each(function () {
            const $count = $(this);
            const baseValue = parseInt($count.data("base") ?? $count.text(), 10) || 0;
            $count.data("base", baseValue);

            let display = baseValue;
            if (!wasActive && isUp) display = baseValue + 1;
            else if (!wasActive && !isUp) display = baseValue - 1;

            $count.text(display);
            $count.toggleClass("voted", !wasActive && isUp);
        });
    });
});
