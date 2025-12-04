document.addEventListener("DOMContentLoaded", function() {
    const footerHTML = `
    <footer class="site-footer">
        <div class="footer-container">
            <div class="footer-section about">
                <h3>exSighting</h3>
                <p>Explore the world, capture the moment. exSighting is your trusted companion on every journey.</p>
            </div>

            <div class="footer-section links">
                <h3>Explore</h3>
                <ul>
                    <li><a href="home.html">Home</a></li>
                    <li><a href="about.html">About Us</a></li>
                    <li><a href="destinations.html">Destinations</a></li>
                </ul>
            </div>

            <div class="footer-section contact">
                <h3>Contact</h3>
                <p><i class="fas fa-map-marker-alt"></i> Ho Chi Minh City, Vietnam</p>
                <p><i class="fas fa-envelope"></i> contact@exsighting.com</p>
            </div>

            <div class="footer-section social">
                <h3>Connect</h3>
                <div class="social-icons">
                    <a href="https://github.com/yourusername" target="_blank" class="social-icon github">
                        <i class="fab fa-github"></i>
                    </a>
                    <a href="#" class="social-icon facebook"><i class="fab fa-facebook"></i></a>
                    <a href="#" class="social-icon instagram"><i class="fab fa-instagram"></i></a>
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