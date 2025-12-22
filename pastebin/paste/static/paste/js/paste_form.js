(function() {
    var pasteText = document.getElementById('paste_text');
    var maxChar = 200000;

    function checkTextLength(event) {
        var formNode = event.target.value;
        var button = document.getElementById('btn-submit');
        var formErrors = document.getElementById('form-errors');

        if (formNode.length > maxChar) {
            button.disabled = true;
            formErrors.textContent = `Превышен лимит на ${formNode.length - maxChar} символов`;
        } else {
            button.disabled = false;
            formErrors.textContent = '';
        }
    }

    if (!pasteText.__listenerAttached) {
        pasteText.addEventListener('input', checkTextLength);
        pasteText.__listenerAttached = true;
    }
})();
