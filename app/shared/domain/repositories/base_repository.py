from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import Mapped, Session
from sqlalchemy.orm.interfaces import ORMOption

from app.infraestructure.database.database import Base


@dataclass
class Model:
    id: Mapped[UUID]
    deleted_at: Mapped[datetime | None]


class BaseRepository[ModelT: Base]:
    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    @property
    def _columns(self) -> type[Model]:
        return cast(type[Model], self.model)

    def _apply_options(
        self, stmt: Select, options: Sequence[ORMOption] | None
    ) -> Select:
        if options:
            stmt = stmt.options(*options)
        return stmt

    def _has_soft_delete(self) -> bool:
        return hasattr(self.model, "deleted_at")

    def _not_deleted(self) -> list[ColumnElement[bool]]:
        if not self._has_soft_delete():
            return []
        return [self._columns.deleted_at.is_(None)]

    def _select(
        self,
        *conditions: ColumnElement[bool],
        include_deleted: bool = False,
    ) -> Select:
        where: list[ColumnElement[bool]] = list(conditions)

        if not include_deleted:
            where.extend(self._not_deleted())

        return select(self.model).where(*where)

    def _count(self, stmt: Select) -> int:
        return (
            self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )

    def _paginate(self, stmt: Select, page: int, size: int) -> tuple[Select, int]:
        total = self._count(stmt.order_by(None))
        return stmt.offset((page - 1) * size).limit(size), total

    def get(
        self,
        id_: UUID,
        options: Sequence[ORMOption] | None = None,
        include_deleted: bool = False,
    ) -> ModelT | None:
        stmt = self._select(self._columns.id == id_, include_deleted=include_deleted)
        return self.session.scalar(self._apply_options(stmt, options))

    def get_many(
        self,
        ids: Sequence[UUID],
        options: Sequence[ORMOption] | None = None,
        include_deleted: bool = False,
    ) -> list[ModelT]:
        if not ids:
            return []

        stmt = self._select(self._columns.id.in_(ids), include_deleted=include_deleted)

        return list(
            self.session.scalars(self._apply_options(stmt, options)).unique().all()
        )

    def find_one(
        self,
        *conditions: ColumnElement[bool],
        options: Sequence[ORMOption] | None = None,
        include_deleted: bool = False,
    ) -> ModelT | None:
        stmt = self._select(*conditions, include_deleted=include_deleted)
        return self.session.scalar(self._apply_options(stmt, options))

    def find_all(
        self,
        *conditions: ColumnElement[bool],
        options: Sequence[ORMOption] | None = None,
        order_by: Sequence[Any] | None = None,
        include_deleted: bool = False,
    ) -> list[ModelT]:
        stmt = self._select(*conditions, include_deleted=include_deleted)

        if order_by:
            stmt = stmt.order_by(*order_by)

        return list(
            self.session.scalars(self._apply_options(stmt, options)).unique().all()
        )

    def exists(
        self,
        *conditions: ColumnElement[bool],
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(self._columns.id).where(*conditions)

        if not include_deleted:
            stmt = stmt.where(*self._not_deleted())

        return bool(self.session.scalar(select(stmt.exists())))

    def count(
        self,
        *conditions: ColumnElement[bool],
        include_deleted: bool = False,
    ) -> int:
        return self._count(self._select(*conditions, include_deleted=include_deleted))

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        return entity

    def add_all(self, entities: Sequence[ModelT]) -> Sequence[ModelT]:
        self.session.add_all(entities)
        return entities

    def soft_delete(self, entity: ModelT) -> None:
        cast(Model, entity).deleted_at = datetime.now(UTC)

    def destroy(self, entity: ModelT) -> None:
        self.session.delete(entity)
