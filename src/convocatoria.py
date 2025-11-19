from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List
from datetime import date
from sqlalchemy.future import select

app = FastAPI()

# Pydantic models
class ConvocatoriaBase(BaseModel):
    titulo: str = Field(..., min_length=5, max_length=100)
    descripcion: str = Field(..., min_length=10)
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

# SQLAlchemy models
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ConvocatoriaModel(Base):
    __tablename__ = "convocatorias"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
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

# Dependencies
def get_convocatoria_repo(session: AsyncSession = Depends(get_db)):
    return ConvocatoriaRepository(session)

# Repository
class ConvocatoriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, convocatoria: ConvocatoriaCreate) -> Convocatoria:
        db_convocatoria = ConvocatoriaModel(
            titulo=convocatoria.titulo,
            descripcion=convocatoria.descripcion,
            fecha_inicio=convocatoria.fecha_inicio,
            fecha_fin=convocatoria.fecha_fin
        )
        self.session.add(db_convocatoria)
        await self.session.commit()
        await self.session.refresh(db_convocatoria)
        return Convocatoria.from_orm(db_convocatoria)

    async def get_all(self) -> List[Convocatoria]:
        result = await self.session.execute(select(ConvocatoriaModel))
        return [Convocatoria.from_orm(convocatoria) for convocatoria in result.scalars().all()]

    async def get_by_id(self, convocatoria_id: int) -> Convocatoria:
        result = await self.session.execute(select(ConvocatoriaModel).where(ConvocatoriaModel.id == convocatoria_id))
        db_convocatoria = result.scalar_one_or_none()
        if not db_convocatoria:
            raise ValueError(f"Convocatoria with id {convocatoria_id} not found")
        return Convocatoria.from_orm(db_convocatoria)

    async def update(self, convocatoria_id: int, convocatoria_update: ConvocatoriaUpdate) -> Convocatoria:
        result = await self.session.execute(select(ConvocatoriaModel).where(ConvocatoriaModel.id == convocatoria_id))
        db_convocatoria = result.scalar_one_or_none()
        if not db_convocatoria:
            raise ValueError(f"Convocatoria with id {convocatoria_id} not found")
        
        update_data = convocatoria_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_convocatoria, key, value)

        await self.session.commit()
        await self.session.refresh(db_convocatoria)
        return Convocatoria.from_orm(db_convocatoria)