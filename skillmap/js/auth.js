// DOM элементы
const registerModal = document.getElementById('registerModal');
const loginModal = document.getElementById('loginModal');
const registerBtn = document.getElementById('registerBtn');
const loginBtn = document.getElementById('loginBtn');
const heroRegisterBtn = document.getElementById('heroRegisterBtn');
const closeRegisterModal = document.getElementById('closeRegisterModal');
const closeLoginModal = document.getElementById('closeLoginModal');
const switchToLogin = document.getElementById('switchToLogin');
const switchToRegister = document.getElementById('switchToRegister');
const registerForm = document.getElementById('registerForm');
const loginForm = document.getElementById('loginForm');
const navAuth = document.getElementById('navAuth');
const notification = document.getElementById('notification');

// Открытие модальных окон
registerBtn.addEventListener('click', () => openModal('register'));
loginBtn.addEventListener('click', () => openModal('login'));
heroRegisterBtn.addEventListener('click', () => openModal('register'));

// Закрытие модальных окон
closeRegisterModal.addEventListener('click', () => closeModal('register'));
closeLoginModal.addEventListener('click', () => closeModal('login'));

// Переключение между окнами
switchToLogin.addEventListener('click', (e) => {
    e.preventDefault();
    closeModal('register');
    openModal('login');
});

switchToRegister.addEventListener('click', (e) => {
    e.preventDefault();
    closeModal('login');
    openModal('register');
});

// Закрытие по клику вне модального окна
window.addEventListener('click', (e) => {
    if (e.target === registerModal) closeModal('register');
    if (e.target === loginModal) closeModal('login');
});

// Функции управления модальными окнами
function openModal(type) {
    if (type === 'register') {
        registerModal.style.display = 'flex';
        document.getElementById('email').focus();
    } else if (type === 'login') {
        loginModal.style.display = 'flex';
        document.getElementById('loginEmail').focus();
    }
    document.body.style.overflow = 'hidden';
}

function closeModal(type) {
    if (type === 'register') {
        registerModal.style.display = 'none';
        registerForm.reset();
        clearErrors();
    } else if (type === 'login') {
        loginModal.style.display = 'none';
        loginForm.reset();
    }
    document.body.style.overflow = 'auto';
}

// Показать уведомление
function showNotification(message, type = 'info', duration = 3000) {
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, duration);
}

// Очистка ошибок
function clearErrors() {
    document.querySelectorAll('.error-message').forEach(el => {
        el.style.display = 'none';
        el.textContent = '';
    });
    document.querySelectorAll('.form-group input').forEach(input => {
        input.classList.remove('error');
    });
}

// Валидация регистрации
function validateRegisterForm() {
    let isValid = true;
    clearErrors();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Валидация email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        document.getElementById('emailError').textContent = 'Введите корректный email';
        document.getElementById('emailError').style.display = 'block';
        document.getElementById('email').classList.add('error');
        isValid = false;
    }
    
    // Валидация пароля
    if (password.length < 6) {
        document.getElementById('passwordError').textContent = 'Пароль должен быть не менее 6 символов';
        document.getElementById('passwordError').style.display = 'block';
        document.getElementById('password').classList.add('error');
        isValid = false;
    }
    
    // Подтверждение пароля
    if (password !== confirmPassword) {
        document.getElementById('confirmPasswordError').textContent = 'Пароли не совпадают';
        document.getElementById('confirmPasswordError').style.display = 'block';
        document.getElementById('confirmPassword').classList.add('error');
        isValid = false;
    }
    
    return isValid;
}

// Обработка регистрации
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!validateRegisterForm()) return;
    
    const submitBtn = document.getElementById('submitRegister');
    const registerText = document.getElementById('registerText');
    const registerLoading = document.getElementById('registerLoading');
    
    // Показать индикатор загрузки
    submitBtn.disabled = true;
    registerText.style.display = 'none';
    registerLoading.style.display = 'inline';
    
    try {
        const apprenticeData = {
            email: document.getElementById('email').value,
            surname: document.getElementById('surname').value,
            name: document.getElementById('name').value,
            patronymic: document.getElementById('patronymic').value,
            password: document.getElementById('password').value,
            // Стандартные поля для ученика
            status: 'active',
            trackId: 'default-track',
            groupCode: 'NEW-2024',
            advisorUserId: 'system',
            hoursPerWeek: 20,
            progressPercent: 0,
            creditsEarned: 0
        };
        
        const result = await api.registerApprentice(apprenticeData);
        
        showNotification('Регистрация успешна! Теперь вы можете войти.', 'success');
        closeModal('register');
        
        // Автоматически входим после регистрации
        setTimeout(() => {
            openModal('login');
            document.getElementById('loginEmail').value = apprenticeData.email;
            document.getElementById('loginPassword').focus();
        }, 1500);
        
    } catch (error) {
        showNotification(`Ошибка регистрации: ${error.message}`, 'error');
    } finally {
        // Скрыть индикатор загрузки
        submitBtn.disabled = false;
        registerText.style.display = 'inline';
        registerLoading.style.display = 'none';
    }
});

