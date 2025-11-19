# app/models/convocation_model.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select  # Importar select para consultas asincrónicas

Base = declarative_base()

class ConvocationBase(BaseModel):
    """
    Base model for convocation information.
    """
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    start_date: date
    end_date: date

class ConvocationCreate(ConvocationBase):
    """
    Model for creating a new convocation.
    """

class ConvocationUpdate(ConvocationBase):
    """
    Model for updating an existing convocation.
    """

class ConvocationInDBBase(ConvocationBase):
    id: int

    class Config:
        orm_mode = True

class Convocation(ConvocationInDBBase):
    """
    Model for convocation information returned to the client.
    """

class ConvocationInDB(Base):
    __tablename__ = 'convocations'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)


# app/repositories/convocation_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.convocation_model import ConvocationInDB, ConvocationCreate, ConvocationUpdate, Convocation
from .base_repository import BaseRepository
from typing import List

class ConvocationRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """
        Initialize the convocation repository.

        Args:
            session (AsyncSession): The database session.
        """
        super().__init__(session)

    async def create(self, convocation: ConvocationCreate) -> Convocation:
        """
        Create a new convocation.

        Args:
            convocation (ConvocationCreate): The convocation data to be created.

        Returns:
            Convocation: The created convocation data.
        """
        db_convocation = ConvocationInDB(
            title=convocation.title,
            description=convocation.description,
            start_date=convocation.start_date,
            end_date=convocation.end_date
        )
        self.session.add(db_convocation)
        await self.session.commit()
        await self.session.refresh(db_convocation)
        return Convocation.from_orm(db_convocation)

    async def get_all(self, skip: int = 0, limit: int = 10) -> List[Convocation]:
        """
        Retrieve a list of convocations.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[Convocation]: A list of convocation data.
        """
        result = await self.session.execute(select(ConvocationInDB).offset(skip).limit(limit))
        return [Convocation.from_orm(convocation) for convocation in result.scalars().all()]

    async def get_by_id(self, convocation_id: int) -> Optional[Convocation]:
        """
        Retrieve a convocation by ID.

        Args:
            convocation_id (int): The ID of the convocation to retrieve.

        Returns:
            Optional[Convocation]: The retrieved convocation data or None if not found.
        """
        result = await self.session.execute(select(ConvocationInDB).where(ConvocationInDB.id == convocation_id))
        db_convocation = result.scalars().first()
        return Convocation.from_orm(db_convocation) if db_convocation else None