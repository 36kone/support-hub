from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from app.models import User, UserSession, VersionControl
from app.schemas import UserSessionSearchRequest
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from app.shared.domain.repositories.base_repository import BaseRepository


def _default_search_options() -> list[ORMOption]:
    return [
        selectinload(UserSession.user).load_only(User.name),
        selectinload(UserSession.version).load_only(
            VersionControl.id, VersionControl.version, VersionControl.build_number
        ),
        selectinload(UserSession.who_revoked).load_only(User.name),
    ]


class UserSessionRepository(BaseRepository[UserSession]):
    model = UserSession

    def get(
        self,
        id_: UUID,
        options: Sequence[ORMOption] | None = None,
        include_deleted: bool = False,
    ) -> UserSession | None:
        stmt = self._select(UserSession.id == id_, include_deleted=include_deleted)

        return self.session.scalar(self._apply_options(stmt, options))

    def get_by_user_id(
        self,
        user_id: UUID,
        options: Sequence[ORMOption] | None = None,
    ) -> UserSession | None:
        stmt = self._select(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            include_deleted=True,
        ).order_by(UserSession.created_at.desc())

        return self.session.scalar(self._apply_options(stmt, options))

    def get_push_token_by_user_id(self, user_id: UUID) -> str | None:
        return self.session.scalar(
            select(UserSession.push_token).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        )

    def search(
        self,
        filters: UserSessionSearchRequest,
        options: Sequence[ORMOption] | None = None,
    ) -> tuple[list[UserSession], int]:
        stmt = (
            self._select(User.deleted_at.is_(None), include_deleted=True)
            .join(UserSession.user)
            .outerjoin(UserSession.version)
        )

        if filters.keyword:
            like = f"%{filters.keyword.strip()}%"

            stmt = stmt.where(
                or_(
                    User.name.ilike(like),
                    VersionControl.build_number.ilike(like),
                    VersionControl.version.ilike(like),
                )
            )

        if filters.user_id:
            stmt = stmt.where(UserSession.user_id == filters.user_id)

        if filters.revoked_by:
            stmt = stmt.where(UserSession.revoked_by == filters.revoked_by)

        if filters.is_revoked is not None:
            stmt = stmt.where(
                UserSession.revoked_at.is_not(None)
                if filters.is_revoked
                else UserSession.revoked_at.is_(None)
            )

        stmt = stmt.distinct()
        paginated, total = self._paginate(stmt, filters.page, filters.size)
        paginated = paginated.order_by(UserSession.created_at.desc())

        items = list(
            self.session.scalars(
                self._apply_options(
                    paginated,
                    options if options is not None else _default_search_options(),
                )
            )
            .unique()
            .all()
        )

        return items, total

    def revoke(self, id_: UUID, current_user_id: UUID | None = None) -> None:
        self.session.execute(
            update(UserSession)
            .where(and_(UserSession.id == id_, UserSession.revoked_at.is_(None)))
            .values(
                revoked_at=datetime.now(UTC),
                revoked_by=current_user_id if current_user_id else None,
            )
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
                and_(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            )
            .values(revoked_at=datetime.now(UTC))
            .returning(UserSession.id)
        )

        return list(result.scalars().all())
