document.addEventListener("DOMContentLoaded", function() {
    const footerHTML = `
    <footer class="site-footer">
        <div class="footer-container">
            <div class="footer-col">
                <div class="footer-logo">
                    <i class="fas fa-umbrella"></i> exSighting
                </div>
                <p class="footer-desc">Sight the Extraordinary. Discover the hidden beauty of Vietnam in your own way.</p>
            </div>

            <div class="footer-col">
                <h4>Explore</h4>
                <ul class="footer-links">
                    <li><a href="home.html">Home</a></li>
                    <li><a href="about.html">About Us</a></li>
                    <li><a href="results.html?mode=popular">Popular Places</a></li>
                </ul>
            </div>

            <div class="footer-col">
                <h4>Contact</h4>
                <ul class="contact-list">
                    <li><i class="fas fa-map-marker-alt"></i> Ho Chi Minh City, Vietnam</li>
                    <li><i class="fas fa-envelope"></i> sigmaalphaprovip@gmail.com</li>
                    <li><i class="fas fa-phone"></i> +84 987 654 321</li>
                </ul>
            </div>

            <div class="footer-col">
                <h4>Connect</h4>
                <div class="social-icons">
                    <a href="#" aria-label="Github"><i class="fab fa-github"></i></a>
                    <a href="#" aria-label="Facebook"><i class="fab fa-facebook-f"></i></a>
                    <a href="#" aria-label="Instagram"><i class="fab fa-instagram"></i></a>
                </div>
            </div>
        </div>
        
        <div class="footer-bottom">
            &copy; 2025 exSighting Team. All rights reserved.
        </div>
    </footer>
    `;

    const placeholder = document.getElementById('footer-placeholder');
    if(placeholder) placeholder.innerHTML = footerHTML;
});