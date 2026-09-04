from app.services.user.user_session_service import UserSessionService
from sqlalchemy.orm import Session


def build_user_session_service(session: Session) -> UserSessionService:
    return UserSessionService(
        session=session,
        repository=UserSessionRepository(session),
    )
