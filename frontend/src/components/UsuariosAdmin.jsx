import { useState, useEffect } from "react"
import axios from "axios"

export default function UsuariosAdmin() {
  const [usuarios, setUsuarios] = useState([])
  const [form, setForm] = useState({ username: "", password: "", role: "vendedor" })
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")

  const cargarUsuarios = async () => {
    const res = await axios.get("http://127.0.0.1:8000/usuarios/listar", {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    })
    setUsuarios(res.data)
  }

  useEffect(() => { cargarUsuarios() }, [])

  const guardar = async () => {
	  
	setError("")

	  // Validaciones
	  if (!form.username.trim()) {
		setError("El username es obligatorio")
		return
	  }
	  if (!editandoId && !form.password.trim()) {
		setError("La contraseña es obligatoria al crear un usuario")
		return
	  }
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem("token")}` }
      if (editandoId) {
        await axios.put(`http://127.0.0.1:8000/usuarios/${editandoId}`, form, { headers })
      } else {
        await axios.post("http://127.0.0.1:8000/usuarios/", form, { headers })
      }
      setForm({ username: "", password: "", role: "vendedor" })
      setEditandoId(null)
      cargarUsuarios()
    } catch (e) {
      setError(e.response?.data?.detail || "Error al guardar")
    }
  }

  const editar = (u) => {
    setEditandoId(u.id)
    setForm({ username: u.username, password: "", role: u.role })
  }

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar este usuario?")) return
    await axios.delete(`http://127.0.0.1:8000/usuarios/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    })
    cargarUsuarios()
  }

  return (
    <div>
      <h3>{editandoId ? "Editar usuario" : "Nuevo usuario"}</h3>
      <input placeholder="Username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
      <input placeholder="Password" type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
      <select value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
        <option value="vendedor">Vendedor</option>
        <option value="admin">Admin</option>
      </select>
      <button onClick={guardar}>{editandoId ? "Guardar cambios" : "Crear"}</button>
		<button onClick={() => {
		  setEditandoId(null)
		  setForm({ username: "", password: "", role: "vendedor" })
		  setError("")
		}}>
		  Cancelar
		</button>
	  
      {error && <p className="error">{error}</p>}

      <h3>Usuarios existentes</h3>
      <table>
        <thead><tr><th>ID</th><th>Username</th><th>Rol</th><th>Acciones</th></tr></thead>
        <tbody>
          {usuarios.map(u => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.username}</td>
              <td>{u.role}</td>
              <td>
                <button onClick={() => editar(u)}>Editar</button>
                <button onClick={() => eliminar(u.id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}