document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
        e.preventDefault();
        const el = document.querySelector(a.getAttribute('href'));
        if (el) el.scrollIntoView({ behavior: 'smooth' });
    });
});
const cards = document.querySelectorAll('.card');
const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
        if (e.isIntersecting) e.target.style.opacity = '1';
    });
}, { threshold: 0.1 });
cards.forEach(c => {
    c.style.opacity = '0';
    c.style.transition = 'opacity 0.6s, transform 0.3s';
    observer.observe(c);
});