// Обработка входа
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitLogin');
    const loginText = document.getElementById('loginText');
    const loginLoading = document.getElementById('loginLoading');
    
    // Показать индикатор загрузки
    submitBtn.disabled = true;
    loginText.style.display = 'none';
    loginLoading.style.display = 'inline';
    
    try {
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        const result = await api.login(email, password);
        
        if (result.success) {
            showNotification('Вход выполнен успешно!', 'success');
            closeModal('login');
            
            // Обновить интерфейс
            setTimeout(() => {
                checkAndUpdateAuthUI();
            }, 500);
        } else {
            showNotification(result.error || 'Ошибка входа', 'error');
        }
    } catch (error) {
        showNotification(`Ошибка входа: ${error.message}`, 'error');
    } finally {
        // Скрыть индикатор загрузки
        submitBtn.disabled = false;
        loginText.style.display = 'inline';
        loginLoading.style.display = 'none';
    }
});

// Обновить UI после авторизации
async function checkAndUpdateAuthUI() {
    try {
        const user = await api.getCurrentUser();
        
        if (user) {
            // Создаем меню пользователя
            const userMenu = document.createElement('div');
            userMenu.className = 'user-menu';
            
            const userAvatar = document.createElement('div');
            userAvatar.className = 'user-avatar';
            userAvatar.textContent = user.name[0] + user.surname[0];
            
            const userInfo = document.createElement('div');
            userInfo.className = 'user-info';
            
            const userName = document.createElement('div');
            userName.className = 'user-name';
            userName.textContent = `${user.name} ${user.surname}`;
            
            const userRole = document.createElement('div');
            userRole.className = 'user-role';
            
            // Определяем роль по типу пользователя
            let roleText = 'Студент';
            let role = 'STUDENT';
            
            if (user.type === 'admin') {
                roleText = 'Администратор';
                role = 'ADMIN';
            } else if (user.type === 'teacher') {
                roleText = 'Преподаватель';
                role = 'TEACHER';
            } else if (user.type === 'moderator') {
                roleText = 'Модератор';
                role = 'MODERATOR';
            }
            
            userRole.textContent = roleText;
            
            // Сохраняем информацию о пользователе
            localStorage.setItem('user_role', role);
            localStorage.setItem('user_name', `${user.name} ${user.surname}`);
            
            // Создаем выпадающее меню
            const dropdown = document.createElement('div');
            dropdown.className = 'dropdown';
            
            const dropdownToggle = document.createElement('button');
            dropdownToggle.className = 'dropdown-toggle';
            dropdownToggle.innerHTML = '<i class="fas fa-chevron-down"></i>';
            
            const dropdownMenu = document.createElement('div');
            dropdownMenu.className = 'dropdown-menu';
            
            // Пункты меню в зависимости от роли
            const menuItems = [
                { text: 'Мой профиль', href: '#', icon: 'user' },
                { text: 'Мои курсы', href: '#', icon: 'book' }
            ];
            
            if (role === 'ADMIN') {
                menuItems.push({ text: 'Админ-панель', href: '#', icon: 'cog' });
            } else if (role === 'TEACHER') {
                menuItems.push({ text: 'Мои ученики', href: '#', icon: 'users' });
                menuItems.push({ text: 'Расписание', href: '#', icon: 'calendar' });
            } else if (role === 'STUDENT') {
                menuItems.push({ text: 'Мои тренировки', href: '#', icon: 'dumbbell' });
            }
            
            menuItems.push({ type: 'divider' });
            menuItems.push({ 
                text: 'Выйти', 
                href: '#', 
                icon: 'sign-out-alt',
                action: async () => {
                    await api.logout();
                    showNotification('Вы вышли из системы', 'info');
                    updateAuthUI(false);
                }
            });
            
            menuItems.forEach(item => {
                if (item.type === 'divider') {
                    const divider = document.createElement('div');
                    divider.className = 'dropdown-divider';
                    dropdownMenu.appendChild(divider);
                } else {
                    const link = document.createElement('a');
                    link.className = 'dropdown-item';
                    link.href = item.href;
                    link.innerHTML = `<i class="fas fa-${item.icon}"></i> ${item.text}`;
                    
                    if (item.action) {
                        link.addEventListener('click', (e) => {
                            e.preventDefault();
                            item.action();
                        });
                    }
                    
                    dropdownMenu.appendChild(link);
                }
            });
            
            // Сборка UI
            userInfo.appendChild(userName);
            userInfo.appendChild(userRole);
            
            dropdown.appendChild(dropdownToggle);
            dropdown.appendChild(dropdownMenu);
            
            userMenu.appendChild(userAvatar);
            userMenu.appendChild(userInfo);
            userMenu.appendChild(dropdown);
            
            // Заменяем кнопки авторизации на меню пользователя
            navAuth.innerHTML = '';
            navAuth.appendChild(userMenu);
            
            // Показываем/скрываем элементы в зависимости от роли
            updateUIForRole(role);
            
            // Обработка клика на выпадающее меню
            dropdownToggle.addEventListener('click', () => {
                dropdownMenu.classList.toggle('show');
            });
            
            // Закрытие меню при клике вне
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target)) {
                    dropdownMenu.classList.remove('show');
                }
            });
        }
    } catch (error) {
        console.error('Failed to get user:', error);
        updateAuthUI(false);
    }
}

