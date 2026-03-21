from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.ruta import RutaRequest
from app.models.localidad import Localidad
from app.models.provincia import Provincia
from app.models.ruta import Ruta
import requests
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import urllib.parse
from sqlalchemy.orm import joinedload


router = APIRouter(prefix="/rutas", tags=["rutas"])


@router.post("/calcular")
def calcular_ruta(data: RutaRequest, db: Session = Depends(get_db)):
    
    load_dotenv()

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    origen = data.origen
    destino = data.destino

    loc_origen = db.get(Localidad, origen.localidad_id)
    loc_destino = db.get(Localidad, destino.localidad_id)

    prov_origen = loc_origen.provincia
    prov_destino = loc_destino.provincia

    direccion_origen = f"{origen.calle} {origen.altura}, {loc_origen.nombre}, {prov_origen.nombre}, AR"
    direccion_destino = f"{destino.calle} {destino.altura}, {loc_destino.nombre}, {prov_destino.nombre}, AR"
    
    ruta_guardada = db.query(Ruta).filter(
        Ruta.origen_texto == direccion_origen,
        Ruta.destino_texto == direccion_destino
    ).first()

    if ruta_guardada:
        print("No hubo que usar la api, ahorraste")
        return {
            "origen": direccion_origen,
            "destino": direccion_destino,
            "distancia": ruta_guardada.distancia_metros,
            "duracion": ruta_guardada.duracion_segundos,
            "mapa": ruta_guardada.mapa_url,
            "cache": True
        }

    direccion_origen_parsed = urllib.parse.quote(direccion_origen)
    direccion_destino_parsed = urllib.parse.quote(direccion_destino)
       

    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={direccion_origen_parsed}&destination={direccion_destino_parsed}&key={GOOGLE_API_KEY}"

    response = requests.get(url)

    data_maps = response.json()
    
    
    if data_maps["status"] != "OK":
        raise HTTPException(
            status_code=400,
            detail=f"Google Maps error: {data_maps['status']}"
        )
    
    leg = data_maps["routes"][0]["legs"][0]

    distancia = leg["distance"]["text"]
    duracion = leg["duration"]["text"]

    mapa_url = (
        "https://maps.googleapis.com/maps/api/staticmap?"
        f"size=600x400"
        f"&markers=color:green|{direccion_origen_parsed}"
        f"&markers=color:red|{direccion_destino_parsed}"
        f"&path=color:0x0000ff|weight:5|enc:{data_maps['routes'][0]['overview_polyline']['points']}"
        f"&key={GOOGLE_API_KEY}"
    )
    
    nueva_ruta = Ruta(
    origen_texto=direccion_origen,
    destino_texto=direccion_destino,
    distancia_metros=distancia,
    duracion_segundos=duracion,
    mapa_url=mapa_url
    )

    db.add(nueva_ruta)
    db.commit()
    
    return {
        "origen": direccion_origen,
        "destino": direccion_destino,
        "distancia": distancia,
        "duracion": duracion,
        "mapa": mapa_url
    }
