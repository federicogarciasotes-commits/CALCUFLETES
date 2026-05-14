import { useState, useEffect } from "react"
import api from "../services/api"

// Normaliza texto: minúsculas, sin acentos, sin puntos
function normalizar(texto) {
  return texto
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\./g, "")
}

function DestinoForm({
  destino,
  setDestino,
  provincias,
  busquedaLocalidadDestino,
  setBusquedaLocalidadDestino,
  resultadosDestino,
  setResultadosDestino
}) {

  const [todasLocalidades, setTodasLocalidades] = useState([])

  const cargarLocalidades = async (provincia_id) => {
    if (!provincia_id) return
    const res = await api.get("/localidades/buscar", {
		params: { provincia_id }
	})
    const ordenadas = res.data.sort((a, b) => a.nombre.localeCompare(b.nombre))
    setTodasLocalidades(ordenadas)
  }

  useEffect(() => {
    if (destino.provincia_id) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      cargarLocalidades(destino.provincia_id)
    }
  }, [destino.provincia_id])

  const filtrarLocalidades = (texto) => {
    const textNorm = normalizar(texto)
    const filtradas = todasLocalidades.filter(loc =>
      normalizar(loc.nombre).includes(textNorm)
    )
    setResultadosDestino(filtradas)
  }

  return (
    <>
      <h3>Destino</h3>

      <input
        placeholder="Calle"
        value={destino.calle}
        onChange={(e) => setDestino({ ...destino, calle: e.target.value })}
      />

      <input
        placeholder="Número"
        value={destino.altura}
        onChange={(e) => setDestino({ ...destino, altura: e.target.value })}
      />

      <input
        value={destino.piso}
        placeholder="Piso (opcional)"
        onChange={(e) => setDestino({ ...destino, piso: e.target.value })}
      />

      <input
        value={destino.departamento}
        placeholder="Departamento (opcional)"
        onChange={(e) => setDestino({ ...destino, departamento: e.target.value })}
      />

      <select
        value={destino.provincia_id}
        onChange={(e) => {
          const provincia_id = e.target.value
          setDestino({ ...destino, provincia_id, localidad_id: "" })
          setBusquedaLocalidadDestino("")
          setResultadosDestino([])
          setTodasLocalidades([])
          if (provincia_id) cargarLocalidades(provincia_id)
        }}
      >
        <option value="">Provincia</option>
        {provincias.map((p) => (
          <option key={p.id} value={p.id}>{p.nombre}</option>
        ))}
      </select>

      {/* SELECTOR DE LOCALIDAD */}
      <div className="autocomplete">

        <input
          type="text"
          placeholder="Buscar localidad..."
          value={busquedaLocalidadDestino}
          disabled={!destino.provincia_id}

          onFocus={() => {
            if (todasLocalidades.length > 0) {
              setResultadosDestino(todasLocalidades)
            }
          }}

          onBlur={() => setTimeout(() => setResultadosDestino([]), 200)}

          onChange={(e) => {
            const texto = e.target.value
            setBusquedaLocalidadDestino(texto)
            if (texto.length === 0) {
              setResultadosDestino(todasLocalidades)
            } else {
              filtrarLocalidades(texto)
            }
          }}
        />

        {resultadosDestino.length > 0 && (
          <div className="autocomplete-dropdown">
            {resultadosDestino.map((loc) => (
              <div
                key={loc.id}
                className="autocomplete-item"
                onClick={() => {
                  setDestino({ ...destino, localidad_id: loc.id })
                  setBusquedaLocalidadDestino(loc.nombre)
                  setResultadosDestino([])
                }}
              >
                {loc.nombre}
              </div>
            ))}
          </div>
        )}

      </div>
    </>
  )
}

export default DestinoForm
