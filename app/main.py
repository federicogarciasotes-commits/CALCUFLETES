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

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

allow_origin_regex = os.getenv("CORS_ORIGIN_REGEX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
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