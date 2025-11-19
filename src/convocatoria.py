from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

router = APIRouter()

# Pydantic models
class ConvocatoriaBase(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=100)
    descripcion: str
    fecha_inicio: date
    fecha_fin: date

class ConvocatoriaCreate(ConvocatoriaBase):
    pass

class ConvocatoriaUpdate(ConvocatoriaBase):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

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
    titulo = Column(String, index=True)
    descripcion = Column(String)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)

# Database session
from app.database import get_db

async def get_convocatoria_repo(session: AsyncSession = Depends(get_db)):
    return ConvocatoriaRepository(session)

class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

class ConvocatoriaRepository(BaseRepository):
    async def create(self, convocatoria: ConvocatoriaCreate) -> ConvocatoriaModel:
        db_convocatoria = ConvocatoriaModel(
            titulo=convocatoria.titulo,
            descripcion=convocatoria.descripcion,
            fecha_inicio=convocatoria.fecha_inicio,
            fecha_fin=convocatoria.fecha_fin
        )
        self.session.add(db_convocatoria)
        await self.session.commit()
        await self.session.refresh(db_convocatoria)
        return db_convocatoria

    async def get_all(self) -> List[ConvocatoriaModel]:
        result = await self.session.execute(select(ConvocatoriaModel))
        return result.scalars().all()

    async def get_by_id(self, convocatoria_id: int) -> ConvocatoriaModel:
        result = await self.session.execute(select(ConvocatoriaModel).where(ConvocatoriaModel.id == convocatoria_id))
        db_convocatoria = result.scalar_one_or_none()
        if not db_convocatoria:
            raise ValueError(f"Convocatoria with id {convocatoria_id} not found")
        return db_convocatoria

    async def update(self, convocatoria_id: int, convocatoria_update: ConvocatoriaUpdate) -> ConvocatoriaModel:
        db_convocatoria = await self.get_by_id(convocatoria_id)
        for key, value in convocatoria_update.dict(exclude_unset=True).items():
            setattr(db_convocatoria, key, value)
        self.session.add(db_convocatoria)
        await self.session.commit()
        await self.session.refresh(db_convocatoria)
        return db_convocatoria

    async def delete(self, convocatoria_id: int) -> ConvocatoriaModel:
        db_convocatoria = await self.get_by_id(convocatoria_id)
        await self.session.delete(db_convocatoria)
        await self.session.commit()
        return db_convocatoria

# CRUD endpoints
@router.post("/convocatorias/", response_model=Convocatoria, status_code=201)
async def create_convocatoria(convocatoria: ConvocatoriaCreate, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Create a new convocatoria.
    """
    db_convocatoria = await repo.create(convocatoria)
    return Convocatoria.from_orm(db_convocatoria)

@router.get("/convocatorias/", response_model=List[Convocatoria], status_code=200)
async def read_convocatorias(repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Get a list of all convocatorias.
    """
    db_convocatorias = await repo.get_all()
    return [Convocatoria.from_orm(convocatoria) for convocatoria in db_convocatorias]

@router.get("/convocatorias/{convocatoria_id}", response_model=Convocatoria, status_code=200)
async def read_convocatoria(convocatoria_id: int, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Get a single convocatoria by ID.
    """
    try:
        db_convocatoria = await repo.get_by_id(convocatoria_id)
        return Convocatoria.from_orm(db_convocatoria)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/convocatorias/{convocatoria_id}", response_model=Convocatoria, status_code=200)
async def update_convocatoria(convocatoria_id: int, convocatoria_update: ConvocatoriaUpdate, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Update a convocatoria by ID.
    """
    try:
        db_convocatoria = await repo.update(convocatoria_id, convocatoria_update)
        return Convocatoria.from_orm(db_convocatoria)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/convocatorias/{convocatoria_id}", response_model=Convocatoria, status_code=200)
async def delete_convocatoria(convocatoria_id: int, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Delete a convocatoria by ID.
    """
    try:
        db_convocatoria = await repo.delete(convocatoria_id)
        return Convocatoria.from_orm(db_convocatoria)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))