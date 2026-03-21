import { useState, useEffect } from "react"
import axios from "axios"

const headers = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` })

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

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/origenes/").then(r => setOrigenes(r.data))
    axios.get("http://127.0.0.1:8000/provincias/").then(r => setProvincias(r.data))
  }, [])

  const [busquedaLocalidad, setBusquedaLocalidad] = useState("")
	// Reemplazá cargarLocalidades por un useEffect reactivo:
	useEffect(() => {
	  if (!form.provincia_id && !busquedaLocalidad) {
		setLocalidades([])
		return
	  }
	  const params = new URLSearchParams()
	  if (form.provincia_id) params.append("provincia_id", form.provincia_id)
	  if (busquedaLocalidad) params.append("nombre", busquedaLocalidad)
	  axios.get(`http://127.0.0.1:8000/localidades/buscar?${params}`)
		.then(r => setLocalidades(r.data))
	}, [form.provincia_id, busquedaLocalidad])
	
  const [mostrarSugerencias, setMostrarSugerencias] = useState(false)
  
  const cargar = async () => {
	  const r = await axios.get("http://127.0.0.1:8000/origenes/")
	  setOrigenes(r.data)
	}

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
        await axios.put(`http://127.0.0.1:8000/origenes/${editandoId}`, body, { headers: headers() })
      } else {
        await axios.post("http://127.0.0.1:8000/origenes/", body, { headers: headers() })
      }
      resetForm()
      const r = await axios.get("http://127.0.0.1:8000/origenes/")
	  await cargar()
	  onOrigenCambiado()
      setOrigenes(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || "Error al guardar")
    }
  }

  const editar = async (id) => {
    const r = await axios.get(`http://127.0.0.1:8000/origenes/${id}`)
	resetForm()
	await cargar()
	onOrigenCambiado()
    const d = r.data
    setEditandoId(id)
    setForm({
      nombre: d.nombre, es_default: d.es_default,
      calle: d.direccion.calle, altura: String(d.direccion.altura),
      piso: d.direccion.piso || "", departamento: d.direccion.departamento || "",
      provincia_id: d.direccion.provincia_id, localidad_id: d.direccion.localidad_id
    })
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar este origen?")) return
    try {
      await axios.delete(`http://127.0.0.1:8000/origenes/${id}`, { headers: headers() })
	  await cargar()
	  onOrigenCambiado()
      setOrigenes(origenes.filter(o => o.id !== id))
    } catch (e) {
      setError(e.response?.data?.detail || "Error al eliminar")
    }
  }

  const resetForm = () => {
    setEditandoId(null)
    setForm({ nombre: "", es_default: false, calle: "", altura: "", piso: "", departamento: "", provincia_id: "", localidad_id: "" })
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
      <select value={form.provincia_id} onChange={e => setForm({...form, provincia_id: e.target.value, localidad_id: "", })}>
        <option value="">-- Provincia --</option>
        {provincias.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
      </select>		

		<div style={{ position: "relative" }}>
		  <input
			placeholder="Buscar localidad..."
			value={busquedaLocalidad}
			onChange={e => {
			  setBusquedaLocalidad(e.target.value)
			  setMostrarSugerencias(true)
			  setForm({...form, localidad_id: ""}) // limpiar selección al escribir de nuevo
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
      <button onClick={guardar}>{editandoId ? "Guardar cambios" : "Crear"}</button>
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