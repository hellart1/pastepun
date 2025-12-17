const toggleBtn = document.getElementById('theme-toggle');
const htmlEl = document.documentElement;

if (localStorage.getItem('theme') === 'dark') {
    htmlEl.classList.add('dark-theme');
}

if(toggleBtn) {
    toggleBtn.addEventListener('click', () => {
        htmlEl.classList.toggle('dark-theme');
        
        if (htmlEl.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });
}