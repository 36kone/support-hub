from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import ColumnElement, and_, or_, select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.interfaces import ORMOption

from app.enums import CustomerStatusEnum
from app.enums.user.user_enum import UserStatusEnum
from app.models import Customer, Team, User, UserProfile
from app.schemas import UserSearchRequest
from app.shared.domain.repositories.base_repository import BaseRepository


def _default_get_options() -> list[ORMOption]:
    return [
        joinedload(User.teams).load_only(Team.id, Team.name),
        joinedload(User.profile).load_only(UserProfile.id, UserProfile.name),
        joinedload(User.customer).load_only(
            Customer.id,
            Customer.name,
            Customer.email,
            Customer.document,
            Customer.document_type,
            Customer.cellphone,
        ),
        joinedload(User.who_created).load_only(User.name),
        joinedload(User.who_updated).load_only(User.name),
    ]


def _default_search_options() -> list[ORMOption]:
    return [
        selectinload(User.teams).load_only(Team.id, Team.name),
        selectinload(User.profile).load_only(UserProfile.id, UserProfile.name),
        selectinload(User.who_created).load_only(User.id, User.name),
        selectinload(User.who_updated).load_only(User.id, User.name),
    ]


class UserRepository(BaseRepository[User]):
    model = User

    def _exists_with_value(
        self,
        condition: ColumnElement[bool],
        exclude_id: UUID | None = None,
    ) -> bool:
        conditions = [condition]
        if exclude_id is not None:
            conditions.append(User.id != exclude_id)

        return self.exists(*conditions)

    def exists_by_phone(self, phone: str, exclude_id: UUID | None = None) -> bool:
        return self._exists_with_value(User.phone == phone, exclude_id)

    def exists_by_email(self, email: str, exclude_id: UUID | None = None) -> bool:
        return self._exists_with_value(User.email == email, exclude_id)

    def exists_by_username(self, username: str, exclude_id: UUID | None = None) -> bool:
        return self._exists_with_value(User.username == username, exclude_id)

    def exists_by_customer_id(
        self,
        customer_id: UUID,
        exclude_id: UUID | None = None,
    ) -> bool:
        return self._exists_with_value(User.customer_id == customer_id, exclude_id)

    def get(
        self,
        id_: UUID,
        options: Sequence[ORMOption] | None = None,
        include_deleted: bool = False,
    ) -> User | None:
        stmt = (
            self._select(
                User.id == id_,
                or_(
                    User.customer_id.is_(None),
                    and_(
                        Customer.deleted_at.is_(None),
                        Customer.status == CustomerStatusEnum.ACTIVE,
                    ),
                ),
                include_deleted=include_deleted,
            )
            .outerjoin(User.customer)
            .execution_options(populate_existing=True)
        )

        return self.session.scalar(
            self._apply_options(stmt, options if options is not None else _default_get_options())
        )

    def get_simple(self, id_: UUID, options: Sequence[ORMOption] | None = None) -> User | None:
        stmt = self._select(User.id == id_, include_deleted=True)

        return self.session.scalar(self._apply_options(stmt, options))

    def get_by_customer_id(
        self,
        customer_id: UUID,
        options: Sequence[ORMOption] | None = None,
    ) -> User | None:
        stmt = self._select(User.customer_id == customer_id)

        return self.session.scalar(self._apply_options(stmt, options))

    def get_by_email(
        self,
        email: str,
        options: Sequence[ORMOption] | None = None,
    ) -> User | None:
        stmt = self._select(
            User.email == email,
            User.status == UserStatusEnum.ACTIVE,
            or_(
                User.customer_id.is_(None),
                and_(
                    Customer.deleted_at.is_(None),
                    Customer.status == CustomerStatusEnum.ACTIVE,
                ),
            ),
        ).outerjoin(User.customer)

        return self.session.scalar(
            self._apply_options(
                stmt, options if options is not None else [joinedload(User.customer)]
            )
        )

    def get_by_username(
        self,
        username: str,
        options: Sequence[ORMOption] | None = None,
    ) -> User | None:
        stmt = self._select(
            User.username == username,
            User.status == UserStatusEnum.ACTIVE,
            or_(
                User.customer_id.is_(None),
                and_(
                    Customer.deleted_at.is_(None),
                    Customer.status == CustomerStatusEnum.ACTIVE,
                ),
            ),
        ).outerjoin(User.customer)

        return self.session.scalar(
            self._apply_options(
                stmt, options if options is not None else [joinedload(User.customer)]
            )
        )

    def get_by_password_reset_token(
        self,
        token: str,
        options: Sequence[ORMOption] | None = None,
    ) -> User | None:
        stmt = self._select(
            User.password_recovery == token,
            User.password_recovery_expire >= datetime.now(UTC),
            include_deleted=True,
        )

        return self.session.scalar(self._apply_options(stmt, options))

    def find_active_non_super_user_ids(self) -> list[UUID]:
        return list(
            self.session.scalars(
                select(User.id).where(
                    User.super_user.is_(False),
                    User.status == UserStatusEnum.ACTIVE,
                    User.deleted_at.is_(None),
                )
            ).all()
        )

    def search(
        self,
        filters: UserSearchRequest,
        options: Sequence[ORMOption] | None = None,
    ) -> tuple[list[User], int]:
        stmt = self._select().join(User.profile)

        if filters.keyword:
            like = f"%{filters.keyword.strip()}%"

            stmt = stmt.where(
                or_(
                    User.name.ilike(like),
                    User.email.ilike(like),
                    # busca pelo nome da equipe onde o usuário está vinculado
                    User.teams.any(Team.name.ilike(like)),
                    # busca pelo nome da equipe onde o usuário é gestor
                    User.managed_teams.any(Team.name.ilike(like)),
                )
            )

        if filters.roles:
            stmt = stmt.where(User.role.in_(filters.roles))

        if filters.status:
            stmt = stmt.where(User.status == filters.status)

        stmt = stmt.distinct()
        paginated, total = self._paginate(stmt, filters.page, filters.size)
        paginated = paginated.order_by(User.name.asc())

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
