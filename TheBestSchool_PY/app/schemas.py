from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from uuid import UUID

class UserType(str, Enum):
    ADMIN = "admin"
    APPRENTICE = "apprentice"
    TEACHER = "teacher"
    MODERATOR = "moderator"

# Базовые схемы
class UserBase(BaseModel):
    email: EmailStr
    surname: str
    name: str
    patronymic: Optional[str] = None
    active: bool = True
    phone: Optional[str] = Field(None, min_length=11, max_length=11)  # Добавляем phone

class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    type: UserType

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    surname: Optional[str] = None
    name: Optional[str] = None
    patronymic: Optional[str] = None
    password: Optional[str] = None
    active: Optional[bool] = None
    phone: Optional[str] = Field(None, min_length=11, max_length=11)  # Добавляем

class UserInDB(UserBase):
    id: UUID
    type: UserType
    up_date: Optional[List[str]] = None
    reg_date: str

    class Config:
        from_attributes = True

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    phone: str = Field(..., min_length=11, max_length=11)
    surname: str
    name: str
    patronymic: Optional[str] = None
    type: UserType = UserType.APPRENTICE  # По умолчанию студент


# Специфичные схемы
class AdminCreate(UserCreate):
    super_permissions: bool = False
    can_manage_roles: bool = False
    can_manage_billing: bool = False
    can_impersonate: bool = False

class AdminResponse(UserInDB):
    super_permissions: bool
    can_manage_roles: bool
    can_manage_billing: bool
    can_impersonate: bool
    last_audit_action: Optional[str] = None

class ApprenticeCreate(UserCreate):
    status: str = "active"
    track_id: str
    group_code: str
    advisor_user_id: Optional[str] = None
    hours_per_week: int
    progress_percent: float = 0
    credits_earned: int = 0
    enrollment_date: str
    expected_graduation: str

class ApprenticeResponse(UserInDB):
    status: str
    track_id: str
    group_code: str
    advisor_user_id: Optional[str] = None
    hours_per_week: int
    progress_percent: float
    credits_earned: int
    enrollment_date: str
    expected_graduation: str

class TeacherCreate(UserCreate):
    hire_date: str
    department: str
    title: str
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    office_hours: Optional[str] = None
    teacher_hours_per_week: int
    rating: float = 0

class TeacherResponse(UserInDB):
    hire_date: str
    department: str
    title: str
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    office_hours: Optional[str] = None
    teacher_hours_per_week: int
    rating: float

class ModeratorCreate(UserCreate):
    assigned_scope: str
    permissions_scope: str
    on_call: bool = False
    warnings_issued: int = 0
    users_banned: int = 0

class ModeratorResponse(UserInDB):
    assigned_scope: str
    permissions_scope: str
    on_call: bool
    warnings_issued: int
    users_banned: int
    last_action_at: Optional[str] = None

# Расписание
class TeacherScheduleBase(BaseModel):
    monday_start: Optional[str] = None
    monday_end: Optional[str] = None
    tuesday_start: Optional[str] = None
    tuesday_end: Optional[str] = None
    wednesday_start: Optional[str] = None
    wednesday_end: Optional[str] = None
    thursday_start: Optional[str] = None
    thursday_end: Optional[str] = None
    friday_start: Optional[str] = None
    friday_end: Optional[str] = None
    saturday_start: Optional[str] = None
    saturday_end: Optional[str] = None
    sunday_start: Optional[str] = None
    sunday_end: Optional[str] = None

class TeacherScheduleCreate(TeacherScheduleBase):
    pass

class TeacherScheduleResponse(TeacherScheduleBase):
    id: str
    teacher: TeacherResponse

# Тренировки
class TrainingBase(BaseModel):
    number_gym: int
    date: str  # dd.MM.yyyy
    time_start: str  # HH:mm

class TrainingCreate(TrainingBase):
    pass

class TrainingResponse(TrainingBase):
    id: int
    teacher: TeacherResponse
    apprentice: ApprenticeResponse

# Авторизация
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    user_type: Optional[str] = None

# Ответы API
class ApiResponse(BaseModel):
    result: Optional[dict] = None
    error: Optional[str] = None
    
