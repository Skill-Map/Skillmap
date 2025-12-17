from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

import crud
import schemas
from database import get_db
from auth import get_current_user, require_role
import models

router = APIRouter(prefix="/trainerSchedule", tags=["schedule"])

@router.post("/{trainer_id}", response_model=schemas.TeacherScheduleResponse)
async def create_schedule(
    trainer_id: str,
    day: str = Query(..., description="Day of week: monday, tuesday, etc."),
    start_time: str = Query(..., description="Start time in HH:mm"),
    end_time: str = Query(..., description="End time in HH:mm"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Проверяем, что пользователь - учитель или админ
    if current_user.type not in ["admin", "teacher"] or (
        current_user.type == "teacher" and current_user.id != trainer_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Проверяем существование учителя
    teacher = await crud.get_user(db, trainer_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Создаем или обновляем расписание
    day_field_start = f"{day.lower()}_start"
    day_field_end = f"{day.lower()}_end"
    
    # Получаем текущее расписание
    current_schedule = await crud.get_schedule(db, trainer_id)
    schedule_data = {}
    
    if current_schedule:
        schedule_data = schemas.TeacherScheduleCreate(**{
            k: v for k, v in current_schedule.__dict__.items()
            if not k.startswith('_')
        })
    
    # Обновляем поле дня
    schedule_data_dict = schedule_data.dict() if schedule_data else {}
    schedule_data_dict[day_field_start] = start_time
    schedule_data_dict[day_field_end] = end_time
    
    updated_schedule = schemas.TeacherScheduleCreate(**schedule_data_dict)
    
    return await crud.create_or_update_schedule(db, trainer_id, updated_schedule)

@router.get("/{trainer_id}", response_model=schemas.TeacherScheduleResponse)
async def get_schedule(
    trainer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    schedule = await crud.get_schedule(db, trainer_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Проверяем права доступа
    if current_user.type != "admin" and current_user.id != trainer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return schedule

@router.delete("/{trainer_id}")
async def delete_schedule_day(
    trainer_id: str,
    day: str = Query(..., description="Day to clear: monday, tuesday, etc."),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type not in ["admin", "teacher"] or (
        current_user.type == "teacher" and current_user.id != trainer_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await crud.delete_schedule_day(db, trainer_id, day)
    if result is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return {"message": f"Schedule for {day} cleared successfully"}