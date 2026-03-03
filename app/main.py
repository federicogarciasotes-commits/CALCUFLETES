from fastapi import FastAPI
from app.routers import auth
from app.routers import usuarios


app = FastAPI()

app.include_router(auth.router)

app.include_router(usuarios.router)

@app.get("/")
def root():
    return {"message": "Servidor funcionando"}

from app.database import engine, Base
from app.models import usuario

Base.metadata.create_all(bind=engine)