// Shared JavaScript across all pages
document.addEventListener('DOMContentLoaded', () => {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Platform detection for download buttons
    const platform = navigator.platform.toLowerCase();
    const isWindows = platform.includes('win');
    const isMac = platform.includes('mac');
    
    if (isWindows || isMac) {
        const buttons = document.querySelectorAll('.download-btn');
        buttons.forEach(btn => {
            if ((isWindows && btn.dataset.os === 'windows') || 
                (isMac && btn.dataset.os === 'macos')) {
                btn.classList.add('bg-purple-600', 'text-white');
            }
        });
    }
});