window.addEventListener('DOMContentLoaded', event => {

    // Navbar shrink
    const navbarShrink = () => {
        const navbarCollapsible = document.body.querySelector('#mainNav');
        if (!navbarCollapsible) return;
        navbarCollapsible.classList.toggle('navbar-shrink', window.scrollY > 0);
    };
    navbarShrink();
    document.addEventListener('scroll', navbarShrink);

    // Collapse responsive navbar on link click
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    document.querySelectorAll('#navbarResponsive .nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (navbarToggler && window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });

    // Carousel
    const carousel = document.getElementById('carouselExampleCaptions');
    if (carousel) {
        new bootstrap.Carousel(carousel, {
            interval: 3000,
            wrap: true,
            ride: 'carousel',
            pause: false
        });
    }

    // Fade-in on scroll
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.destination-card, .testimonial-card, .circuit-card').forEach(el => {
        el.classList.add('fade-in-up');
        observer.observe(el);
    });

});
