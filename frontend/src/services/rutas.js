import api from "./api";

export const calcularRuta = async (origen, destino) => {
  const response = await api.post("/rutas/calcular", {
    origen: origen,
    destino: destino
  });

  return response.data;
};