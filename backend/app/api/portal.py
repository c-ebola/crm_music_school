from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.db.session import get_db
from app.models.discipline import Discipline
from app.models.lead import Lead
from app.models.lesson import Lesson
from app.models.room import Room
from app.models.schedule import Schedule
from app.models.session import Session
from app.models.session_student import SessionStudent
from app.models.user import User
from datetime import date, timedelta
from app.schemas.schedule import ScheduleRead
from app.schemas.subscription import SubscriptionRead
from app.services import homework_service, schedule_service, subscription_service

router = APIRouter(prefix="/api/portal", tags=["portal"])


async def _my_lead(current: User, db: AsyncSession) -> Lead:
    res = await db.execute(select(Lead).where(Lead.user_id == current.id))
    lead = res.scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=403, detail="Раздел доступен только ученику")
    return lead


@router.get("/me")
async def my_profile(current: User = Depends(get_current_active_user),
                     db: AsyncSession = Depends(get_db)):
    lead = await _my_lead(current, db)
    disc = await db.get(Discipline, lead.discipline_id) if lead.discipline_id else None

    branch_name = None
    if lead.branch_id:
        from app.models.branch import Branch
        b = await db.get(Branch, lead.branch_id)
        branch_name = b.name if b else None

    teacher_name = None
    if lead.teacher_id:
        t = await db.get(User, lead.teacher_id)
        if t:
            teacher_name = " ".join(filter(None, [t.last_name, t.first_name])) or None

    return {
        "student_id": lead.id,
        "name": lead.student_full_name or lead.contact_full_name,
        "discipline": disc.name if disc else None,
        "branch": branch_name,
        "teacher": teacher_name,
        "level": lead.level.value if lead.level else None,
    }

@router.get("/schedule")
async def my_schedule(current: User = Depends(get_current_active_user),
                      db: AsyncSession = Depends(get_db)):
    lead = await _my_lead(current, db)
    session_ids = (await db.execute(
        select(SessionStudent.session_id).where(SessionStudent.student_id == lead.id)
    )).scalars().all()    
    if not session_ids:
        return []
    today = date.today()
    rows = (await db.execute(
        select(Schedule).where(
            Schedule.entity_type == "session",
            Schedule.entity_id.in_(session_ids),
            Schedule.date >= today,
        ).order_by(Schedule.date.asc(), Schedule.quant.asc())
    )).scalars().all()

    out = []
    for sch in rows:
        sess = await db.get(Session, sch.entity_id)
        if sess is None:
            continue
        status = sess.status.value if hasattr(sess.status, "value") else str(sess.status)
        if status == "cancelled":
            continue
        lesson = await db.get(Lesson, sess.lesson_id) if sess.lesson_id else None
        if sess is None:
            continue
        lesson = await db.get(Lesson, sess.lesson_id) if sess.lesson_id else None
        discipline = teacher = room_name = None
        if lesson is not None:
            if lesson.discipline_id:
                d = await db.get(Discipline, lesson.discipline_id)
                discipline = d.name if d else None
            if lesson.teacher_id:
                t = await db.get(User, lesson.teacher_id)
                if t:
                    teacher = " ".join(filter(None, [t.last_name, t.first_name])) or None
        if sess.room_id:
            r = await db.get(Room, sess.room_id)
            room_name = r.name if r else None
        out.append({
            "date": sch.date.isoformat(),
            "quant": sch.quant,
            "discipline": discipline,
            "teacher": teacher,
            "room": room_name,
            "status": status,
        })
    return out


@router.get("/homeworks")
async def my_homeworks(current: User = Depends(get_current_active_user),
                       db: AsyncSession = Depends(get_db)):
    lead = await _my_lead(current, db)
    return await homework_service.list_homeworks(db, student_id=lead.id)


@router.get("/subscriptions", response_model=list[SubscriptionRead])
async def my_subscriptions(current: User = Depends(get_current_active_user),
                           db: AsyncSession = Depends(get_db)):
    lead = await _my_lead(current, db)
    return await subscription_service.list_subscriptions(db, student_id=lead.id)


@router.get("/week", response_model=list[ScheduleRead])
async def my_week(week_start: date | None = None,
                  current: User = Depends(get_current_active_user),
                  db: AsyncSession = Depends(get_db)):
    lead = await _my_lead(current, db)
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    return await schedule_service.list_week_schedule(db, week_start=week_start, student_id=lead.id)

@router.get("/week", response_model=list[ScheduleRead])
async def my_week(week_start: date | None = None,
                  current: User = Depends(get_current_active_user),
                  db: AsyncSession = Depends(get_db)):
    lead = await _my_lead(current, db)
    return await schedule_service.list_week_schedule(db, week_start=week_start, student_id=lead.id)