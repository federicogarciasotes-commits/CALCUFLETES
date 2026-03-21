import { useState, useEffect } from "react"
import axios from "axios"

const API = "http://127.0.0.1:8000"
const headers = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` })

export default function TransportistasAdmin() {
  const [transportistas, setTransportistas] = useState([])
  const [dias, setDias] = useState([])
  const [provincias, setProvincias] = useState([])
  const [localidadesBuscadas, setLocalidadesBuscadas] = useState([])
  const [provinciaFiltro, setProvinciaFiltro] = useState("")
  const [busquedaNombre, setBusquedaNombre] = useState("")
  // Para mostrar nombres de las localidades seleccionadas
  const [localidadesSeleccionadas, setLocalidadesSeleccionadas] = useState([]) // [{id, nombre}]
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")
  const [form, setForm] = useState({ nombre: "", descripcion: "", dias_ids: [] })

  const cargar = async () => {
    const r = await axios.get(`${API}/transportistas/listar`, { headers: headers() })
    setTransportistas(r.data)
  }

  useEffect(() => {
    cargar()
    axios.get(`${API}/provincias/`).then(r => setProvincias(r.data))
    axios.get(`${API}/transportistas/dias/`).then(r => setDias(r.data))
  }, [])

  // Buscar localidades cuando cambia provincia o nombre
  useEffect(() => {
    if (!provinciaFiltro && !busquedaNombre) {
      setLocalidadesBuscadas([])
      return
    }
    const params = new URLSearchParams()
    if (provinciaFiltro) params.append("provincia_id", provinciaFiltro)
    if (busquedaNombre) params.append("nombre", busquedaNombre)
    axios.get(`${API}/localidades/buscar?${params}`).then(r => setLocalidadesBuscadas(r.data))
  }, [provinciaFiltro, busquedaNombre])

  const toggleDia = (id) => setForm(f => ({
    ...f,
    dias_ids: f.dias_ids.includes(id) ? f.dias_ids.filter(x => x !== id) : [...f.dias_ids, id]
  }))

  const agregarLocalidad = (loc) => {
    if (!localidadesSeleccionadas.find(l => l.id === loc.id)) {
      setLocalidadesSeleccionadas(prev => [...prev, { id: loc.id, nombre: loc.nombre }])
    }
  }

  const quitarLocalidad = (id) => {
    setLocalidadesSeleccionadas(prev => prev.filter(l => l.id !== id))
  }

  const seleccionarTodaProvincia = () => {
    const nuevas = localidadesBuscadas.filter(
      l => !localidadesSeleccionadas.find(s => s.id === l.id)
    )
    setLocalidadesSeleccionadas(prev => [...prev, ...nuevas.map(l => ({ id: l.id, nombre: l.nombre }))])
  }

  const guardar = async () => {
    setError("")
    if (!form.nombre.trim()) return setError("El nombre es obligatorio")
    const body = {
      ...form,
      destinos_ids: localidadesSeleccionadas.map(l => l.id)
    }
    try {
      if (editandoId) {
        await axios.put(`${API}/transportistas/editar/${editandoId}`, body, { headers: headers() })
      } else {
        await axios.post(`${API}/transportistas/`, body, { headers: headers() })
      }
      resetForm()
      cargar()
    } catch (e) {
      setError(e.response?.data?.detail || "Error al guardar")
    }
  }

  const editar = async (t) => {
    setEditandoId(t.id)
    setForm({ nombre: t.nombre, descripcion: t.descripcion || "", dias_ids: t.dias_ids })
    // Cargar nombres de los destinos actuales
    if (t.destinos_ids.length > 0) {
      const r = await axios.get(`${API}/localidades/buscar`)
      // Traer los que coincidan — o podés usar el endpoint de nombres del transportista
      const detalle = await axios.get(`${API}/transportistas/${t.id}`)
      setLocalidadesSeleccionadas(
        detalle.data.destinos.map((nombre, i) => ({ id: t.destinos_ids[i], nombre }))
      )
    } else {
      setLocalidadesSeleccionadas([])
    }
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar este transportista?")) return
    try {
      await axios.delete(`${API}/transportistas/${id}`, { headers: headers() })
      cargar()
    } catch (e) {
      setError(e.response?.data?.detail || "Error al eliminar")
    }
  }

  const resetForm = () => {
    setEditandoId(null)
    setForm({ nombre: "", descripcion: "", dias_ids: [] })
    setLocalidadesSeleccionadas([])
    setProvinciaFiltro("")
    setBusquedaNombre("")
  }

  return (
    <div>
      <h3>{editandoId ? "Editar transportista" : "Nuevo transportista"}</h3>

      <input placeholder="Nombre" value={form.nombre}
        onChange={e => setForm({...form, nombre: e.target.value})} />
      <input placeholder="Descripción" value={form.descripcion}
        onChange={e => setForm({...form, descripcion: e.target.value})} />

      {/* Días */}
      <div>
        <strong>Días de reparto:</strong>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", margin: "6px 0" }}>
          {dias.map(d => (
            <label key={d.id} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <input type="checkbox" checked={form.dias_ids.includes(d.id)} onChange={() => toggleDia(d.id)} />
              {d.nombre}
            </label>
          ))}
        </div>
      </div>

      {/* Buscador de destinos */}
      <div>
        <strong>Destinos:</strong>
        <div style={{ display: "flex", gap: "8px", margin: "6px 0" }}>
          <select value={provinciaFiltro} onChange={e => setProvinciaFiltro(e.target.value)}>
            <option value="">-- Filtrar por provincia --</option>
            {provincias.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
          </select>
          <input placeholder="Buscar localidad..." value={busquedaNombre}
            onChange={e => setBusquedaNombre(e.target.value)} />
        </div>

        {/* Botón seleccionar toda la provincia */}
        {provinciaFiltro && localidadesBuscadas.length > 0 && (
          <button onClick={seleccionarTodaProvincia} style={{ marginBottom: "8px" }}>
            Seleccionar toda la provincia ({localidadesBuscadas.length} localidades)
          </button>
        )}

        {/* Lista de resultados para agregar */}
        {localidadesBuscadas.length > 0 && (
          <div style={{ maxHeight: "180px", overflowY: "auto", border: "1px solid #ddd", borderRadius: "6px", padding: "4px" }}>
            {localidadesBuscadas.map(l => (
              <div key={l.id} style={{ display: "flex", justifyContent: "space-between", padding: "3px 6px" }}>
                <span>{l.nombre}</span>
                <button onClick={() => agregarLocalidad(l)} style={{ fontSize: "12px" }}>
                  {localidadesSeleccionadas.find(s => s.id === l.id) ? "✓" : "+ Agregar"}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Chips de localidades seleccionadas */}
        {localidadesSeleccionadas.length > 0 && (
		  <div>
			<strong>Seleccionadas ({localidadesSeleccionadas.length}):</strong>
			<div style={{
			  display: "flex",
			  flexWrap: "wrap",
			  gap: "6px",
			  marginTop: "6px",
			  maxHeight: "120px",
			  overflowY: "auto",
			  border: "1px solid #ddd",
			  borderRadius: "8px",
			  padding: "8px"
			}}>
			  {localidadesSeleccionadas.map(l => (
				<span key={l.id} style={{ background: "#e0e0e0", borderRadius: "12px", padding: "3px 10px", fontSize: "13px", display: "flex", alignItems: "center", gap: "4px" }}>
				  {l.nombre}
				  <button onClick={() => quitarLocalidad(l.id)}
					style={{ background: "none", border: "none", cursor: "pointer", fontWeight: "bold", padding: 0 }}>×</button>
				</span>
			  ))}
			</div>
		  </div>
		)}
      </div>

      <button onClick={guardar}>{editandoId ? "Guardar cambios" : "Crear"}</button>
      <button onClick={resetForm}>Cancelar</button>
      {error && <p className="error">{error}</p>}

      <h3>Transportistas existentes</h3>
      <table>
        <thead><tr><th>Nombre</th><th>Descripción</th><th>Acciones</th></tr></thead>
        <tbody>
          {transportistas.map(t => (
            <tr key={t.id}>
              <td>{t.nombre}</td>
              <td>{t.descripcion}</td>
              <td>
                <button onClick={() => editar(t)}>Editar</button>
                <button onClick={() => eliminar(t.id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}