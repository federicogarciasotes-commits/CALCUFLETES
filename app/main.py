from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth
from app.routers import usuarios
from app.routers import origenes
from app.routers import transportistas
from app.routers import provincias
from app.routers import localidades
from app.routers import rutas
from app.routers import productos
from app.routers import cotizaciones

from app.database import engine, Base
from app.models import usuario

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://192.168.0.170:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(origenes.router)
app.include_router(transportistas.router)
app.include_router(provincias.router)
app.include_router(localidades.router)
app.include_router(rutas.router)
app.include_router(productos.router)
app.include_router(cotizaciones.router)

@app.get("/")
def root():
    return {"message": "Servidor funcionando"}

Base.metadata.create_all(bind=engine)