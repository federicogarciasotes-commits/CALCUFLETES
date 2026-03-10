import { useState } from "react"
import axios from "axios"

function Login({ setUsuario }) {

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [mensaje, setMensaje] = useState("")

  const login = async () => {

    try {

      const params = new URLSearchParams()
      params.append("username", username)
      params.append("password", password)

      const res = await axios.post(
        "http://localhost:8000/login",
        params
      )

      const token = res.data.access_token

      localStorage.setItem("token", token)

      setUsuario({ username })

    } catch (error) {

      console.error(error)
      setMensaje("Error en login")

    }

  }

  return (

    <div style={{ padding: 40, maxWidth: 400 }}>
	
	<h1>CALCUFLETES</h1>

      <h2>Login</h2>

      <input
        placeholder="usuario"
        value={username}
        onChange={(e)=>setUsername(e.target.value)}
      />

      <br /><br />

      <input
        type="password"
        placeholder="password"
        value={password}
        onChange={(e)=>setPassword(e.target.value)}
      />

      <br /><br />

      <button onClick={login}>
        Login
      </button>

      <p>{mensaje}</p>

    </div>

  )

}

export default Login