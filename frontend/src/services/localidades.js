import api from "./api";

export async function buscarLocalidades(nombre, provincia_id) {
  const res = await api.get("/localidades/buscar", {
    params: {
      nombre: nombre,
      provincia_id: provincia_id
    }
  });

  return res.data;
}