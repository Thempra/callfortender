from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

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

    async def delete(self, convocatoria_id: int) -> ConvocatoriaInDB:
        db_convocatoria = await self.get_by_id(convocatoria_id)
        await self.session.delete(db_convocatoria)
        await self.session.commit()
        return db_convocatoria

# Dependency to get the convocatoria repository
def get_convocatoria_repo(session: AsyncSession = Depends(get_db)) -> ConvocatoriaRepository:
    return ConvocatoriaRepository(session)

# CRUD endpoints for Convocatoria
@app.post("/convocatorias/", response_model=Convocatoria, status_code=201)
async def create_convocatoria(convocatoria: ConvocatoriaCreate, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Create a new convocatoria.
    """
    db_convocatoria = await repo.create(convocatoria)
    return db_convocatoria

@app.get("/convocatorias/", response_model=List[Convocatoria])
async def read_convocatorias(skip: int = 0, limit: int = 10, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Retrieve a list of convocatorias.
    """
    return await repo.get_all(skip, limit)

@app.get("/convocatorias/{convocatoria_id}", response_model=Convocatoria)
async def read_convocatoria(convocatoria_id: int, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Retrieve a single convocatoria by ID.
    """
    try:
        return await repo.get_by_id(convocatoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/convocatorias/{convocatoria_id}", response_model=Convocatoria)
async def update_convocatoria(convocatoria_id: int, convocatoria_update: ConvocatoriaUpdate, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Update a convocatoria by ID.
    """
    try:
        return await repo.update(convocatoria_id, convocatoria_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/convocatorias/{convocatoria_id}", response_model=Convocatoria)
async def delete_convocatoria(convocatoria_id: int, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Delete a convocatoria by ID.
    """
    try:
        return await repo.delete(convocatoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))