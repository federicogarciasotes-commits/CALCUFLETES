import { useState, useEffect } from "react"
import api from "../services/api"

export default function ProductosAdmin() {
  const [vista, setVista] = useState("subcategorias") // "subcategorias" | "productos"

  return (
    <div>
      <div>
        <button onClick={() => setVista("subcategorias")}>Subcategorías</button>
        <button onClick={() => setVista("productos")}>Productos</button>
      </div>
      {vista === "subcategorias" ? <SubcategoriasPanel /> : <ProductosPanel />}
    </div>
  )
}

function SubcategoriasPanel() {
  const [lista, setLista] = useState([])
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")
  const [form, setForm] = useState({ nombre: "", largo: "", ancho: "", alto: "", peso: "" })
  const [originalForm, setOriginalForm] = useState(null)

  const cargar = () => api.get("/subcategorias/").then(r => setLista(r.data))
  useEffect(() => { cargar() }, [])

  // Auto-dismiss del error
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000)
      return () => clearTimeout(timer)
    }
  }, [error])

  const camposNumericos = ["largo", "ancho", "alto", "peso"]

  // Deshabilitar botón guardar
  const guardarDeshabilitado = (() => {
    if (!form.nombre.trim()) return true
    if (camposNumericos.some(c => form[c] === "" || isNaN(form[c]))) return true

    if (editandoId && originalForm) {
      const sinCambios =
        form.nombre === originalForm.nombre &&
        camposNumericos.every(c => String(form[c]) === String(originalForm[c]))
      if (sinCambios) return true
    }

    return false
  })()

  const guardar = async () => {
    setError("")
    if (!form.nombre.trim()) return setError("El nombre es obligatorio")
    if (camposNumericos.some(v => form[v] === "" || isNaN(form[v])))
      return setError("Largo, ancho, alto y peso son obligatorios y deben ser números")
    const body = {
      nombre: form.nombre,
      largo: Number(form.largo), ancho: Number(form.ancho),
      alto: Number(form.alto), peso: Number(form.peso)
    }
    try {
      if (editandoId) {
        await api.put(`/subcategorias/${editandoId}`, body)
      } else {
        await api.post("/subcategorias", body)
      }
      resetForm()
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
  }

  const editar = (s) => {
    const datos = { nombre: s.nombre, largo: s.largo, ancho: s.ancho, alto: s.alto, peso: s.peso }
    setEditandoId(s.id)
    setForm(datos)
    setOriginalForm(datos)
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar?")) return
    try {
      await api.delete(`/subcategorias/${id}`)
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
  }

  const resetForm = () => {
    setEditandoId(null)
    setOriginalForm(null)
    setForm({ nombre: "", largo: "", ancho: "", alto: "", peso: "" })
    setError("")
  }

  return (
    <div>
      <h3>{editandoId ? "Editar subcategoría" : "Nueva subcategoría"}</h3>
      <input placeholder="Nombre" value={form.nombre} onChange={e => setForm({...form, nombre: e.target.value})} />
      {["largo","ancho","alto","peso"].map(campo => (
        <input key={campo} placeholder={campo} type="number" value={form[campo]}
          onChange={e => setForm({...form, [campo]: e.target.value})} />
      ))}
      <button onClick={guardar} disabled={guardarDeshabilitado}>
        {editandoId ? "Guardar" : "Crear"}
      </button>
      <button onClick={resetForm}>Cancelar</button>
      {error && <p className="error">{error}</p>}

      <table>
        <thead><tr><th>Nombre</th><th>Largo</th><th>Ancho</th><th>Alto</th><th>Peso</th><th>Acciones</th></tr></thead>
        <tbody>
          {lista.map(s => (
            <tr key={s.id}>
              <td>{s.nombre}</td><td>{s.largo}</td><td>{s.ancho}</td><td>{s.alto}</td><td>{s.peso}</td>
              <td>
                <button onClick={() => editar(s)}>Editar</button>
                <button onClick={() => eliminar(s.id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ProductosPanel() {
  const [productos, setProductos] = useState([])
  const [subcategorias, setSubcategorias] = useState([])
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")
  const [form, setForm] = useState({ nombre: "", subcategorias_ids: [] })
  const [originalForm, setOriginalForm] = useState(null)
  const [busquedaSub, setBusquedaSub] = useState("")

  const subcategoriasFiltradas = subcategorias.filter(s =>
    s.nombre.toLowerCase().includes(busquedaSub.toLowerCase())
  )

  const cargar = () => api.get("/productos/").then(r => setProductos(r.data))
  useEffect(() => {
    cargar()
    api.get("/subcategorias/").then(r => setSubcategorias(r.data))
  }, [])

  // Auto-dismiss del error
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000)
      return () => clearTimeout(timer)
    }
  }, [error])

  // Deshabilitar botón guardar
  const guardarDeshabilitado = (() => {
    if (!form.nombre.trim()) return true
    if (form.subcategorias_ids.length === 0) return true

    if (editandoId && originalForm) {
      const mismoNombre = form.nombre === originalForm.nombre
      const mismasSubs =
        form.subcategorias_ids.length === originalForm.subcategorias_ids.length &&
        [...form.subcategorias_ids].sort().join() === [...originalForm.subcategorias_ids].sort().join()
      if (mismoNombre && mismasSubs) return true
    }

    return false
  })()

  const toggleSub = (id) => setForm(f => ({
    ...f,
    subcategorias_ids: f.subcategorias_ids.includes(id)
      ? f.subcategorias_ids.filter(x => x !== id)
      : [...f.subcategorias_ids, id]
  }))

  const guardar = async () => {
    setError("")
    if (!form.nombre.trim()) return setError("El nombre es obligatorio")
    if (form.subcategorias_ids.length === 0) return setError("Seleccioná al menos una subcategoría")
    try {
      if (editandoId) {
        await api.put(`/productos/${editandoId}`, form)
      } else {
        await api.post("/productos", form)
      }
      resetForm()
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
  }

  const editar = (p) => {
    const datos = { nombre: p.nombre, subcategorias_ids: p.subcategorias.map(s => s.id) }
    setEditandoId(p.id)
    setForm(datos)
    setOriginalForm(datos)
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar?")) return
    try {
      await api.delete(`/productos/${id}`)
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
  }

  const resetForm = () => {
    setEditandoId(null)
    setOriginalForm(null)
    setForm({ nombre: "", subcategorias_ids: [] })
    setBusquedaSub("")
    setError("")
  }

  return (
    <div>
      <h3>{editandoId ? "Editar producto" : "Nuevo producto"}</h3>
      <input placeholder="Nombre" value={form.nombre} onChange={e => setForm({...form, nombre: e.target.value})} />
      <div>
        <div>
          <strong>Subcategorías:</strong>
          <input
            placeholder="Buscar subcategoría..."
            value={busquedaSub}
            onChange={e => setBusquedaSub(e.target.value)}
          />

          {subcategoriasFiltradas.length > 0 && (
            <div style={{
              maxHeight: "180px",
              overflowY: "auto",
              border: "1px solid #ddd",
              borderRadius: "6px",
              padding: "4px",
              marginTop: "4px"
            }}>
              {subcategoriasFiltradas.map(s => (
                <div key={s.id}
                  style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px" }}>
                  <span>{s.nombre}</span>
                  <button onClick={() => {
                    toggleSub(s.id)
                    setBusquedaSub("")
                  }}>
                    {form.subcategorias_ids.includes(s.id) ? "✓" : "+ Agregar"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {form.subcategorias_ids.length > 0 && (
            <div style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "6px",
              marginTop: "8px",
              maxHeight: "100px",
              overflowY: "auto",
              border: "1px solid #ddd",
              borderRadius: "8px",
              padding: "8px"
            }}>
              {form.subcategorias_ids.map(id => {
                const sub = subcategorias.find(s => s.id === id)
                return sub ? (
                  <span key={id} style={{
                    background: "#e0e0e0",
                    borderRadius: "12px",
                    padding: "3px 10px",
                    fontSize: "13px",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px"
                  }}>
                    {sub.nombre}
                    <button onClick={() => toggleSub(id)}
                      style={{ background: "none", border: "none", cursor: "pointer", fontWeight: "bold", padding: 0 }}>
                      ×
                    </button>
                  </span>
                ) : null
              })}
            </div>
          )}
        </div>
      </div>

      <button onClick={guardar} disabled={guardarDeshabilitado}>
        {editandoId ? "Guardar" : "Crear"}
      </button>
      <button onClick={resetForm}>Cancelar</button>
      {error && <p className="error">{error}</p>}

      <table>
        <thead><tr><th>Nombre</th><th>Subcategorías</th><th>Acciones</th></tr></thead>
        <tbody>
          {productos.map(p => (
            <tr key={p.id}>
              <td>{p.nombre}</td>
              <td>{p.subcategorias.map(s => s.nombre).join(", ")}</td>
              <td>
                <button onClick={() => editar(p)}>Editar</button>
                <button onClick={() => eliminar(p.id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
