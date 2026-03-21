function ListaProductos({ productos, setProductos }) {

  function eliminarProducto(index) {

    const nuevaLista = productos.filter((_, i) => i !== index)

    setProductos(nuevaLista)

  }

  return (

    <div className="productos-lista">

      <h3>Productos cargados</h3>

      <table>

        <thead>

          <tr>
            <th>Producto</th>
            <th>Cantidad</th>
            <th>Peso total</th>
            <th>Volumen</th>
            <th></th>
          </tr>

        </thead>

        <tbody>

          {productos.map((p, i) => {

            const volumenTotal = p.volumen * p.cantidad

            return (

              <tr key={i}>

                <td>{<p>{p.nombre} - {p.subcategoria}</p>}</td>

                <td>{p.cantidad}</td>

                <td>{(p.peso * p.cantidad).toFixed(4)} kg</td>

                <td>{volumenTotal.toFixed(4)} m³</td>

                <td>
                  <button onClick={() => eliminarProducto(i)}>
                    Eliminar
                  </button>
                </td>

              </tr>

            )

          })}

        </tbody>

      </table>

    </div>

  )

}

export default ListaProductos