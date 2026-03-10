function TransportistasDisponibles({ transportistas, seleccionarTransportista }) {

  if (!transportistas || transportistas.length === 0) {
    return <p>No hay transportistas disponibles</p>
  }

  return (
  
  <div>
  <h3>Transportistas disponibles</h3>
  
    <div className="tabla-transportistas">

    <table>

        <thead>
          <tr>
            <th>Transportista</th>
            <th>Descripción</th>
            <th>Precio</th>
            <th>Días de reparto</th>
            <th>Elegir</th>
          </tr>
        </thead>

        <tbody>

          {transportistas.map((t) => (

            <tr key={t.id}>

              <td>{t.nombre}</td>

              <td>{t.descripcion}</td>

              <td>
			  {t.precio ? `$${t.precio}` : "Cotizar"}
			 </td>

              <td>
			  {t.dias && t.dias.length > 0
				? t.dias.join(", ")
				: "—"}
			 </td>

              <td>
                <button
                  onClick={() => seleccionarTransportista(t)}
                >
                  Seleccionar
                </button>
              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>
  </div>

  )
}

export default TransportistasDisponibles