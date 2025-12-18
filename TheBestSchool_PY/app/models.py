# models.py - ПОЛНОСТЬЮ ПЕРЕПИСАННЫЙ ФАЙЛ
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Создаем базовый класс для моделей
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    # UUID как первичный ключ
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    patronymic = Column(String)
    phone = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    up_date = Column(JSON)
    reg_date = Column(DateTime, server_default=func.now())
    type = Column(String, nullable=False)  # admin, apprentice, teacher, moderator
    
    # Поля для Admin
    super_permissions = Column(Boolean, default=False)
    can_manage_roles = Column(Boolean, default=False)
    can_manage_billing = Column(Boolean, default=False)
    can_impersonate = Column(Boolean, default=False)
    last_audit_action = Column(DateTime)
    
    # Поля для Apprentice
    status = Column(String, default="active")
    track_id = Column(String)
    group_code = Column(String)
    advisor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    hours_per_week = Column(Integer)
    progress_percent = Column(Float, default=0)
    credits_earned = Column(Integer, default=0)
    enrollment_date = Column(String)  # dd.MM.yyyy
    expected_graduation = Column(String)  # dd.MM.yyyy
    
    # Поля для Teacher
    hire_date = Column(String)  # dd.MM.yyyy
    department = Column(String)
    title = Column(String)
    bio = Column(Text)
    specialties = Column(JSON)
    office_hours = Column(String)
    teacher_hours_per_week = Column(Integer)
    rating = Column(Float, default=0)
    
    # Поля для Moderator
    assigned_scope = Column(String)
    permissions_scope = Column(String)
    on_call = Column(Boolean, default=False)
    warnings_issued = Column(Integer, default=0)
    users_banned = Column(Integer, default=0)
    last_action_at = Column(DateTime)
    
    # Связи
    advisor = relationship("User", remote_side=[id], foreign_keys=[advisor_user_id])
    trainings_as_teacher = relationship("Training", foreign_keys="Training.teacher_id", back_populates="teacher")
    trainings_as_apprentice = relationship("Training", foreign_keys="Training.apprentice_id", back_populates="apprentice")
    schedule = relationship("TeacherSchedule", back_populates="teacher", uselist=False)
    user_courses = relationship("UserCourseProgress", back_populates="user", cascade="all, delete-orphan")
    vacancy_requests = relationship("UserVacancyRequest", back_populates="user", cascade="all, delete-orphan")
    assignments_given = relationship("LessonAssignment", foreign_keys="LessonAssignment.assigned_by", back_populates="teacher")
    assignments_received = relationship("LessonAssignment", foreign_keys="LessonAssignment.user_id", back_populates="user")
    submissions = relationship("LessonSubmission", back_populates="user")

class TeacherSchedule(Base):
    __tablename__ = "teacher_schedules"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    
    monday_start = Column(String)
    monday_end = Column(String)
    tuesday_start = Column(String)
    tuesday_end = Column(String)
    wednesday_start = Column(String)
    wednesday_end = Column(String)
    thursday_start = Column(String)
    thursday_end = Column(String)
    friday_start = Column(String)
    friday_end = Column(String)
    saturday_start = Column(String)
    saturday_end = Column(String)
    sunday_start = Column(String)
    sunday_end = Column(String)
    
    teacher = relationship("User", back_populates="schedule")

class Training(Base):
    __tablename__ = "trainings"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    number_gym = Column(Integer, nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    apprentice_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(String, nullable=False)  # dd.MM.yyyy
    time_start = Column(String, nullable=False)  # HH:mm
    
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="trainings_as_teacher")
    apprentice = relationship("User", foreign_keys=[apprentice_id], back_populates="trainings_as_apprentice")

class Course(Base):
    __tablename__ = "courses"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)
    category_name = Column(String, nullable=False)
    category_color = Column(String, default="#1A535C")
    icon = Column(String)
    duration = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_public = Column(Boolean, default=True)

    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan")
    vacancies = relationship("CourseVacancy", back_populates="course", cascade="all, delete-orphan")
    user_progresses = relationship("UserCourseProgress", back_populates="course", cascade="all, delete-orphan")
    generated_requests = relationship("UserVacancyRequest", back_populates="generated_course")

class CourseModule(Base):
    __tablename__ = "course_modules"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    recommended_time = Column(String)

    course = relationship("Course", back_populates="modules")
    lessons = relationship("CourseLesson", back_populates="module", cascade="all, delete-orphan")
    user_progresses = relationship("UserCourseProgress", back_populates="current_module")

class CourseLesson(Base):
    __tablename__ = "course_lessons"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"), nullable=False, index=True)
    order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    pptx_url = Column(Text, nullable=True)
    homework_url = Column(Text, nullable=True)

    module = relationship("CourseModule", back_populates="lessons")
    assignments = relationship("LessonAssignment", back_populates="lesson", cascade="all, delete-orphan")

class Vacancy(Base):
    __tablename__ = "vacancies"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hh_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False, index=True)
    company = Column(String)
    salary = Column(String)
    experience = Column(String)
    employment = Column(String)
    description = Column(Text)
    skills = Column(JSON)
    url = Column(String)
    parsed_at = Column(DateTime, server_default=func.now())

    courses = relationship("CourseVacancy", back_populates="vacancy")

class CourseVacancy(Base):
    __tablename__ = "course_vacancies"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    vacancy_id = Column(UUID(as_uuid=True), ForeignKey("vacancies.id"), nullable=False)

    course = relationship("Course", back_populates="vacancies")
    vacancy = relationship("Vacancy", back_populates="courses")

class UserCourseProgress(Base):
    __tablename__ = "user_course_progress"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    current_module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"))
    completed_lessons = Column(JSON, default=list)
    progress_percent = Column(Float, default=0.0)
    started_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="user_courses")
    course = relationship("Course", back_populates="user_progresses")
    current_module = relationship("CourseModule", back_populates="user_progresses")

class UserVacancyRequest(Base):
    __tablename__ = "user_vacancy_requests"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    vacancy_title = Column(String, nullable=False)
    vacancy_links = Column(JSON, nullable=False)
    user_level = Column(String)
    status = Column(String, default="pending")
    analysis_result = Column(JSON)
    generated_course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)

    user = relationship("User", back_populates="vacancy_requests")
    generated_course = relationship("Course", back_populates="generated_requests")

class LessonAssignment(Base):
    __tablename__ = "lesson_assignments"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("course_lessons.id"), nullable=False, index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="assigned")  # assigned, submitted, reviewed, closed
    note = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="assignments_received")
    lesson = relationship("CourseLesson", back_populates="assignments")
    teacher = relationship("User", foreign_keys=[assigned_by], back_populates="assignments_given")
    submissions = relationship("LessonSubmission", back_populates="assignment", cascade="all, delete-orphan")

class LessonSubmission(Base):
    __tablename__ = "lesson_submissions"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("lesson_assignments.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    file_url = Column(Text, nullable=False)
    filename = Column(String, nullable=True)
    status = Column(String, default="sent")  # sent | processing | accepted | rejected
    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    assignment = relationship("LessonAssignment", back_populates="submissions")
    user = relationship("User", back_populates="submissions")

class TeacherCourseAssignment(Base):
    """Назначение преподавателя на курс (админом)"""
    __tablename__ = "teacher_course_assignments"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # admin
    assigned_at = Column(DateTime, server_default=func.now())
    status = Column(String, default="active")  # active, inactive
    
    # Связи
    teacher = relationship("User", foreign_keys=[teacher_id], backref="course_assignments")
    course = relationship("Course", backref="teacher_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])