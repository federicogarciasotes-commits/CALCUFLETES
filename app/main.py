from fastapi import FastAPI
from app.routers import auth
from app.routers import usuarios
from app.routers import origenes
from app.database import engine, Base
from app.models import usuario
from app.routers import transportistas
from app.routers import provincias
from app.routers import localidades
from app.routers import transportistas



app = FastAPI()

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(origenes.router)
app.include_router(transportistas.router)
app.include_router(provincias.router)
app.include_router(localidades.router)
app.include_router(transportistas.router)


@app.get("/")
def root():
    return {"message": "Servidor funcionando"}
    

Base.metadata.create_all(bind=engine)

