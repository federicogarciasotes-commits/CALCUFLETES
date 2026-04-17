import { useState } from "react"
import UsuariosAdmin from "./UsuariosAdmin"
import TransportistasAdmin from "./TransportistasAdmin"
import OrigenesAdmin from "./OrigenesAdmin"
import ProductosAdmin from "./ProductosAdmin"

export default function AdminPanel({ onOrigenCambiado }) {
  const [seccion, setSeccion] = useState("usuarios")

  return (
    <div className="admin-panel">
      <h2>Panel de Administración</h2>
      <div className="admin-tabs">
        <button onClick={() => setSeccion("usuarios")} className={seccion === "usuarios" ? "tab-activa" : ""}>Usuarios</button>
        <button onClick={() => setSeccion("transportistas")} className={seccion === "transportistas" ? "tab-activa" : ""}>Transportistas</button>
        <button onClick={() => setSeccion("origenes")} className={seccion === "origenes" ? "tab-activa" : ""}>Orígenes</button>
        <button onClick={() => setSeccion("productos")} className={seccion === "productos" ? "tab-activa" : ""}>Productos</button>
      </div>
      {seccion === "usuarios" && <UsuariosAdmin />}
      {seccion === "transportistas" && <TransportistasAdmin />}
      {seccion === "origenes" && <OrigenesAdmin onOrigenCambiado={onOrigenCambiado} />}
      {seccion === "productos" && <ProductosAdmin />}
    </div>
  )
}
