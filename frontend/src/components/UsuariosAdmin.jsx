import { useState, useEffect } from "react"
import axios from "axios"

export default function UsuariosAdmin() {
  const [usuarios, setUsuarios] = useState([])
  const [form, setForm] = useState({ username: "", password: "", role: "vendedor" })
  const [originalForm, setOriginalForm] = useState(null)
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")
  const [passwordVisible, setPasswordVisible] = useState(false)

  const cargarUsuarios = async () => {
    const res = await axios.get("http://127.0.0.1:8000/usuarios/listar", {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    })
    setUsuarios(res.data)
  }

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargarUsuarios() }, [])

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError("")
      }, 3000)

      return () => clearTimeout(timer)
    }
  }, [error])

  // Determina si el botón guardar debe estar deshabilitado
  const guardarDeshabilitado = (() => {
    // Campos vacíos siempre bloquean
    if (!form.username.trim()) return true

    if (editandoId) {
      // En edición: bloquear si no hubo ningún cambio respecto al original
      const sinCambios =
        originalForm &&
        form.username === originalForm.username &&
        form.password === originalForm.password &&
        form.role === originalForm.role
      if (sinCambios) return true

      // Si cambió la contraseña, no puede quedar vacía
      if (form.password !== originalForm?.password && !form.password.trim()) return true
    } else {
      // En creación: contraseña obligatoria
      if (!form.password.trim()) return true
    }

    return false
  })()

  const guardar = async () => {
    setError("")

    // Validaciones (respaldo por si acaso)
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
      const payload = { ...form }
      if (editandoId && payload.password === "********") {
        delete payload.password
      }

      if (editandoId) {
        await axios.put(`http://127.0.0.1:8000/usuarios/${editandoId}`, payload, { headers })
      } else {
        await axios.post("http://127.0.0.1:8000/usuarios/", payload, { headers })
      }
      setForm({ username: "", password: "", role: "vendedor" })
      setOriginalForm(null)
      setPasswordVisible(false)
      setEditandoId(null)
      cargarUsuarios()
    } catch (e) {
      setError(e.response?.data?.detail || "Error al guardar")
    }
  }

  const editar = (u) => {
    setEditandoId(u.id)
    setPasswordVisible(false)
    const datos = { username: u.username, password: "********", role: u.role }
    setForm(datos)
    setOriginalForm(datos)
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <input
          placeholder="Password"
          type={passwordVisible ? "text" : "password"}
          value={form.password}
          onChange={e => {
            let value = e.target.value

            // Si estaba el placeholder y empieza a escribir, lo reemplaza
            if (form.password === "********") {
              value = e.target.value.replace(/\*/g, "")
            }

            setForm({ ...form, password: value })
          }}
        />
        <button type="button" onClick={() => setPasswordVisible(!passwordVisible)}>
          {passwordVisible ? "Ocultar" : "Mostrar"}
        </button>
      </div>
      <select value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
        <option value="vendedor">Vendedor</option>
        <option value="admin">Admin</option>
      </select>
      <button onClick={guardar} disabled={guardarDeshabilitado}>
        {editandoId ? "Guardar cambios" : "Crear"}
      </button>
      <button onClick={() => {
        setEditandoId(null)
        setOriginalForm(null)
        setForm({ username: "", password: "", role: "vendedor" })
        setPasswordVisible(false)
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