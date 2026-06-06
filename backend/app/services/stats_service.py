from collections import defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch, BranchKind
from app.models.discipline import Discipline
from app.models.lead import Lead, StudentStatus
from app.models.lesson import Lesson
from app.models.payment import Payment, PaymentStatus
from app.models.role import Role
from app.models.session import Session
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User

RU = ["", "Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]


async def dashboard(db: AsyncSession) -> dict:
    today = date.today()

    # ученики 
    students = (await db.execute(select(Lead).where(Lead.is_student.is_(True)))).scalars().all()
    active = [s for s in students
              if s.student_status not in (StudentStatus.finished, StudentStatus.dropped)]
    student_branch = {s.id: s.branch_id for s in students}
    new_month = sum(
        1 for s in active
        if s.enrollment_date
        and s.enrollment_date.year == today.year
        and s.enrollment_date.month == today.month
    )

    # абонементы
    subs = (await db.execute(select(Subscription))).scalars().all()
    by_student = defaultdict(list)
    sub_student = {}
    for sub in subs:
        by_student[sub.student_id].append(sub)
        sub_student[sub.id] = sub.student_id

    def has_valid(student_id):
        for x in by_student.get(student_id, []):
            if (x.status != SubscriptionStatus.cancelled
                    and x.end_date >= today
                    and x.lessons_used < x.lessons_total):
                return True
        return False

    at_risk = sum(1 for s in active
                  if s.student_status == StudentStatus.paused or not has_valid(s.id))

    priced_by_branch = defaultdict(float)
    for sub in subs:
        if sub.status == SubscriptionStatus.cancelled:
            continue
        priced_by_branch[student_branch.get(sub.student_id)] += float(sub.price_paid)

    # платежи (подтверждённые)
    payments = (await db.execute(
        select(Payment).where(Payment.status == PaymentStatus.confirmed)
    )).scalars().all()
    rev_by_month = defaultdict(float)
    rev_by_branch = defaultdict(float)
    for p in payments:
        rev_by_month[(p.payment_date.year, p.payment_date.month)] += float(p.amount)
        sid = sub_student.get(p.subscription_id)
        if sid is not None:
            rev_by_branch[student_branch.get(sid)] += float(p.amount)

    cur_rev = rev_by_month.get((today.year, today.month), 0.0)
    pm = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    prev_rev = rev_by_month.get(pm, 0.0)

    seq = []
    for i in range(5, -1, -1):
        mm, yy = today.month - i, today.year
        while mm <= 0:
            mm += 12
            yy -= 1
        seq.append((yy, mm))
    revenue_by_month = [{"month": RU[mm], "amount": rev_by_month.get((yy, mm), 0.0)} for (yy, mm) in seq]

    # преподаватели
    teachers = (await db.execute(
        select(User).join(Role, User.role_id == Role.id).where(Role.code == "teacher")
    )).scalars().all()
    teach_by_branch = defaultdict(int)
    tname, tbranch = {}, {}
    for t in teachers:
        teach_by_branch[t.branch_id] += 1
        tname[t.id] = " ".join(filter(None, [t.last_name, t.first_name]))
        tbranch[t.id] = t.branch_id

    sess_rows = (await db.execute(
        select(Lesson.teacher_id, func.count(Session.id))
        .select_from(Session).join(Lesson, Session.lesson_id == Lesson.id)
        .group_by(Lesson.teacher_id)
    )).all()
    sess_count = {tid: cnt for (tid, cnt) in sess_rows if tid is not None}

    # филиалы (только учебные)
    stu_by_branch = defaultdict(int)
    for s in active:
        stu_by_branch[s.branch_id] += 1

    branches = (await db.execute(select(Branch).where(Branch.kind == BranchKind.school))).scalars().all()
    branch_name = {b.id: b.name for b in branches}
    branch_rows = []
    for b in branches:
        rev = rev_by_branch.get(b.id, 0.0)
        branch_rows.append({
            "name": b.name,
            "city": b.city,
            "students": stu_by_branch.get(b.id, 0),
            "teachers": teach_by_branch.get(b.id, 0),
            "revenue": rev,
            "debt": max(0.0, priced_by_branch.get(b.id, 0.0) - rev),
        })
    branch_rows.sort(key=lambda r: r["revenue"], reverse=True)

    top_teachers = sorted(
        ({"name": tname.get(tid, "#" + str(tid)),
          "branch": branch_name.get(tbranch.get(tid)),
          "sessions": cnt}
         for tid, cnt in sess_count.items() if tid in tname),
        key=lambda r: r["sessions"], reverse=True,
    )[:5]

    disc_count = defaultdict(int)
    for s in active:
        disc_count[s.discipline_id] += 1
    discs = (await db.execute(select(Discipline))).scalars().all()
    dname = {d.id: d.name for d in discs}
    disciplines = sorted(
        ({"name": dname.get(did, "—"), "students": cnt} for did, cnt in disc_count.items()),
        key=lambda r: r["students"], reverse=True,
    )[:6]

    return {
        "period": RU[today.month] + " " + str(today.year),
        "branches_count": len(branches),
        "kpi": {
            "revenue": cur_rev,
            "revenue_prev": prev_rev,
            "active_students": len(active),
            "new_students_month": new_month,
            "at_risk": at_risk,
        },
        "branches": branch_rows,
        "revenue_by_month": revenue_by_month,
        "top_teachers": top_teachers,
        "disciplines": disciplines,
    }
