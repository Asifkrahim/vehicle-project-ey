// ========================================
// VehicleCare+ JS - Animations & UX
// ========================================

// Car animation on login/signup/dashboard pages
document.addEventListener('DOMContentLoaded', function () {
    const cars = document.querySelectorAll('.car-container');

    cars.forEach(car => {
        let pos = 0;
        setInterval(() => {
            pos += 1;
            if (pos > window.innerWidth) pos = -200; // Reset
            car.style.transform = `translateX(${pos}px)`;
        }, 20);
    });

    // Headlights blinking
    const headlights = document.querySelectorAll('.headlight');
    setInterval(() => {
        headlights.forEach(h => h.classList.toggle('headlight-on'));
    }, 1000);
});
