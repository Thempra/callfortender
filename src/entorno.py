# app/models/call_model.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CallBase(BaseModel):
    """
    Base model for call information.
    """
    caller_id: int = Field(..., description="ID of the caller")
    receiver_id: int = Field(..., description="ID of the receiver")
    duration: Optional[float] = Field(None, description="Duration of the call in seconds")


class CallCreate(CallBase):
    """
    Model for creating a new call.
    """


class CallUpdate(CallBase):
    """
    Model for updating an existing call.
    """


class CallInDBBase(CallBase):
    """
    Base model for call information stored in the database.
    """
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Call(CallInDBBase):
    """
    Model for call information returned to the client.
    """


# app/repositories/call_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.call_model import CallInDB, CallCreate, CallUpdate
from .base_repository import BaseRepository
from sqlalchemy.future import select


class CallRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """
        Initialize the call repository.

        Args:
            session (AsyncSession): The database session.
        """
        super().__init__(session)

    async def create(self, call: CallCreate) -> CallInDB:
        """
        Create a new call.

        Args:
            call (CallCreate): The call data to be created.

        Returns:
            CallInDB: The created call data.
        """
        db_call = CallInDB(
            caller_id=call.caller_id,
            receiver_id=call.receiver_id,
            duration=call.duration,
            created_at=datetime.utcnow()
        )
        self.session.add(db_call)
        await self.session.commit()
        await self.session.refresh(db_call)
        return db_call

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[CallInDB]:
        """
        Retrieve a list of calls.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[CallInDB]: A list of call data.
        """
        result = await self.session.execute(select(CallInDB).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_by_id(self, call_id: int) -> CallInDB:
        """
        Retrieve a call by ID.

        Args:
            call_id (int): The ID of the call to retrieve.

        Returns:
            CallInDB: The retrieved call data.
        """
        result = await self.session.execute(select(CallInDB).where(CallInDB.id == call_id))
        db_call = result.scalar_one_or_none()
        if not db_call:
            raise ValueError(f"Call with id {call_id} not found")
        return db_call

    async def update(self, call_id: int, call_update: CallUpdate) -> CallInDB:
        """
        Update an existing call.

        Args:
            call_id (int): The ID of the call to update.
            call_update (CallUpdate): The data to update the call with.

        Returns:
            CallInDB: The updated call data.
        """
        db_call = await self.get_by_id(call_id)
        for key, value in call_update.dict(exclude_unset=True).items():
            setattr(db_call, key, value)
        self.session.add(db_call)
        await self.session.commit()
        await self.session.refresh(db_call)
        return db_call

    async def delete(self, call_id: int) -> CallInDB:
        """
        Delete a call by ID.

        Args:
            call_id (int): The ID of the call to delete.

        Returns:
            CallInDB: The deleted call data.
        """
        db_call = await self.get_by_id(call_id)
        await self.session.delete(db_call)
        await self.session.commit()
        return db_call


# app/services/call_service.py

from typing import List
from ..models.call_model import CallCreate, CallUpdate, Call
from ..repositories.call_repository import CallRepository


class CallService:
    def __init__(self, call_repo: CallRepository):
        """
        Initialize the call service.

        Args:
            call_repo (CallRepository): The call repository.
        """
        self.call_repo = call_repo

    async def create_call(self, call: CallCreate) -> Call:
        """
        Create a new call.

        Args:
            call (CallCreate): The call data to be created.

        Returns:
            Call: The created call data.
        """
        return await self.call_repo.create(call)

    async def get_all_calls(self, skip: int = 0, limit: int = 10) -> List[Call]:
        """
        Retrieve a list of calls.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[Call]: A list of call data.
        """
        return await self.call_repo.get_all(skip, limit)

    async def get_call_by_id(self, call_id: int) -> Call:
        """
        Retrieve a call by ID.

        Args:
            call_id (int): The ID of the call to retrieve.

        Returns:
            Call: The retrieved call data.
        """
        return await self.call_repo.get_by_id(call_id)

    async def update_call(self, call_id: int, call_update: CallUpdate) -> Call:
        """
        Update an existing call.

        Args:
            call_id (int): The ID of the call to update.
            call_update (CallUpdate): The data to update the call with.

        Returns:
            Call: The updated call data.
        """
        return await self.call_repo.update(call_id, call_update)

    async def delete_call(self, call_id: int) -> Call:
        """
        Delete a call by ID.

        Args:
            call_id (int): The ID of the call to delete.

        Returns:
            Call: The deleted call data.
        """
        return await self.call_repo.delete(call_id)


# app/routers/call_router.py

from fastapi import APIRouter, Depends
from ..models.call_model import CallCreate, CallUpdate, Call
from ..services.call_service import CallService
from ..dependencies import get_call_processing_service


router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/", response_model=Call)
async def create_call(call: CallCreate, call_service: CallService = Depends(get_call_processing_service)):
    """
    Create a new call.

    Args:
        call (CallCreate): The call data to be created.
        call_service (CallService): The call service.

    Returns:
        Call: The created call data.
    """
    return await call_service.create_call(call)


@router.get("/", response_model=list[Call])
async def get_all_calls(skip: int = 0, limit: int = 10, call_service: CallService = Depends(get_call_processing_service)):
    """
    Retrieve a list of calls.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        call_service (CallService): The call service.

    Returns:
        List[Call]: A list of call data.
    """
    return await call_service.get_all_calls(skip, limit)


@router.get("/{call_id}", response_model=Call)
async def get_call_by_id(call_id: int, call_service: CallService = Depends(get_call_processing_service)):
    """
    Retrieve a call by ID.

    Args:
        call_id (int): The ID of the call to retrieve.
        call_service (CallService): The call service.

    Returns:
        Call: The retrieved call data.
    """
    return await call_service.get_call_by_id(call_id)


@router.put("/{call_id}", response_model=Call)
async def update_call(call_id: int, call_update: CallUpdate, call_service: CallService = Depends(get_call_processing_service)):
    """
    Update an existing call.

    Args:
        call_id (int): The ID of the call to update.
        call_update (CallUpdate): The data to update the call with.
        call_service (CallService): The call service.

    Returns:
        Call: The updated call data.
    """
    return await call_service.update_call(call_id, call_update)


@router.delete("/{call_id}", response_model=Call)
async def delete_call(call_id: int, call_service: CallService = Depends(get_call_processing_service)):
    """
    Delete a call by ID.

    Args:
        call_id (int): The ID of the call to delete.
        call_service (CallService): The call service.

    Returns:
        Call: The deleted call data.
    """
    return await call_service.delete_call(call_id)


# app/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .repositories.call_repository import CallRepository
from .services.call_service import CallService


def get_call_repo(session: AsyncSession = Depends(get_db)) -> CallRepository:
    """
    Dependency to get the call repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        CallRepository: The call repository.
    """
    return CallRepository(session)


def get_call_processing_service(call_repo: CallRepository = Depends(get_call_repo)) -> CallService:
    """
    Dependency to get the call processing service.

    Args:
        call_repo (CallRepository): The call repository.

    Returns:
        CallService: The call service.
    """
    return CallService(call_repo)