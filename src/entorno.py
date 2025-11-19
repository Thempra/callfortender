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
from sqlalchemy.future import select
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
            raise ValueError("Call not found")
        return Call.from_orm(db_call)