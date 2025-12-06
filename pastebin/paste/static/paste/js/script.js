function checkTextLength(event) {
    const maxChar = 200000
    const formNode = event.target.value
    const button = document.getElementById('btn-submit')
    const formErrors = document.getElementById('form-errors')
    
    if (formNode.length > maxChar) {
        button.disabled = true
        formErrors.textContent = `Превышен лимит на ${formNode.length - maxChar} символов`
    }
    else {
        button.disabled = false
        formErrors.textContent = ''
    }
}

const text = document.getElementById('paste_text');

text.addEventListener('input', checkTextLength);