// Обновить UI в зависимости от роли
function updateUIForRole(role) {
    // Здесь можно добавлять/убирать элементы в зависимости от роли
    const navLinks = document.querySelector('.nav-links');
    
    // Например, добавляем пункт "Админ-панель" для администраторов
    if (role === 'ADMIN') {
        const adminLink = document.createElement('a');
        adminLink.href = '#admin';
        adminLink.className = 'nav-link';
        adminLink.textContent = 'Админ-панель';
        navLinks.appendChild(adminLink);
    }
    
    // Добавляем пункт "Мои тренировки" для студентов
    if (role === 'STUDENT') {
        const trainingLink = document.createElement('a');
        trainingLink.href = '#trainings';
        trainingLink.className = 'nav-link';
        trainingLink.textContent = 'Мои тренировки';
        navLinks.appendChild(trainingLink);
    }
    
    // Добавляем пункт "Мои ученики" для преподавателей
    if (role === 'TEACHER') {
        const studentsLink = document.createElement('a');
        studentsLink.href = '#students';
        studentsLink.className = 'nav-link';
        studentsLink.textContent = 'Мои ученики';
        navLinks.appendChild(studentsLink);
    }
}

// Обновить UI авторизации
function updateAuthUI(isAuthenticated) {
    if (isAuthenticated) {
        checkAndUpdateAuthUI();
    } else {
        // Показать кнопки входа/регистрации
        navAuth.innerHTML = `
            <button class="btn btn-outline" id="loginBtn">Войти</button>
            <button class="btn btn-primary" id="registerBtn">Регистрация</button>
        `;
        
        // Удаляем добавленные пункты меню
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.textContent === 'Админ-панель' || 
                link.textContent === 'Мои тренировки' || 
                link.textContent === 'Мои ученики') {
                link.remove();
            }
        });
        
        // Перепривязываем события
        document.getElementById('loginBtn').addEventListener('click', () => openModal('login'));
        document.getElementById('registerBtn').addEventListener('click', () => openModal('register'));
    }
}

// Проверить авторизацию при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    const isAuthenticated = await api.checkAuth();
    updateAuthUI(isAuthenticated);
});

// auth-min.js - минимизированная версия
document.addEventListener('DOMContentLoaded',function(){
    fetch('/api/auth/check-redirect',{credentials:'include'})
    .then(r=>r.ok?r.json():null).then(d=>{if(d&&d.redirect)setTimeout(()=>location.href=d.url,100)});
    
    function h(e){e.preventDefault();fetch('/api/auth/me',{credentials:'include'}).then(r=>r.ok?r.json():null)
    .then(u=>{if(u&&u.authenticated)fetch('/api/auth/check-redirect',{credentials:'include'})
    .then(r=>r.ok?r.json():null).then(d=>{location.href=d&&d.redirect?d.url:'/dashboard'});
    else location.href=e.target.href||'/register'})}
    
    document.querySelectorAll('.create-skills-btn,.start-free-btn,.get-started-btn').forEach(b=>{
        b.onclick=h});
});