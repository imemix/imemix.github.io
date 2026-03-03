function copyCode(button) {
    const codeBlock = button.previousElementSibling;
    const code = codeBlock.textContent;
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    });
}

// Hamburger menu toggle
const hamburgerBtn = document.getElementById('hamburgerBtn');
const docsSidebar = document.getElementById('docsSidebar');

if (hamburgerBtn) {
    hamburgerBtn.addEventListener('click', () => {
        docsSidebar.classList.toggle('open');
        hamburgerBtn.classList.toggle('active');
    });

    // Close menu when a link is clicked
    const tocLinks = docsSidebar.querySelectorAll('.toc a');
    tocLinks.forEach(link => {
        link.addEventListener('click', () => {
            docsSidebar.classList.remove('open');
            hamburgerBtn.classList.remove('active');
        });
    });
}