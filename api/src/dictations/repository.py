from typing import TypeVar

from sqlalchemy import delete
from api.core.logging import get_logger
from api.src.dictations.schemas import BaseModel as SchemaBaseModel
from api.src.dictations.models import (
    DictationsModel,
    UserEditsModel,
    UserPreferencesModel,
)
from typing import Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


SchemaType = TypeVar("SchemaType", bound=SchemaBaseModel)
ModelType = Union[DictationsModel, UserEditsModel, UserPreferencesModel]


class BaseRepository:

    def __init__(self, session: AsyncSession, model: ModelType):
        self.session = session
        self.model = model

    async def create(self, schema: SchemaType) -> ModelType:
        """create new record"""

        # todo: add some format of duplication check

        item = self.model(**schema.model_dump())

        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        return item

    async def update(self, id: int, schema: SchemaType) -> ModelType:
        """update record by id"""

        item = await self.get_by_id(id)

        for key, value in schema.model_dump().items():
            setattr(item, key, value)

        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        return item

    async def get_by_id(self, id: int) -> ModelType:
        """get record by id"""

        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[ModelType]:
        """get all records"""

        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int) -> list[ModelType]:
        """get records by user id"""

        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()


class DictationsRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DictationsModel)


class UserEditsRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserEditsModel)


class UserPreferencesRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserPreferencesModel)
