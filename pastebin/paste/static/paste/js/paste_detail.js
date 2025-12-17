document.addEventListener("DOMContentLoaded", function() {
    const rawTextElement = document.getElementById('raw-paste-content');
    const container = document.getElementById('code-container');

    if (!rawTextElement || !container) {
        return;
    }
    
    const rawText = rawTextElement.value;
    
    const lines = rawText.split('\n');
    
    let html = '';
    lines.forEach((line, index) => {
        const safeLine = line.length === 0 ? ' ' : line
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

        html += `
            <div class="line-row">
                <div class="line-num">${index + 1}</div>
                <div class="line-code">${safeLine}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
});