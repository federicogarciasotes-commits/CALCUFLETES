import { useEffect, useState } from "react"
import { obtenerTiposProducto } from "../services/productos"

function ProductosForm({ productos, setProductos }) {

  const [tiposProducto, setTiposProducto] = useState([])
  const [productoSeleccionado, setProductoSeleccionado] = useState(null)
  const [subcategoriaSeleccionada, setSubcategoriaSeleccionada] = useState(null)
  const [cantidad, setCantidad] = useState(1)

  useEffect(() => {

    async function cargar() {
      const data = await obtenerTiposProducto()
      setTiposProducto(data)
    }

    cargar()

  }, [])

  function agregarProducto() {

	  if (!productoSeleccionado || !subcategoriaSeleccionada) return

	  if (cantidad <= 0) {
		alert("La cantidad debe ser mayor a 0")
		return
	  }

	  const existenteIndex = productos.findIndex(
		p =>
		  p.nombre === productoSeleccionado.nombre &&
		  p.subcategoria === subcategoriaSeleccionada.nombre
	  )

	  if (existenteIndex !== -1) {

		const nuevosProductos = [...productos]

		nuevosProductos[existenteIndex].cantidad += cantidad

		setProductos(nuevosProductos)

	  } else {

		const nuevo = {
		  nombre: productoSeleccionado.nombre,
		  subcategoria: subcategoriaSeleccionada.nombre,
		  peso: subcategoriaSeleccionada.peso,
		  alto: subcategoriaSeleccionada.alto,
		  ancho: subcategoriaSeleccionada.ancho,
		  largo: subcategoriaSeleccionada.largo,
		  cantidad,
		  volumen:
			subcategoriaSeleccionada.largo *
			subcategoriaSeleccionada.ancho *
			subcategoriaSeleccionada.alto
		}

		setProductos([...productos, nuevo])

	  }

	  setCantidad(1)

	}

  return (

    <div className="form-box">

      <h3>Productos</h3>

      <div className="producto-row">

        <div className="producto-select">

          <label>Tipo de producto</label>

          <select
            onChange={(e) => {

              const prod = tiposProducto.find(
                p => p.id === Number(e.target.value)
              )

              setProductoSeleccionado(prod)

              if (prod && prod.subcategorias.length === 1) {
                setSubcategoriaSeleccionada(prod.subcategorias[0])
              } else {
                setSubcategoriaSeleccionada(null)
              }

            }}
          >

            <option value="">Seleccionar producto</option>

            {tiposProducto.map(p => (

              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>

            ))}

          </select>

        </div>


        <div className="producto-cantidad">

          <label>Cantidad</label>

          <input
            type="number"
            min="1"
            value={cantidad}
            onChange={(e) => setCantidad(Number(e.target.value))}
          />

        </div>

      </div>


      {/* Producto con una sola subcategoría */}

      {productoSeleccionado && productoSeleccionado.subcategorias.length === 1 && (

        <p>
          Presentación: {productoSeleccionado.subcategorias[0].nombre}
        </p>

      )}


      {/* Selector de subcategoría si hay varias */}

      {productoSeleccionado && productoSeleccionado.subcategorias.length > 1 && (

        <div className="producto-subcategoria">

          <label>Presentación</label>

          <select
            onChange={(e) => {

              const sub = productoSeleccionado.subcategorias.find(
                s => s.id === Number(e.target.value)
              )

              setSubcategoriaSeleccionada(sub)

            }}
          >

            <option value="">Seleccionar presentación</option>

            {productoSeleccionado.subcategorias.map(s => (

              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>

            ))}

          </select>

        </div>

      )}


      {/* Información de la subcategoría */}

      {subcategoriaSeleccionada && (

        <div className="producto-info">

          <p>Peso: {subcategoriaSeleccionada.peso} kg</p>

          <p>
            Medidas: {subcategoriaSeleccionada.alto} × {subcategoriaSeleccionada.ancho} × {subcategoriaSeleccionada.largo} m
          </p>

          <p>
            Volumen: {
              (
                subcategoriaSeleccionada.alto *
                subcategoriaSeleccionada.ancho *
                subcategoriaSeleccionada.largo
              ).toFixed(4)
            } m³
          </p>

        </div>

      )}


      <button
        disabled={!productoSeleccionado || !subcategoriaSeleccionada || cantidad <= 0}
        onClick={agregarProducto}
      >
        Agregar producto
      </button>

    </div>

  )

}

export default ProductosForm