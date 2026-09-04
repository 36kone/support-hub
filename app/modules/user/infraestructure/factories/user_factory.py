from app.services.logs.audit_log_service import AuditLogService
from app.services.user.user_service import UserService
from sqlalchemy.orm import Session


def build_user_service(session: Session) -> UserService:
    return UserService(
        session=session,
        repository=UserRepository(session),
        user_session_service=build_user_session_service(session),
        audit_log_service=AuditLogService(session),
    )
