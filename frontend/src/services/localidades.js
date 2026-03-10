import axios from "axios";

export async function buscarLocalidades(nombre) {

  const res = await axios.get(
    `http://localhost:8000/localidades/buscar?nombre=${nombre}`
  );

  return res.data;
}