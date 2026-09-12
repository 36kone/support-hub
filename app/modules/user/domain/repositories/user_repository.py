from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import ColumnElement, or_, select

from app.modules.user.infraestructure.models.user_model import User
from app.shared.domain.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Synchronous repository retained for domain-level consumers."""

    model = User

    def _exists_with_value(
        self, condition: ColumnElement[bool], exclude_id: UUID | None = None
    ) -> bool:
        if exclude_id is not None:
            return self.exists(condition, User.id != exclude_id)
        return self.exists(condition)

    def exists_by_phone(self, phone: str, exclude_id: UUID | None = None) -> bool:
        return self._exists_with_value(User.phone == phone, exclude_id)

    def exists_by_email(self, email: str, exclude_id: UUID | None = None) -> bool:
        return self._exists_with_value(User.email == email.lower(), exclude_id)

    def get_by_email(self, email: str) -> User | None:
        return self.find_one(User.email == email.lower(), User.is_active.is_(True))

    def get_by_password_reset_token(self, token: str) -> User | None:
        return self.find_one(
            User.password_recovery == token,
            User.password_recovery_expire >= datetime.now(UTC),
        )

    def find_active_non_super_user_ids(self) -> list[UUID]:
        return list(
            self.session.scalars(
                select(User.id).where(
                    User.is_super_user.is_(False),
                    User.is_active.is_(True),
                    User.deleted_at.is_(None),
                )
            ).all()
        )

    def search(self, keyword: str | None = None) -> list[User]:
        statement = self._select()
        if keyword:
            value = f"%{keyword.strip()}%"
            statement = statement.where(or_(User.name.ilike(value), User.email.ilike(value)))
        return list(self.session.scalars(statement.order_by(User.name)).all())
