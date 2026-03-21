import { useState, useEffect } from "react"
import axios from "axios"

// Normaliza texto: minúsculas, sin acentos, sin puntos
function normalizar(texto) {
  return texto
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\./g, "")
}

function OrigenForm({
  origen,
  setOrigen,
  provincias,
  origenes,
  origenSeleccionado,
  cambiarOrigen,
  busquedaLocalidadOrigen,
  setBusquedaLocalidadOrigen,
  resultadosOrigen,
  setResultadosOrigen,
}) {

  const [todasLocalidades, setTodasLocalidades] = useState([])

  const cargarLocalidades = async (provincia_id) => {
    if (!provincia_id) return
    const res = await axios.get(`http://127.0.0.1:8000/localidades/buscar`, {
		params: { provincia_id }
	})
    const ordenadas = res.data.sort((a, b) => a.nombre.localeCompare(b.nombre))
    setTodasLocalidades(ordenadas)
  }

  useEffect(() => {
    if (origen.provincia_id) {
      cargarLocalidades(origen.provincia_id)
    }
  }, [origen.provincia_id])

  const filtrarLocalidades = (texto) => {
    const textNorm = normalizar(texto)
    const filtradas = todasLocalidades.filter(loc =>
      normalizar(loc.nombre).includes(textNorm)
    )
    setResultadosOrigen(filtradas)
  }

  return (
    <>
      <h3>Origen (default)</h3>

      <select
        value={origenSeleccionado?.id || ""}
        onChange={(e) => cambiarOrigen(e.target.value)}
      >
        {origenes.map(o => (
          <option key={o.id} value={o.id}>{o.nombre}</option>
        ))}
      </select>

      <input
        value={origen.calle}
        placeholder="Calle"
        onChange={(e) => setOrigen({ ...origen, calle: e.target.value })}
      />

      <input
        value={origen.altura}
        placeholder="Número"
        onChange={(e) => setOrigen({ ...origen, altura: e.target.value })}
      />

      <input
        value={origen.piso}
        placeholder="Piso (opcional)"
        onChange={(e) => setOrigen({ ...origen, piso: e.target.value })}
      />

      <input
        value={origen.departamento}
        placeholder="Departamento (opcional)"
        onChange={(e) => setOrigen({ ...origen, departamento: e.target.value })}
      />

      <select
        value={origen.provincia_id}
        onChange={(e) => {
          const provincia_id = e.target.value
          setOrigen({ ...origen, provincia_id, localidad_id: "" })
          setBusquedaLocalidadOrigen("")
          setResultadosOrigen([])
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
          value={busquedaLocalidadOrigen}
          disabled={!origen.provincia_id}

          onFocus={() => {
            if (todasLocalidades.length > 0) {
              setResultadosOrigen(todasLocalidades)
            } else if (origen.provincia_id) {
              cargarLocalidades(origen.provincia_id)
            }
          }}

          onBlur={() => setTimeout(() => setResultadosOrigen([]), 200)}

          onChange={(e) => {
            const texto = e.target.value
            setBusquedaLocalidadOrigen(texto)
            if (texto.length === 0) {
              setResultadosOrigen(todasLocalidades)
            } else {
              filtrarLocalidades(texto)
            }
          }}
        />

        {resultadosOrigen.length > 0 && (
          <div className="autocomplete-dropdown">
            {resultadosOrigen.map((loc) => (
              <div
                key={loc.id}
                className="autocomplete-item"
                onClick={() => {
                  setOrigen({ ...origen, localidad_id: loc.id })
                  setBusquedaLocalidadOrigen(loc.nombre)
                  setResultadosOrigen([])
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

export default OrigenForm