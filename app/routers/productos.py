from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Producto, Subcategoria
from app.schemas.producto import ProductoCreate, ProductoRead, ProductoUpdate, SubcategoriaCreate, SubcategoriaRead, SubcategoriaUpdate
from app.auth.dependencies import get_current_user

def require_admin(user = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden realizar esta acción"
        )
    return user

router = APIRouter(tags=["Productos"])

# Crear
@router.post("/subcategorias", response_model=SubcategoriaRead)
def crear_subcategoria(
    sub: SubcategoriaCreate,
    db: Session = Depends(get_db),
    user = Depends(require_admin)
):

    existente = db.query(Subcategoria).filter(Subcategoria.nombre == sub.nombre).first()

    if existente:
        raise HTTPException(400, "La subcategoría ya existe")

    nueva = Subcategoria(**sub.model_dump())

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return nueva


# Listar subcategorías
@router.get("/subcategorias/", response_model=List[SubcategoriaRead])
def listar_subcategorias(db: Session = Depends(get_db)):
    return db.query(Subcategoria).all()


# Editar
@router.put("/subcategorias/{id}", response_model=SubcategoriaRead)
def editar_subcategoria(
    id: int,
    sub: SubcategoriaUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_admin)
):

    subcat = db.query(Subcategoria).filter(Subcategoria.id == id).first()

    if not subcat:
        raise HTTPException(404, "Subcategoría no encontrada")

    # evitar duplicados
    existente = db.query(Subcategoria)\
        .filter(Subcategoria.nombre == sub.nombre, Subcategoria.id != id)\
        .first()

    if existente:
        raise HTTPException(400, "Ya existe otra subcategoría con ese nombre")

    datos = sub.model_dump(exclude_unset=True)

    for campo, valor in datos.items():
        setattr(subcat, campo, valor)

    db.commit()
    db.refresh(subcat)

    return subcat


# Eliminar
@router.delete("/subcategorias/{id}")
def borrar_subcategoria(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(require_admin)
):

    subcat = db.query(Subcategoria).filter(Subcategoria.id == id).first()

    if not subcat:
        raise HTTPException(404, "Subcategoría no encontrada")

    # verificar si está asociada a productos
    if subcat.productos:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar la subcategoría porque está asociada a productos"
        )

    db.delete(subcat)
    db.commit()

    return {"mensaje": "Subcategoría eliminada"}
    

# Crear
@router.post("/productos", response_model=ProductoRead)
def crear_producto(
    prod: ProductoCreate,
    db: Session = Depends(get_db),
    user = Depends(require_admin)
):

    existente = db.query(Producto).filter(Producto.nombre == prod.nombre).first()

    if existente:
        raise HTTPException(400, "El producto ya existe")

    subcats = db.query(Subcategoria)\
        .filter(Subcategoria.id.in_(prod.subcategorias_ids)).all()

    if len(subcats) != len(prod.subcategorias_ids):
        raise HTTPException(404, "Alguna subcategoría no existe")

    nuevo = Producto(nombre=prod.nombre)
    nuevo.subcategorias = subcats

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo
    
    
# Listar productos
@router.get("/productos/", response_model=List[ProductoRead])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(Producto).all()


# Editar
@router.put("/productos/{id}", response_model=ProductoRead)
def editar_producto(
    id: int,
    prod: ProductoUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_admin)
):

    producto = db.query(Producto).filter(Producto.id == id).first()

    if not producto:
        raise HTTPException(404, "Producto no encontrado")
        
    existente = db.query(Producto)\
        .filter(Producto.nombre == prod.nombre, Producto.id != id)\
        .first()

    if existente:
        raise HTTPException(400, "Ya existe otro producto con ese nombre")

    datos = prod.model_dump(exclude_unset=True)

    if "nombre" in datos:
        producto.nombre = datos["nombre"]

    if "subcategorias_ids" in datos:
        subcats = db.query(Subcategoria)\
            .filter(Subcategoria.id.in_(datos["subcategorias_ids"])).all()

        if len(subcats) != len(datos["subcategorias_ids"]):
            raise HTTPException(404, "Alguna subcategoría no existe")

        producto.subcategorias = subcats

    db.commit()
    db.refresh(producto)

    return producto



# Eliminar
@router.delete("/productos/{id}")
def borrar_producto(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(require_admin)
):

    producto = db.query(Producto).filter(Producto.id == id).first()

    if not producto:
        raise HTTPException(404, "Producto no encontrado")

    db.delete(producto)
    db.commit()

    return {"mensaje": "Producto eliminado"}