from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

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
    id: str
    type: UserType
    up_date: Optional[List[str]] = None
    reg_date: str

    class Config:
        orm_mode = True

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