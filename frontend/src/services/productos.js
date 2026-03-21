import axios from "axios"

export async function obtenerTiposProducto() {

  const res = await axios.get(
    "http://127.0.0.1:8000/productos/"
  )

  return res.data
}