/**
 * Client-side form validation module.
 *
 * Enhances forms marked with the `needs-client-validation` class by
 * providing real-time field feedback (password strength, field matching)
 * and preventing submission when the form is invalid.
 */
$(function () {
    /**
     * Check whether a password meets the minimum complexity rules.
     * @param {string} value - The password string.
     * @returns {boolean} True if at least 8 chars with a letter and digit.
     */
    function isStrongPassword(value) {
        return value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value);
    }

    /**
     * Toggle Bootstrap validation classes on a field.
     * @param {jQuery} $field - The jQuery-wrapped input element.
     * @param {boolean} isValid - Whether the field currently passes validation.
     */
    function setValidity($field, isValid) {
        $field.toggleClass("is-invalid", !isValid);
        $field.toggleClass("is-valid", isValid && $field.val().length > 0);
    }

    /**
     * Run all applicable validation rules on a single field.
     * @param {HTMLInputElement} field - The raw DOM input element.
     * @returns {boolean} True if the field is valid.
     */
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

    // Re-validate on every keystroke so feedback is immediate
    $(".needs-client-validation input").on("input change", function () {
        validateField(this);

        const $form = $(this).closest("form");
        const $matchingFields = $form.find("[data-match='#" + this.id + "']");
        $matchingFields.each(function () {
            validateField(this);
        });
    });
});
