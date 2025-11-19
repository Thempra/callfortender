# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import get_call_service
from .schemas.call_schema import CallCreate, CallResponse
from .services.call_service import CallService

app = FastAPI()

@app.post("/calls/", response_model=CallResponse)
async def create_call(call: CallCreate, call_service: CallService = Depends(get_call_service)):
    try:
        created_call = await call_service.create_call(call)
        return created_call
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(call_id: int, call_service: CallService = Depends(get_call_service)):
    try:
        call = await call_service.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        return call
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# app/schemas/call_schema.py
from pydantic import BaseModel, Field

class CallCreate(BaseModel):
    caller_id: int = Field(..., description="ID of the caller")
    receiver_id: int = Field(..., description="ID of the receiver")
    duration: float = Field(..., description="Duration of the call in seconds")

class CallResponse(CallCreate):
    id: int

# app/services/call_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from .repositories.call_repository import CallRepository
from .schemas.call_schema import CallCreate, CallResponse

class CallService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CallRepository(session)

    async def create_call(self, call: CallCreate) -> CallResponse:
        db_call = await self.repository.create(call)
        return CallResponse.from_orm(db_call)

    async def get_call(self, call_id: int) -> CallResponse:
        db_call = await self.repository.get_by_id(call_id)
        if not db_call:
            raise ValueError(f"Call with id {call_id} not found")
        return CallResponse.from_orm(db_call)

# app/repositories/call_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.call_model import Call, CallCreate
from .base_repository import BaseRepository

class CallRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(self, call: CallCreate) -> Call:
        db_call = Call(
            caller_id=call.caller_id,
            receiver_id=call.receiver_id,
            duration=call.duration
        )
        self.session.add(db_call)
        await self.session.commit()
        await self.session.refresh(db_call)
        return db_call

    async def get_by_id(self, call_id: int) -> Call:
        result = await self.session.execute(select(Call).where(Call.id == call_id))
        db_call = result.scalar_one_or_none()
        return db_call

# app/models/call_model.py
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()

class CallCreate(BaseModel):
    caller_id: int = Field(..., description="ID of the caller")
    receiver_id: int = Field(..., description="ID of the receiver")
    duration: float = Field(..., description="Duration of the call in seconds")

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    duration = Column(Float, nullable=False)

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .repositories.call_repository import CallRepository
from .services.call_service import CallService

def get_call_repo(session: AsyncSession = Depends(get_db)) -> CallRepository:
    return CallRepository(session)

def get_call_service(call_repo: CallRepository = Depends(get_call_repo)) -> CallService:
    return CallService(call_repo)