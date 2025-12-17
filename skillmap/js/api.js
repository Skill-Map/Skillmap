// API базовый URL
const API_BASE_URL = 'http://localhost:8080';

// Общие заголовки
const getHeaders = () => {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    const token = localStorage.getItem('auth_token');
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
};

// Универсальный метод запроса
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: getHeaders()
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        // Для логина Spring Security возвращает редирект, обрабатываем отдельно
        if (endpoint === '/login' && method === 'POST') {
            return { success: response.ok };
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}`);
            }
            
            return result.result;
        } else {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return null;
        }
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// API методы
const api = {
    // Регистрация ученика (все регистрируются как ученики)
    registerApprentice: async (apprenticeData) => {
        return apiRequest('/apprentice', 'POST', {
            ...apprenticeData,
            type: 'apprentice',
            active: true
        });
    },
    
    // Логин (Spring Security form login)
    login: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData,
                credentials: 'include' // Для cookies/sessions
            });
            
            if (response.ok) {
                // Сохраняем email в localStorage
                localStorage.setItem('user_email', email);
                return { success: true };
            }
            return { success: false, error: 'Неверный email или пароль' };
        } catch (error) {
            return { success: false, error: 'Ошибка сети' };
        }
    },
    
    // Логаут
    logout: async () => {
        try {
            await fetch(`${API_BASE_URL}/logout`, {
                method: 'POST',
                credentials: 'include'
            });
            localStorage.removeItem('user_email');
            return true;
        } catch (error) {
            console.error('Logout error:', error);
            return false;
        }
    },
    
    // Получить текущего пользователя
    getCurrentUser: async () => {
        return apiRequest('/user');
    },
    
    // Проверить авторизацию
    checkAuth: async () => {
        try {
            await apiRequest('/user');
            return true;
        } catch {
            return false;
        }
    },
    
    // Получить всех преподавателей
    getTeachers: async () => {
        return apiRequest('/trainer');
    },
    
    // Получить расписание преподавателя
    getTeacherSchedule: async (teacherId) => {
        return apiRequest(`/trainerSchedule/${teacherId}`);
    },
    
    // Создать тренировку
    createTraining: async (teacherId, apprenticeId, numberGym, date, timeStart) => {
        const params = new URLSearchParams({
            numberGym: numberGym.toString(),
            date: date,
            timeStart: timeStart
        });
        
        return apiRequest(`/training/${teacherId}/${apprenticeId}?${params}`, 'POST');
    },
    
    // Получить тренировки ученика
    getStudentTrainings: async (studentId) => {
        return apiRequest(`/training/apprentice/${studentId}`);
    },
    
    // Получить тренировки преподавателя
    getTeacherTrainings: async (teacherId) => {
        return apiRequest(`/training/trainer/${teacherId}`);
    }
};

// Экспорт
window.api = api;