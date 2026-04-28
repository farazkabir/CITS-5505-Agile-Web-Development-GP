$(function () {
    function isStrongPassword(value) {
        return value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value);
    }

    function setValidity($field, isValid) {
        $field.toggleClass("is-invalid", !isValid);
        $field.toggleClass("is-valid", isValid && $field.val().length > 0);
    }

    function validateField(field) {
        const $field = $(field);
        let isValid = field.checkValidity();

        if ($field.is("[data-password-strength]")) {
            isValid = isStrongPassword($field.val());
        }

        if ($field.is("[data-match]")) {
            const matchSelector = $field.data("match");
            isValid = $field.val() === $(matchSelector).val() && $field.val().length > 0;
        }

        setValidity($field, isValid);
        return isValid;
    }

    $(".needs-client-validation").on("submit", function (event) {
        const form = this;
        let formIsValid = true;

        $(form).find("input[required], input[data-match], input[data-password-strength]").each(function () {
            formIsValid = validateField(this) && formIsValid;
        });

        if (!formIsValid) {
            event.preventDefault();
            event.stopPropagation();
        }
    });

    $(".needs-client-validation input").on("input change", function () {
        validateField(this);

        const $form = $(this).closest("form");
        const $matchingFields = $form.find("[data-match='#" + this.id + "']");
        $matchingFields.each(function () {
            validateField(this);
        });
    });
});
