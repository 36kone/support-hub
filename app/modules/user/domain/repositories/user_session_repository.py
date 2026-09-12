from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select, update

from app.modules.user.infraestructure.models.user_session_model import UserSession
from app.shared.domain.repositories.base_repository import BaseRepository


class UserSessionRepository(BaseRepository[UserSession]):
    """Synchronous repository retained for domain-level consumers."""

    model = UserSession

    def get_by_user_id(self, user_id: UUID) -> UserSession | None:
        return self.session.scalar(
            self._select(UserSession.user_id == user_id)
            .where(UserSession.revoked_at.is_(None))
            .order_by(UserSession.created_at.desc())
        )

    def get_push_token_by_user_id(self, user_id: UUID) -> str | None:
        # Push tokens do not belong to the current session model.
        return None

    def search(self, user_id: UUID | None = None, is_revoked: bool | None = None) -> list[UserSession]:
        statement = self._select()
        if user_id is not None:
            statement = statement.where(UserSession.user_id == user_id)
        if is_revoked is not None:
            statement = statement.where(
                UserSession.revoked_at.is_not(None)
                if is_revoked
                else UserSession.revoked_at.is_(None)
            )
        return list(self.session.scalars(statement.order_by(UserSession.created_at.desc())).all())

    def revoke(self, id_: UUID, current_user_id: UUID | None = None) -> None:
        self.session.execute(
            update(UserSession)
            .where(and_(UserSession.id == id_, UserSession.revoked_at.is_(None)))
            .values(revoked_at=datetime.now(UTC), revoked_by=current_user_id)
        )

    def get_active_ids_by_user_id(self, user_id: UUID) -> list[UUID]:
        return list(
            self.session.scalars(
                select(UserSession.id).where(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                )
            ).all()
        )

    def revoke_by_user_id(self, user_id: UUID) -> list[UUID]:
        result = self.session.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .returning(UserSession.id)
        )
        return list(result.scalars().all())
