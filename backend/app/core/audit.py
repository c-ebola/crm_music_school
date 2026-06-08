from fastapi import Request

from app.core.security import decode_token
from app.services import audit_service

_MUTATING = {"POST", "PUT", "PATCH", "DELETE"}
_SKIP_PREFIXES = ("/api/auth",)   # вход логируется отдельно в auth.py

_RESOURCE_RU = {
    "leads": "лид/ученик",
    "subscriptions": "абонемент",
    "subscription-plans": "тариф абонемента",
    "payments": "оплата",
    "sessions": "занятие",
    "session-students": "запись на занятие",
    "schedule": "расписание",
    "lessons": "урок (тип)",
    "exams": "экзамен",
    "exam-sessions": "экзамен (проведение)",
    "commissions": "комиссия",
    "events": "концерт",
    "performances": "выступление",
    "performance-students": "участник концерта",
    "homeworks": "домашнее задание",
    "users": "пользователь",
    "branches": "филиал",
    "rooms": "кабинет",
    "disciplines": "дисциплина",
    "instruments": "инструмент",
    "roles": "роль",
}
_VERB_RU = {"POST": "Создание", "PUT": "Изменение", "PATCH": "Изменение", "DELETE": "Удаление"}


def _action_for(method: str, path: str) -> str:
    parts = [p for p in path.split("/") if p]      # ['api', 'subscriptions', '5']
    resource = parts[1] if len(parts) > 1 else ""
    ru = _RESOURCE_RU.get(resource, resource or "—")
    return f"{_VERB_RU.get(method, method)}: {ru}"


async def audit_middleware(request: Request, call_next):
    """Логирует изменяющие /api-запросы после ответа. Никогда не ломает запрос."""
    response = await call_next(request)
    try:
        method = request.method
        path = request.url.path
        if (
            method in _MUTATING
            and path.startswith("/api")
            and not any(path.startswith(p) for p in _SKIP_PREFIXES)
        ):
            actor_id = None
            auth = request.headers.get("authorization")
            if auth and auth.lower().startswith("bearer "):
                payload = decode_token(auth.split(" ", 1)[1])
                if payload:
                    actor_id = payload.get("sub")
            await audit_service.record(
                method=method, path=path, status_code=response.status_code,
                action=_action_for(method, path), actor_user_id=actor_id,
            )
    except Exception:
        pass
    return response