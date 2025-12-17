// Основная логика приложения
document.addEventListener('DOMContentLoaded', function() {
    // Мобильное меню
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.getElementById('navLinks');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
        });
    }
    
    // Плавная прокрутка
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 80,
                    behavior: 'smooth'
                });
                
                // Закрыть мобильное меню
                if (window.innerWidth <= 768) {
                    navLinks.style.display = 'none';
                }
            }
        });
    });
    
    // Активный пункт меню при прокрутке
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.nav-link');
        
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= (sectionTop - 100)) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
    
    // Кнопка "Посмотреть курсы"
    const heroCoursesBtn = document.getElementById('heroCoursesBtn');
    if (heroCoursesBtn) {
        heroCoursesBtn.addEventListener('click', () => {
            document.querySelector('#courses').scrollIntoView({
                behavior: 'smooth'
            });
        });
    }
    
    // Инициализация
    init();
});

// Инициализация приложения
async function init() {
    // Загрузка преподавателей (пример)
    try {
        const teachers = await api.getTeachers();
        // Можно обновить UI с реальными данными
        console.log('Teachers loaded:', teachers);
    } catch (error) {
        console.error('Failed to load teachers:', error);
    }
}

// Утилиты
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

function formatTime(timeString) {
    if (!timeString) return '';
    return timeString; // Уже в формате HH:mm
}