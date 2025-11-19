from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from sqlalchemy.future import select

app = FastAPI()

# Pydantic models for Convocatoria
class ConvocatoriaBase(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=255)
    descripcion: str
    fecha_inicio: date
    fecha_fin: date

class ConvocatoriaCreate(ConvocatoriaBase):
    pass

class ConvocatoriaUpdate(ConvocatoriaBase):
    pass

class ConvocatoriaInDBBase(ConvocatoriaBase):
    id: int

    class Config:
        orm_mode = True

class Convocatoria(ConvocatoriaInDBBase):
    pass

# SQLAlchemy models for Convocatoria
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ConvocatoriaInDB(Base):
    __tablename__ = "convocatorias"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)

# Database setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Repository for Convocatoria
class ConvocatoriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, convocatoria: ConvocatoriaCreate) -> ConvocatoriaInDB:
        db_convocatoria = ConvocatoriaInDB(**convocatoria.dict())
        self.session.add(db_convocatoria)
        await self.session.commit()
        await self.session.refresh(db_convocatoria)
        return db_convocatoria

    async def get_all(self, skip: int = 0, limit: int = 10) -> List[ConvocatoriaInDB]:
        result = await self.session.execute(select(ConvocatoriaInDB).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_by_id(self, convocatoria_id: int) -> ConvocatoriaInDB:
        result = await self.session.execute(select(ConvocatoriaInDB).where(ConvocatoriaInDB.id == convocatoria_id))
        db_convocatoria = result.scalar_one_or_none()
        if not db_convocatoria:
            raise ValueError(f"Convocatoria with id {convocatoria_id} not found")
        return db_convocatoria

    async def update(self, convocatoria_id: int, convocatoria_update: ConvocatoriaUpdate) -> ConvocatoriaInDB:
        db_convocatoria = await self.get_by_id(convocatoria_id)
        for key, value in convocatoria_update.dict(exclude_unset=True).items():
            setattr(db_convocatoria, key, value)
        self.session.add(db_convocatoria)
        await self.session.commit()
        await self.session.refresh(db_convocatoria)
        return db_convocatoria