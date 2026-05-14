import { useState } from "react"
import api from "../services/api"
import '../App.css'

function Login({ setUsuario }) {

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [mensaje, setMensaje] = useState("")


  const login = async () => {

    try {

      const params = new URLSearchParams()
      params.append("username", username)
      params.append("password", password)

      const res = await api.post("/login", params)

      const token = res.data.access_token

      localStorage.setItem("token", token)
	  
	  const me = await api.get("/me")
	  localStorage.setItem("usuario", JSON.stringify(me.data))
	  setUsuario(me.data)

    } catch (error) {

      console.error(error)
      setMensaje("Error en login")

    }

  }

   return (

	  <div className="login-container">

		<div className="login-card">

		  <h1>CALCUFLETES</h1>

		  <h2>Login</h2>

		  <input
			placeholder="Usuario"
			value={username}
			onChange={(e)=>setUsername(e.target.value)}
		  />

		  <input
			type="password"
			placeholder="Password"
			value={password}
			onChange={(e)=>setPassword(e.target.value)}
		  />

		  <button onClick={login}>
			Login
		  </button>

		  <p className="login-mensaje">{mensaje}</p>

		</div>

	  </div>

	)

}

export default Login
