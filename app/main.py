import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
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


def is_winerror_10054(exception):
    return (
        sys.platform.startswith("win")
        and isinstance(exception, ConnectionResetError)
        and getattr(exception, "winerror", None) == 10054
    )


def ignore_winerror_10054(loop, context):
    exception = context.get("exception")
    if is_winerror_10054(exception):
        return
    loop.default_exception_handler(context)


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if sys.platform.startswith("win"):
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(ignore_winerror_10054)
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def ignore_client_connection_reset(request, call_next):
    try:
        return await call_next(request)
    except ConnectionResetError as e:
        if is_winerror_10054(e):
            return Response(status_code=499)
        raise

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
