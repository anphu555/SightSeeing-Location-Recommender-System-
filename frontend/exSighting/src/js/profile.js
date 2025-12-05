document.addEventListener('DOMContentLoaded', () => {
    // Handle Tabs Switching
    const tabs = document.querySelectorAll('.tab-link');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            // Add active class to current
            tab.classList.add('active');
            const targetId = tab.getAttribute('data-tab');
            const targetContent = document.getElementById(targetId);
            
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    // Handle Remove from Wishlist (Demo)
    const removeBtns = document.querySelectorAll('.btn-icon-remove');
    removeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); // Stop click event bubbling
            // Confirm dialog in English
            if(confirm("Are you sure you want to remove this location from your wishlist?")) {
                const card = btn.closest('.place-card');
                card.style.opacity = '0'; // Fade out effect
                setTimeout(() => card.remove(), 300);
            }
        });
    });
});