# app/models/convocation_model.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date
from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ConvocationBase(BaseModel):
    """
    Base model for convocation information.
    """
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    start_date: date
    end_date: date
    is_active: bool = True

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

class ConvocationInDB(ConvocationInDBBase):
    """
    Model for convocation information stored in the database.
    """


# app/repositories/convocation_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.convocation_model import ConvocationInDB, ConvocationCreate, ConvocationUpdate, Convocation
from .base_repository import BaseRepository

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
            end_date=convocation.end_date,
            is_active=convocation.is_active
        )
        self.session.add(db_convocation)
        await self.session.commit()
        await self.session.refresh(db_convocation)
        return Convocation.from_orm(db_convocation)

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[Convocation]:
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

    async def get_by_id(self, convocation_id: int) -> Convocation:
        """
        Retrieve a convocation by ID.

        Args:
            convocation_id (int): The ID of the convocation to retrieve.

        Returns:
            Convocation: The retrieved convocation data.
        """
        result = await self.session.execute(select(ConvocationInDB).where(ConvocationInDB.id == convocation_id))
        db_convocation = result.scalar_one_or_none()
        if not db_convocation:
            raise ValueError(f"Convocation with id {convocation_id} not found")
        return Convocation.from_orm(db_convocation)

    async def update(self, convocation_id: int, convocation_update: ConvocationUpdate) -> Convocation:
        """
        Update an existing convocation.

        Args:
            convocation_id (int): The ID of the convocation to update.
            convocation_update (ConvocationUpdate): The data to update the convocation with.

        Returns:
            Convocation: The updated convocation data.
        """
        db_convocation = await self.get_by_id(convocation_id)
        for key, value in convocation_update.dict(exclude_unset=True).items():
            setattr(db_convocation, key, value)
        self.session.add(db_convocation)
        await self.session.commit()
        await self.session.refresh(db_convocation)
        return Convocation.from_orm(db_convocation)

    async def delete(self, convocation_id: int) -> Convocation:
        """
        Delete a convocation by ID.

        Args:
            convocation_id (int): The ID of the convocation to delete.

        Returns:
            Convocation: The deleted convocation data.
        """
        db_convocation = await self.get_by_id(convocation_id)
        await self.session.delete(db_convocation)
        await self.session.commit()
        return Convocation.from_orm(db_convocation)


# app/services/convocation_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.convocation_repository import ConvocationRepository
from ..models.convocation_model import ConvocationCreate, ConvocationUpdate, Convocation

class ConvocationService:
    def __init__(self, session: AsyncSession):
        """
        Initialize the convocation service.

        Args:
            session (AsyncSession): The database session.
        """
        self.repository = ConvocationRepository(session)

    async def create_convocation(self, convocation: ConvocationCreate) -> Convocation:
        """
        Create a new convocation.

        Args:
            convocation (ConvocationCreate): The convocation data to be created.

        Returns:
            Convocation: The created convocation data.
        """
        return await self.repository.create(convocation)

    async def get_all_convoations(self, skip: int = 0, limit: int = 10) -> list[Convocation]:
        """
        Retrieve a list of convocations.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[Convocation]: A list of convocation data.
        """
        return await self.repository.get_all(skip, limit)

    async def get_convocation_by_id(self, convocation_id: int) -> Convocation:
        """
        Retrieve a convocation by ID.

        Args:
            convocation_id (int): The ID of the convocation to retrieve.

        Returns:
            Convocation: The retrieved convocation data.
        """
        return await self.repository.get_by_id(convocation_id)

    async def update_convocation(self, convocation_id: int, convocation_update: ConvocationUpdate) -> Convocation:
        """
        Update an existing convocation.

        Args:
            convocation_id (int): The ID of the convocation to update.
            convocation_update (ConvocationUpdate): The data to update the convocation with.

        Returns:
            Convocation: The updated convocation data.
        """
        return await self.repository.update(convocation_id, convocation_update)

    async def delete_convocation(self, convocation_id: int) -> Convocation:
        """
        Delete a convocation by ID.

        Args:
            convocation_id (int): The ID of the convocation to delete.

        Returns:
            Convocation: The deleted convocation data.
        """
        return await self.repository.delete(convocation_id)


# app/routers/convocation_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.convocation_model import ConvocationCreate, ConvocationUpdate, Convocation
from ..dependencies import get_db
from ..services.convocation_service import ConvocationService

router = APIRouter(prefix="/convocations", tags=["Convocations"])

@router.post("/", response_model=Convocation)
async def create_convocation(convocation: ConvocationCreate, session: AsyncSession = Depends(get_db)):
    """
    Create a new convocation.

    Args:
        convocation (ConvocationCreate): The convocation data to be created.
        session (AsyncSession): The database session.

    Returns:
        Convocation: The created convocation data.
    """
    service = ConvocationService(session)
    return await service.create_convocation(convocation)

@router.get("/", response_model=list[Convocation])
async def get_all_convoations(skip: int = 0, limit: int = 10, session: AsyncSession = Depends(get_db)):
    """
    Retrieve a list of convocations.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        session (AsyncSession): The database session.

    Returns:
        List[Convocation]: A list of convocation data.
    """
    service = ConvocationService(session)
    return await service.get_all_convoations(skip, limit)

@router.get("/{convocation_id}", response_model=Convocation)
async def get_convocation_by_id(convocation_id: int, session: AsyncSession = Depends(get_db)):
    """
    Retrieve a convocation by ID.

    Args:
        convocation_id (int): The ID of the convocation to retrieve.
        session (AsyncSession): The database session.

    Returns:
        Convocation: The retrieved convocation data.
    """
    service = ConvocationService(session)
    try:
        return await service.get_convocation_by_id(convocation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{convocation_id}", response_model=Convocation)
async def update_convocation(convocation_id: int, convocation_update: ConvocationUpdate, session: AsyncSession = Depends(get_db)):
    """
    Update an existing convocation.

    Args:
        convocation_id (int): The ID of the convocation to update.
        convocation_update (ConvocationUpdate): The data to update the convocation with.
        session (AsyncSession): The database session.

    Returns:
        Convocation: The updated convocation data.
    """
    service = ConvocationService(session)
    try:
        return await service.update_convocation(convocation_id, convocation_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{convocation_id}", response_model=Convocation)
async def delete_convocation(convocation_id: int, session: AsyncSession = Depends(get_db)):
    """
    Delete a convocation by ID.

    Args:
        convocation_id (int): The ID of the convocation to delete.
        session (AsyncSession): The database session.

    Returns:
        Convocation: The deleted convocation data.
    """
    service = ConvocationService(session)
    try:
        return await service.delete_convocation(convocation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))