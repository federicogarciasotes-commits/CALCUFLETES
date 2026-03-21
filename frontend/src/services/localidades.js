import axios from "axios";

export async function buscarLocalidades(nombre, provincia_id) {

  const res = await axios.get(
    `http://127.0.0.1:8000/localidades/buscar`,
    {
      params: {
        nombre: nombre,
        provincia_id: provincia_id
      }
    }
  );

  return res.data;
}