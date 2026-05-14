import { useState, useEffect } from "react"
import api from "../services/api"

export default function OrigenesAdmin({ onOrigenCambiado }) {

  const [origenes, setOrigenes] = useState([])
  const [provincias, setProvincias] = useState([])
  const [localidades, setLocalidades] = useState([])
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")
  const [form, setForm] = useState({
    nombre: "", es_default: false,
    calle: "", altura: "", piso: "", departamento: "",
    provincia_id: "", localidad_id: ""
  })
  const [originalForm, setOriginalForm] = useState(null)
  const [busquedaLocalidad, setBusquedaLocalidad] = useState("")
  const [mostrarSugerencias, setMostrarSugerencias] = useState(false)

  const cargar = async () => {
    const r = await api.get("/origenes/")
    setOrigenes(r.data)
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    cargar()
    api.get("/provincias/").then(r => setProvincias(r.data))
  }, [])

  // Auto-dismiss del error
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000)
      return () => clearTimeout(timer)
    }
  }, [error])

  // Buscar localidades solo cuando el usuario interactúa explícitamente
  const buscarLocalidades = (provinciaId, nombre) => {
    if (!provinciaId && !nombre) { setLocalidades([]); return }
    const params = new URLSearchParams()
    if (provinciaId) params.append("provincia_id", provinciaId)
    if (nombre) params.append("nombre", nombre)
    api.get(`/localidades/buscar?${params}`)
      .then(r => setLocalidades(r.data))
  }

  // Deshabilitar botón guardar
  const guardarDeshabilitado = (() => {
    if (!form.nombre.trim()) return true
    if (!form.calle.trim()) return true
    if (!form.altura.trim()) return true
    if (!form.localidad_id) return true

    if (editandoId && originalForm) {
      const sinCambios =
        form.nombre === originalForm.nombre &&
        form.es_default === originalForm.es_default &&
        form.calle === originalForm.calle &&
        form.altura === originalForm.altura &&
        form.piso === originalForm.piso &&
        form.departamento === originalForm.departamento &&
        form.provincia_id === originalForm.provincia_id &&
        String(form.localidad_id) === String(originalForm.localidad_id)
      if (sinCambios) return true
    }

    return false
  })()

  const guardar = async () => {
    setError("")
    if (!form.nombre.trim()) return setError("El nombre es obligatorio")
    if (!form.calle.trim() || !form.altura.trim()) return setError("Calle y altura son obligatorios")
    if (!form.localidad_id) return setError("Seleccioná una localidad")

    const body = {
      nombre: form.nombre,
      es_default: form.es_default,
      direccion: {
        calle: form.calle, altura: form.altura,
        piso: form.piso, departamento: form.departamento,
        localidad_id: Number(form.localidad_id)
      }
    }
    try {
      if (editandoId) {
        await api.put(`/origenes/${editandoId}`, body)
      } else {
        await api.post("/origenes/", body)
      }
      resetForm()
      await cargar()
      onOrigenCambiado()
    } catch (e) {
      setError(e.response?.data?.detail || "Error al guardar")
    }
  }

  const editar = async (id) => {
    const r = await api.get(`/origenes/${id}`)
    const d = r.data

    // Traer localidades de la provincia para mostrar el nombre y poblar el dropdown
    let nombreLocalidad = ""
    let localidadesDeProvincia = []
    try {
      const rl = await api.get(
        `/localidades/buscar?provincia_id=${d.direccion.provincia_id}`
      )
      localidadesDeProvincia = rl.data
      const encontrada = rl.data.find(l => l.id === d.direccion.localidad_id)
      if (encontrada) nombreLocalidad = encontrada.nombre
    // eslint-disable-next-line no-unused-vars, no-empty
    } catch (_) {}

    const datos = {
      nombre: d.nombre, es_default: d.es_default,
      calle: d.direccion.calle, altura: String(d.direccion.altura),
      piso: d.direccion.piso || "", departamento: d.direccion.departamento || "",
      provincia_id: d.direccion.provincia_id, localidad_id: d.direccion.localidad_id
    }

    resetForm()
    setLocalidades(localidadesDeProvincia)
    setEditandoId(id)
    setForm(datos)
    setOriginalForm(datos)
    setBusquedaLocalidad(nombreLocalidad)
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar este origen?")) return
    try {
      await api.delete(`/origenes/${id}`)
      await cargar()
      onOrigenCambiado()
    } catch (e) {
      setError(e.response?.data?.detail || "Error al eliminar")
    }
  }

  const resetForm = () => {
    setEditandoId(null)
    setOriginalForm(null)
    setForm({ nombre: "", es_default: false, calle: "", altura: "", piso: "", departamento: "", provincia_id: "", localidad_id: "" })
    setBusquedaLocalidad("")
    setLocalidades([])
    setMostrarSugerencias(false)
    setError("")
  }

  return (
    <div>
      <h3>{editandoId ? "Editar origen" : "Nuevo origen"}</h3>
      <input placeholder="Nombre" value={form.nombre} onChange={e => setForm({...form, nombre: e.target.value})} />
      <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", width: "fit-content" }}>
        <input type="checkbox" checked={form.es_default} onChange={e => setForm({...form, es_default: e.target.checked})} />
        <span>Default</span>
      </label>
      <input placeholder="Calle" value={form.calle} onChange={e => setForm({...form, calle: e.target.value})} />
      <input placeholder="Altura" value={form.altura} onChange={e => setForm({...form, altura: e.target.value})} />
      <input placeholder="Piso" value={form.piso} onChange={e => setForm({...form, piso: e.target.value})} />
      <input placeholder="Departamento" value={form.departamento} onChange={e => setForm({...form, departamento: e.target.value})} />

      <select
        value={form.provincia_id}
        onChange={e => {
          const nuevaProvincia = e.target.value
          setForm({...form, provincia_id: nuevaProvincia, localidad_id: ""})
          setBusquedaLocalidad("")
          buscarLocalidades(nuevaProvincia, "")
        }}
      >
        <option value="">-- Provincia --</option>
        {provincias.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
      </select>

      <div style={{ position: "relative" }}>
        <input
          placeholder="Buscar localidad..."
          value={busquedaLocalidad}
          onChange={e => {
            const val = e.target.value
            setBusquedaLocalidad(val)
            setMostrarSugerencias(true)
            setForm({...form, localidad_id: ""})
            buscarLocalidades(form.provincia_id, val)
          }}
          onFocus={() => setMostrarSugerencias(true)}
        />
        {mostrarSugerencias && localidades.length > 0 && (
          <div style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            maxHeight: "200px",
            overflowY: "auto",
            border: "1px solid #ccc",
            borderRadius: "6px",
            background: "white",
            zIndex: 10
          }}>
            {localidades.map(l => (
              <div
                key={l.id}
                onClick={() => {
                  setForm({...form, localidad_id: l.id})
                  setBusquedaLocalidad(l.nombre)
                  setMostrarSugerencias(false)
                }}
                style={{ padding: "8px 12px", cursor: "pointer" }}
                onMouseEnter={e => e.currentTarget.style.background = "#f0f0f0"}
                onMouseLeave={e => e.currentTarget.style.background = "white"}
              >
                {l.nombre}
              </div>
            ))}
          </div>
        )}
      </div>

      <button onClick={guardar} disabled={guardarDeshabilitado}>
        {editandoId ? "Guardar cambios" : "Crear"}
      </button>
      <button onClick={resetForm}>Cancelar</button>
      {error && <p className="error">{error}</p>}

      <h3>Orígenes existentes</h3>
      <table>
        <thead><tr><th>Nombre</th><th>Default</th><th>Acciones</th></tr></thead>
        <tbody>
          {origenes.map(o => (
            <tr key={o.id}>
              <td>{o.nombre}</td>
              <td>{o.es_default ? "✓ Default" : "—"}</td>
              <td>
                <button onClick={() => editar(o.id)}>Editar</button>
                <button onClick={() => eliminar(o.id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