# Схемы для курсов
class CourseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    category: str = Field(..., pattern="^(it|finance|law|geology|marketing|management)$")
    category_name: str
    category_color: str = Field(default="#1A535C", pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    duration: Optional[str] = None
    is_public: bool = Field(default=True)

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = Field(None, pattern="^(it|finance|law|geology|marketing|management)$")
    category_name: Optional[str] = None
    category_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    duration: Optional[str] = None
    is_public: Optional[bool] = None

class CourseResponse(CourseBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Схемы для модулей
class CourseModuleBase(BaseModel):
    order: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    recommended_time: Optional[str] = None

class CourseModuleCreate(CourseModuleBase):
    course_id: str

class CourseModuleUpdate(BaseModel):
    order: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    recommended_time: Optional[str] = None

class CourseModuleResponse(CourseModuleBase):
    id: UUID
    course_id: UUID

    class Config:
        from_attributes = True


class CourseLessonMaterial(BaseModel):
    pptx_url: Optional[str] = None
    homework_url: Optional[str] = None
    

class CourseLessonBase(BaseModel):
    order: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class CourseLessonCreate(BaseModel):
    module_id: UUID
    order: int
    title: str
    description: Optional[str] = None
    # материалы можно загружать отдельным endpoint'ом, но можно принимать ссылки:
    pptx_url: Optional[str] = None
    homework_url: Optional[str] = None

class CourseLessonUpdate(BaseModel):
    order: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class CourseLessonResponse(BaseModel):
    id: UUID
    module_id: UUID
    order: int
    title: str
    description: Optional[str]
    pptx_url: Optional[str] = None
    homework_url: Optional[str] = None

    class Config:
        from_attributes = True

# Схемы для вакансий
class VacancyBase(BaseModel):
    hh_id: str
    title: str
    company: Optional[str] = None
    salary: Optional[str] = None
    experience: Optional[str] = None
    employment: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    url: str

class VacancyCreate(VacancyBase):
    pass

class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    salary: Optional[str] = None
    experience: Optional[str] = None
    employment: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    url: Optional[str] = None

class VacancyResponse(VacancyBase):
    id: str
    parsed_at: datetime

    class Config:
        from_attributes = True

# Схемы для связи курса и вакансии
class CourseVacancyBase(BaseModel):
    course_id: str
    vacancy_id: str

class CourseVacancyCreate(CourseVacancyBase):
    pass

class CourseVacancyResponse(CourseVacancyBase):
    id: str

    class Config:
        from_attributes = True

# Схемы для прогресса пользователя
class UserCourseProgressBase(BaseModel):
    user_id: str
    course_id: str
    current_module_id: Optional[str] = None
    completed_lessons: List[str] = Field(default_factory=list)
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)

class UserCourseProgressCreate(UserCourseProgressBase):
    pass

class UserCourseProgressUpdate(BaseModel):
    current_module_id: Optional[str] = None
    completed_lessons: Optional[List[str]] = None
    progress_percent: Optional[float] = Field(None, ge=0.0, le=100.0)

class UserCourseProgressResponse(UserCourseProgressBase):
    id: str
    started_at: datetime
    last_accessed: Optional[datetime] = None

    class Config:
        from_attributes = True

# Схемы для запросов на анализ вакансий
class UserVacancyRequestBase(BaseModel):
    user_id: str
    vacancy_title: str
    vacancy_links: List[str] = Field(..., min_items=1)
    user_level: str = Field(..., pattern="^(intern|junior|middle|senior)$")

class UserVacancyRequestCreate(UserVacancyRequestBase):
    pass

class UserVacancyRequestUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|processing|completed|failed)$")
    analysis_result: Optional[dict] = None
    generated_course_id: Optional[str] = None

class UserVacancyRequestResponse(UserVacancyRequestBase):
    id: str
    status: str
    analysis_result: Optional[dict] = None
    generated_course_id: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Детальные схемы для отображения
class CourseDetailResponse(CourseResponse):
    modules: List["CourseModuleDetailResponse"] = []
    vacancies: List[VacancyResponse] = []

class CourseModuleDetailResponse(CourseModuleResponse):
    lessons: List[CourseLessonResponse] = []

# Для создания всего курса целиком (курс + модули + уроки)
class FullCourseCreate(BaseModel):
    course: CourseCreate
    modules: List[Dict[str, Any]] = Field(
        ...,
        description="Список модулей с уроками. Каждый модуль: {'module': CourseModuleCreate, 'lessons': List[CourseLessonCreate]}"
    )

# Схема для отправки вакансии с фронтенда
class VacancySubmissionRequest(BaseModel):
    vacancy_title: str = Field(..., min_length=1, max_length=200)
    vacancy_links: List[str] = Field(..., min_items=1)
    user_level: str = Field(..., pattern="^(intern|junior|middle|senior)$")

# Ответ после анализа вакансии
class VacancyAnalysisResponse(BaseModel):
    request_id: str
    status: str
    common_skills: List[str]
    required_skills: List[str]
    skill_gaps: List[str]
    estimated_duration: str
    weekly_hours: str
    generated_course_id: Optional[str] = None
    
class LessonSubmissionResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    user_id: str
    file_url: str
    filename: Optional[str]
    status: str
    grade: Optional[float]
    feedback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        
        
class LessonAssignmentResponse(BaseModel):
    id: UUID
    user_id: str
    lesson_id: UUID
    assigned_by: str
    assigned_at: datetime
    due_date: Optional[datetime]
    status: str
    note: Optional[str]

    class Config:
        from_attributes = True
        

class LessonSubmissionCreate(BaseModel):
    # будет multipart/form-data: file
    pass


class LessonAssignmentCreate(BaseModel):
    user_id: str
    lesson_id: UUID
    assigned_by: Optional[str] = None  # backend заполнит из current_user
    due_date: Optional[datetime] = None
    note: Optional[str] = None