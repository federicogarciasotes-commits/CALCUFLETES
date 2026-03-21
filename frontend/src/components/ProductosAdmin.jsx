import { useState, useEffect } from "react"
import axios from "axios"

const headers = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` })
const API = "http://127.0.0.1:8000"

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

  const cargar = () => axios.get(`${API}/subcategorias/`).then(r => setLista(r.data))
  useEffect(() => { cargar() }, [])

  const guardar = async () => {
    setError("")
    if (!form.nombre.trim()) return setError("El nombre es obligatorio")
    if ([form.largo, form.ancho, form.alto, form.peso].some(v => v === "" || isNaN(v)))
      return setError("Largo, ancho, alto y peso son obligatorios y deben ser números")
    const body = { nombre: form.nombre, largo: Number(form.largo), ancho: Number(form.ancho), alto: Number(form.alto), peso: Number(form.peso) }
    try {
      if (editandoId) {
        await axios.put(`${API}/subcategorias/${editandoId}`, body, { headers: headers() })
      } else {
        await axios.post(`${API}/subcategorias`, body, { headers: headers() })
      }
      setForm({ nombre: "", largo: "", ancho: "", alto: "", peso: "" })
      setEditandoId(null)
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
  }

  const editar = (s) => {
    setEditandoId(s.id)
    setForm({ nombre: s.nombre, largo: s.largo, ancho: s.ancho, alto: s.alto, peso: s.peso })
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar?")) return
    try {
      await axios.delete(`${API}/subcategorias/${id}`, { headers: headers() })
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
  }

  return (
    <div>
      <h3>{editandoId ? "Editar subcategoría" : "Nueva subcategoría"}</h3>
      <input placeholder="Nombre" value={form.nombre} onChange={e => setForm({...form, nombre: e.target.value})} />
      {["largo","ancho","alto","peso"].map(campo => (
        <input key={campo} placeholder={campo} type="number" value={form[campo]}
          onChange={e => setForm({...form, [campo]: e.target.value})} />
      ))}
      <button onClick={guardar}>{editandoId ? "Guardar" : "Crear"}</button>
      <button onClick={() => { setEditandoId(null); setForm({ nombre: "", largo: "", ancho: "", alto: "", peso: "" }) }}>Cancelar</button>
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
  const [busquedaSub, setBusquedaSub] = useState("")
  const subcategoriasFiltradas = subcategorias.filter(s =>
	  s.nombre.toLowerCase().includes(busquedaSub.toLowerCase())
	)


  const cargar = () => axios.get(`${API}/productos/`).then(r => setProductos(r.data))
  useEffect(() => {
    cargar()
    axios.get(`${API}/subcategorias/`).then(r => setSubcategorias(r.data))
  }, [])

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
        await axios.put(`${API}/productos/${editandoId}`, form, { headers: headers() })
      } else {
        await axios.post(`${API}/productos`, form, { headers: headers() })
      }
      setForm({ nombre: "", subcategorias_ids: [] })
      setEditandoId(null)
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
  }

  const editar = (p) => {
    setEditandoId(p.id)
    setForm({ nombre: p.nombre, subcategorias_ids: p.subcategorias.map(s => s.id) })
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar?")) return
    try {
      await axios.delete(`${API}/productos/${id}`, { headers: headers() })
      cargar()
    } catch (e) { setError(e.response?.data?.detail || "Error") }
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

		  {/* Lista de resultados */}
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

		  {/* Chips de seleccionadas */}
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
      <button onClick={guardar}>{editandoId ? "Guardar" : "Crear"}</button>
      <button onClick={() => { setEditandoId(null); setForm({ nombre: "", subcategorias_ids: [] }) }}>Cancelar</button>
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