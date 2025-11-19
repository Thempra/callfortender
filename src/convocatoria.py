# app/models/convocation_model.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date
from sqlalchemy import Column, Integer, String, Date
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

from ..repositories.convocation_repository import ConvocationRepository
from ..models.convocation_model import ConvocationCreate, ConvocationUpdate, Convocation
from typing import List

class ConvocationService:
    def __init__(self, repository: ConvocationRepository):
        """
        Initialize the convocation service.

        Args:
            repository (ConvocationRepository): The convocation repository.
        """
        self.repository = repository

    async def create_convocation(self, convocation: ConvocationCreate) -> Convocation:
        """
        Create a new convocation.

        Args:
            convocation (ConvocationCreate): The convocation data to be created.

        Returns:
            Convocation: The created convocation data.
        """
        return await self.repository.create(convocation)

    async def get_all_convocations(self, skip: int = 0, limit: int = 10) -> List[Convocation]:
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


# app/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .repositories.convocation_repository import ConvocationRepository
from .services.convocation_service import ConvocationService

def get_convocation_repo(session: AsyncSession = Depends(get_db)) -> ConvocationRepository:
    """
    Dependency to get the convocation repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        ConvocationRepository: The convocation repository.
    """
    return ConvocationRepository(session)

def get_convocation_service(repo: ConvocationRepository = Depends(get_convocation_repo)) -> ConvocationService:
    """
    Dependency to get the convocation service.

    Args:
        repo (ConvocationRepository): The convocation repository.

    Returns:
        ConvocationService: The convocation service.
    """
    return ConvocationService(repo)


# app/routers/convocation_router.py

from fastapi import APIRouter, Depends, HTTPException
from ..models.convocation_model import ConvocationCreate, ConvocationUpdate, Convocation
from ..services.convocation_service import ConvocationService
from typing import List

router = APIRouter(prefix="/convocations", tags=["convocations"])

@router.post("/", response_model=Convocation)
async def create_convocation(convocation: ConvocationCreate, service: ConvocationService = Depends(get_convocation_service)):
    """
    Create a new convocation.

    Args:
        convocation (ConvocationCreate): The convocation data to be created.
        service (ConvocationService): The convocation service.

    Returns:
        Convocation: The created convocation data.
    """
    return await service.create_convocation(convocation)

@router.get("/", response_model=List[Convocation])
async def get_all_convocations(skip: int = 0, limit: int = 10, service: ConvocationService = Depends(get_convocation_service)):
    """
    Retrieve a list of convocations.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        service (ConvocationService): The convocation service.

    Returns:
        List[Convocation]: A list of convocation data.
    """
    return await service.get_all_convocations(skip, limit)

@router.get("/{convocation_id}", response_model=Convocation)
async def get_convocation_by_id(convocation_id: int, service: ConvocationService = Depends(get_convocation_service)):
    """
    Retrieve a convocation by ID.

    Args:
        convocation_id (int): The ID of the convocation to retrieve.
        service (ConvocationService): The convocation service.

    Returns:
        Convocation: The retrieved convocation data.
    """
    try:
        return await service.get_convocation_by_id(convocation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{convocation_id}", response_model=Convocation)
async def update_convocation(convocation_id: int, convocation_update: ConvocationUpdate, service: ConvocationService = Depends(get_convocation_service)):
    """
    Update an existing convocation.

    Args:
        convocation_id (int): The ID of the convocation to update.
        convocation_update (ConvocationUpdate): The data to update the convocation with.
        service (ConvocationService): The convocation service.

    Returns:
        Convocation: The updated convocation data.
    """
    try:
        return await service.update_convocation(convocation_id, convocation_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{convocation_id}", response_model=Convocation)
async def delete_convocation(convocation_id: int, service: ConvocationService = Depends(get_convocation_service)):
    """
    Delete a convocation by ID.

    Args:
        convocation_id (int): The ID of the convocation to delete.
        service (ConvocationService): The convocation service.

    Returns:
        Convocation: The deleted convocation data.
    """
    try:
        return await service.delete_convocation(convocation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))