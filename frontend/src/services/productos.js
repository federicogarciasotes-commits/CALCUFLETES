import api from "./api";

export async function obtenerTiposProducto() {
  const res = await api.get("/productos/");

  return res.data;
}