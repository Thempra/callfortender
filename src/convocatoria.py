from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List
from datetime import date

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
    titulo = Column(String, index=True)
    descripcion = Column(String)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)

# Database setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Dependency to get the convocatoria repository
class ConvocatoriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, convocatoria: ConvocatoriaCreate) -> Convocatoria:
        db_convocatoria = ConvocatoriaModel(**convocatoria.dict())
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
        db_convocatoria = await self.get_by_id(convocatoria_id)
        for key, value in convocatoria_update.dict(exclude_unset=True).items():
            setattr(db_convocatoria, key, value)
        self.session.add(db_convocatoria)
        await self.session.commit()
        await self.session.refresh(db_convocatoria)
        return Convocatoria.from_orm(db_convocatoria)

    async def delete(self, convocatoria_id: int) -> Convocatoria:
        db_convocatoria = await self.get_by_id(convocatoria_id)
        await self.session.delete(db_convocatoria)
        await self.session.commit()
        return Convocatoria.from_orm(db_convocatoria)

def get_convocatoria_repo(session: AsyncSession = Depends(get_db)) -> ConvocatoriaRepository:
    return ConvocatoriaRepository(session)

# CRUD endpoints
@app.post("/convocatorias/", response_model=Convocatoria, status_code=201)
async def create_convocatoria(convocatoria: ConvocatoriaCreate, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Create a new convocatoria.
    
    Args:
        convocatoria (ConvocatoriaCreate): The convocatoria data to create.
        repo (ConvocatoriaRepository): The repository for convocatorias.

    Returns:
        Convocatoria: The created convocatoria.
    """
    return await repo.create(convocatoria)

@app.get("/convocatorias/", response_model=List[Convocatoria], status_code=200)
async def read_convocatorias(repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Get all convocatorias.

    Args:
        repo (ConvocatoriaRepository): The repository for convocatorias.

    Returns:
        List[Convocatoria]: A list of all convocatorias.
    """
    return await repo.get_all()

@app.get("/convocatorias/{convocatoria_id}", response_model=Convocatoria, status_code=200)
async def read_convocatoria(convocatoria_id: int, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Get a single convocatoria by ID.

    Args:
        convocatoria_id (int): The ID of the convocatoria to retrieve.
        repo (ConvocatoriaRepository): The repository for convocatorias.

    Returns:
        Convocatoria: The retrieved convocatoria.
    """
    try:
        return await repo.get_by_id(convocatoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/convocatorias/{convocatoria_id}", response_model=Convocatoria, status_code=200)
async def update_convocatoria(convocatoria_id: int, convocatoria_update: ConvocatoriaUpdate, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Update a convocatoria by ID.

    Args:
        convocatoria_id (int): The ID of the convocatoria to update.
        convocatoria_update (ConvocatoriaUpdate): The data to update the convocatoria with.
        repo (ConvocatoriaRepository): The repository for convocatorias.

    Returns:
        Convocatoria: The updated convocatoria.
    """
    try:
        return await repo.update(convocatoria_id, convocatoria_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/convocatorias/{convocatoria_id}", response_model=Convocatoria, status_code=200)
async def delete_convocatoria(convocatoria_id: int, repo: ConvocatoriaRepository = Depends(get_convocatoria_repo)):
    """
    Delete a convocatoria by ID.

    Args:
        convocatoria_id (int): The ID of the convocatoria to delete.
        repo (ConvocatoriaRepository): The repository for convocatorias.

    Returns:
        Convocatoria: The deleted convocatoria.
    """
    try:
        return await repo.delete(convocatoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))