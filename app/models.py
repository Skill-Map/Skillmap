# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid

# ДОБАВЬТЕ этот глобальный словарь в начале файла
_registry = {}

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}  # Убедитесь, что эта строка есть
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    patronymic = Column(String)
    phone = Column(String, unique=True, index=True, nullable=True)  # Добавлено
    password = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    up_date = Column(JSON)  # Список дат
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
    advisor_user_id = Column(String, ForeignKey("users.id"))
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
    specialties = Column(JSON)  # Список строк
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

class TeacherSchedule(Base):
    __tablename__ = "teacher_schedules"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, ForeignKey("users.id"), primary_key=True)
    
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
    teacher_id = Column(String, ForeignKey("users.id"), nullable=False)
    apprentice_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(String, nullable=False)  # dd.MM.yyyy
    time_start = Column(String, nullable=False)  # HH:mm
    
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="trainings_as_teacher")
    apprentice = relationship("User", foreign_keys=[apprentice_id], back_populates="trainings_as_apprentice")