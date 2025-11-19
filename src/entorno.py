# app/call/__init__.py

from .call_service import CallService
from .call_repository import CallRepository


# app/call/call_model.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class CallBase(BaseModel):
    """
    Base model for call information.
    """
    caller_id: int = Field(..., description="ID of the caller")
    receiver_id: int = Field(..., description="ID of the receiver")
    call_start_time: datetime = Field(..., description="Start time of the call")

class CallCreate(CallBase):
    """
    Model for creating a new call.
    """

class CallUpdate(BaseModel):
    """
    Model for updating an existing call.
    """
    call_end_time: Optional[datetime] = Field(None, description="End time of the call")

class CallInDBBase(CallBase):
    id: int
    call_end_time: Optional[datetime]

    class Config:
        orm_mode = True

class Call(CallInDBBase):
    """
    Model for call information returned to the client.
    """

class CallInDB(CallInDBBase):
    """
    Model for call information stored in the database.
    """


# app/call/call_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.call_model import CallInDB, CallCreate, CallUpdate, Call
from .base_repository import BaseRepository

class CallRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """
        Initialize the call repository.

        Args:
            session (AsyncSession): The database session.
        """
        super().__init__(session)

    async def create(self, call: CallCreate) -> Call:
        """
        Create a new call.

        Args:
            call (CallCreate): The call data to be created.

        Returns:
            Call: The created call data.
        """
        db_call = CallInDB(
            caller_id=call.caller_id,
            receiver_id=call.receiver_id,
            call_start_time=call.call_start_time
        )
        self.session.add(db_call)
        await self.session.commit()
        await self.session.refresh(db_call)
        return Call.from_orm(db_call)

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[Call]:
        """
        Retrieve a list of calls.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[Call]: A list of call data.
        """
        result = await self.session.execute(select(CallInDB).offset(skip).limit(limit))
        return [Call.from_orm(call) for call in result.scalars().all()]

    async def get_by_id(self, call_id: int) -> Call:
        """
        Retrieve a call by ID.

        Args:
            call_id (int): The ID of the call to retrieve.

        Returns:
            Call: The retrieved call data.
        """
        result = await self.session.execute(select(CallInDB).where(CallInDB.id == call_id))
        db_call = result.scalar_one_or_none()
        if not db_call:
            raise ValueError(f"Call with id {call_id} not found")
        return Call.from_orm(db_call)

    async def update(self, call_id: int, call_update: CallUpdate) -> Call:
        """
        Update an existing call.

        Args:
            call_id (int): The ID of the call to update.
            call_update (CallUpdate): The data to update the call with.

        Returns:
            Call: The updated call data.
        """
        db_call = await self.get_by_id(call_id)
        for key, value in call_update.dict(exclude_unset=True).items():
            setattr(db_call, key, value)
        self.session.add(db_call)
        await self.session.commit()
        await self.session.refresh(db_call)
        return Call.from_orm(db_call)

    async def delete(self, call_id: int) -> Call:
        """
        Delete a call by ID.

        Args:
            call_id (int): The ID of the call to delete.

        Returns:
            Call: The deleted call data.
        """
        db_call = await self.get_by_id(call_id)
        await self.session.delete(db_call)
        await self.session.commit()
        return Call.from_orm(db_call)


# app/call/call_service.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from .call_repository import CallRepository
from ..models.call_model import CallCreate, CallUpdate, Call

class CallService:
    def __init__(self, session: AsyncSession):
        """
        Initialize the call service.

        Args:
            session (AsyncSession): The database session.
        """
        self.repository = CallRepository(session)

    async def create_call(self, call: CallCreate) -> Call:
        """
        Create a new call.

        Args:
            call (CallCreate): The call data to be created.

        Returns:
            Call: The created call data.
        """
        return await self.repository.create(call)

    async def get_all_calls(self, skip: int = 0, limit: int = 10) -> List[Call]:
        """
        Retrieve a list of calls.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[Call]: A list of call data.
        """
        return await self.repository.get_all(skip, limit)

    async def get_call_by_id(self, call_id: int) -> Call:
        """
        Retrieve a call by ID.

        Args:
            call_id (int): The ID of the call to retrieve.

        Returns:
            Call: The retrieved call data.
        """
        return await self.repository.get_by_id(call_id)

    async def update_call(self, call_id: int, call_update: CallUpdate) -> Call:
        """
        Update an existing call.

        Args:
            call_id (int): The ID of the call to update.
            call_update (CallUpdate): The data to update the call with.

        Returns:
            Call: The updated call data.
        """
        return await self.repository.update(call_id, call_update)

    async def delete_call(self, call_id: int) -> Call:
        """
        Delete a call by ID.

        Args:
            call_id (int): The ID of the call to delete.

        Returns:
            Call: The deleted call data.
        """
        return await self.repository.delete(call_id)


# app/call/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .call_repository import CallRepository
from .call_service import CallService

def get_call_repo(session: AsyncSession = Depends(get_db)) -> CallRepository:
    """
    Dependency to get the call repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        CallRepository: The call repository.
    """
    return CallRepository(session)

def get_call_service(call_repo: CallRepository = Depends(get_call_repo)) -> CallService:
    """
    Dependency to get the call service.

    Args:
        call_repo (CallRepository): The call repository.

    Returns:
        CallService: The call service.
    """
    return CallService(call_repo)


# app/call/router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.call_model import CallCreate, CallUpdate, Call
from .dependencies import get_call_service

router = APIRouter(prefix="/calls", tags=["calls"])

@router.post("/", response_model=Call)
async def create_call(call: CallCreate, call_service: CallService = Depends(get_call_service)):
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
async def get_all_calls(skip: int = 0, limit: int = 10, call_service: CallService = Depends(get_call_service)):
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
async def get_call_by_id(call_id: int, call_service: CallService = Depends(get_call_service)):
    """
    Retrieve a call by ID.

    Args:
        call_id (int): The ID of the call to retrieve.
        call_service (CallService): The call service.

    Returns:
        Call: The retrieved call data.
    """
    try:
        return await call_service.get_call_by_id(call_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{call_id}", response_model=Call)
async def update_call(call_id: int, call_update: CallUpdate, call_service: CallService = Depends(get_call_service)):
    """
    Update an existing call.

    Args:
        call_id (int): The ID of the call to update.
        call_update (CallUpdate): The data to update the call with.
        call_service (CallService): The call service.

    Returns:
        Call: The updated call data.
    """
    try:
        return await call_service.update_call(call_id, call_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{call_id}", response_model=Call)
async def delete_call(call_id: int, call_service: CallService = Depends(get_call_service)):
    """
    Delete a call by ID.

    Args:
        call_id (int): The ID of the call to delete.
        call_service (CallService): The call service.

    Returns:
        Call: The deleted call data.
    """
    try:
        return await call_service.delete_call(call_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))