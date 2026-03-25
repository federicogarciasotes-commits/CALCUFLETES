import { useState, useEffect } from "react";
import './App.css'
import axios from "axios"

import { calcularRuta } from "./services/rutas"

import Login from "./components/Login"
import OrigenForm from "./components/OrigenForm"
import DestinoForm from "./components/DestinoForm"
import ResultadoRuta from "./components/ResultadoRuta"
import TransportistasDisponibles from "./components/TransportistasDisponibles"
import ProductosForm from "./components/ProductosForm"
import ListaProductos from "./components/ListaProductos"
import AdminPanel from "./components/AdminPanel"


function App() {
	
  const [tabActiva, setTabActiva] = useState("calcular")

  const [usuario, setUsuario] = useState(() => {
	  const guardado = localStorage.getItem("usuario")
	  return guardado ? JSON.parse(guardado) : null
	})

  const [provincias, setProvincias] = useState([])
  const [origenes, setOrigenes] = useState([])

  const [busquedaLocalidadOrigen, setBusquedaLocalidadOrigen] = useState("")
  const [busquedaLocalidadDestino, setBusquedaLocalidadDestino] = useState("")

  const [resultadosOrigen, setResultadosOrigen] = useState([])
  const [resultadosDestino, setResultadosDestino] = useState([])

  const [origenSeleccionado, setOrigenSeleccionado] = useState(null)
  
  const [transportistas, setTransportistas] = useState([])
  const [transportistaSeleccionado, setTransportistaSeleccionado] = useState(null)
  const [precioFlete, setPrecioFlete] = useState("")
  
  const [productos, setProductos] = useState([])
  const [keyProductosForm, setKeyProductosForm] = useState(0)
  const totales = calcularTotales()
  
  const [cargandoTransportistas, setCargandoTransportistas] = useState(false)
  
  const [precioFactura, setPrecioFactura] = useState("")

  const [origen, setOrigen] = useState({
    titulo: "",
    calle: "",
    altura: "",
    piso: "",
    departamento: "",
    provincia_id: "",
    localidad_id: ""
  })

  const [destino, setDestino] = useState({
    calle: "",
    altura: "",
    piso: "",
    departamento: "",
    localidad_id: "",
    provincia_id: ""
  })

  const [resultado, setResultado] = useState(null)
  const [mensaje, setMensaje] = useState("")

  const cancelarCalculo = () => {
	  setDestino({ calle: "", altura: "", piso: "", departamento: "", localidad_id: "", provincia_id: "" })
	  setProductos([])
	  setResultado(null)
	  setTransportistas([])
	  setTransportistaSeleccionado(null)
	  setPrecioFlete("")
	  setMensaje("")
	  setBusquedaLocalidadDestino("")
	  setPrecioFactura("")
	  setKeyProductosForm(k => k + 1)
	}

  // cargar provincias
  useEffect(() => {

    async function cargarProvincias() {
		try {
			const res = await axios.get("http://127.0.0.1:8000/provincias/")
			const ordenadas = res.data.sort((a, b) => a.nombre.localeCompare(b.nombre))
			setProvincias(ordenadas)
		} catch (error) {
			console.error(error)
		}
	}

    cargarProvincias()

  }, [])

  // origen default
  const cargarOrigenDefault = async () => {
	  try {
		const res = await axios.get("http://127.0.0.1:8000/origenes/default")
		const data = res.data
		setOrigen({
		  titulo: data.nombre,
		  calle: data.direccion.calle,
		  altura: data.direccion.altura,
		  piso: data.direccion.piso || "",
		  departamento: data.direccion.departamento || "",
		  provincia_id: data.direccion.provincia_id,
		  localidad_id: data.direccion.localidad_id
		})
		setBusquedaLocalidadOrigen(data.direccion.localidad)
		setOrigenSeleccionado(data)
	  } catch (error) {
		console.error(error)
	  }
	}

	// Y actualizá onOrigenCambiado para que llame a las dos:
	const cargarOrigenes = () => {
	  axios.get("http://127.0.0.1:8000/origenes/titulos")
		.then(res => setOrigenes(res.data))
	  cargarOrigenDefault()  // agregar esta línea
	}

	// El useEffect simplemente la llama:
	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect
	  cargarOrigenDefault()
	  cargarOrigenes()
	}, []) // eslint-disable-line react-hooks/exhaustive-deps


  async function cambiarOrigen(id){

    try{

      const res = await axios.get(
        `http://127.0.0.1:8000/origenes/${id}`
      )

      const data = res.data

      setOrigen({
        titulo: data.nombre,
        calle: data.direccion.calle,
        altura: data.direccion.altura,
        piso: data.direccion.piso || "",
        departamento: data.direccion.departamento || "",
        localidad_id: data.direccion.localidad_id,
        provincia_id: data.direccion.provincia_id
      })

      setBusquedaLocalidadOrigen(
        data.direccion.localidad
      )

      setOrigenSeleccionado(data)

    }catch(error){

      console.error(error)

    }

  }

  const mostrarLocalidadesProvinciaOrigen = async () => {

    if (!origen.provincia_id) return

    const res = await axios.get(
      `http://127.0.0.1:8000/localidades/${origen.provincia_id}`
    )

    setResultadosOrigen(res.data)

  }

  const calcular = async () => {
		setMensaje("")
		
		// Validaciones
		if (!origen.localidad_id) {
			setMensaje("Seleccioná una localidad de origen")
			return
		}
		if (!origen.calle || !origen.altura) {
			setMensaje("Ingresá la calle y número de origen")
			return
		}
		if (!destino.localidad_id) {
			setMensaje("Seleccioná una localidad de destino")
			return
		}
		if (!destino.calle || !destino.altura) {
			setMensaje("Ingresá la calle y número de destino")
			return
		}
		if (productos.length === 0) {
			setMensaje("Agregá al menos un producto")
			return
		}
		if (totales.pesoTotal === 0) {
			setMensaje("El peso total no puede ser 0")
			return
		}
		
		try {
			const data = await calcularRuta(origen, destino)
			setResultado(data)

			if (destino.localidad_id) {
				// 1. Traer transportistas de la base
				const resT = await axios.get(
					`http://127.0.0.1:8000/transportistas/por-destino/${destino.localidad_id}`
				)
				
				setCargandoTransportistas(true)
				
				// 2. Cotizar precios reales
				const resCot = await axios.post(
					"http://127.0.0.1:8000/cotizaciones/",
					{
						localidad_origen_id: origen.localidad_id,
						localidad_destino_id: destino.localidad_id,
						cantidad_bultos: totales.bultos || 1,
						peso_total: totales.pesoTotal || 1
					}
				)

				// 3. Cruzar: agregarle el precio a cada transportista
				const cotizaciones = resCot.data  // array de {transportista, precio, ...}

				const transportistasConPrecio = resT.data.map(t => {
					const cot = cotizaciones.find(
						c => c.transportista.toLowerCase().replace(" ", "") === 
							 t.nombre.toLowerCase().replace(" ", "")
					)
					return {
						...t,
						precio: cot?.precio ?? null
					}
				})
				
				setCargandoTransportistas(false)
				const ordenados = transportistasConPrecio.sort((a, b) => {
					if (a.precio === null && b.precio === null) return 0
					if (a.precio === null) return 1
					if (b.precio === null) return -1
					return a.precio - b.precio
				})
				setTransportistas(ordenados)
			}

		} catch (error) {
			console.error(error)
			setResultado(null)
			setMensaje("Error al calcular ruta")
		}
	}
  
	
  const seleccionarTransportista = (t) => {

	  setTransportistaSeleccionado(t)

	  if (t.precio) {
		setPrecioFlete(t.precio)
	  }

	}
	
	
	function calcularTotales() {

	  let pesoTotal = 0
	  let volumenTotal = 0

	  productos.forEach(p => {

		const volumenUnitario =
		  p.alto * p.ancho * p.largo

		pesoTotal += p.peso * p.cantidad

		volumenTotal += volumenUnitario * p.cantidad

	  })
	  
	  
	  pesoTotal = Number(pesoTotal.toFixed(4))
	  volumenTotal = Number(volumenTotal.toFixed(4))

	  const volumenBulto = 1

	  const bultos = Math.ceil(volumenTotal / volumenBulto)

	  return {
		pesoTotal,
		volumenTotal,
		bultos
	  }
	}
	
  const cerrarSesion = () => {
		localStorage.removeItem("token")
		localStorage.removeItem("usuario")
		setUsuario(null)
		cancelarCalculo()
		cargarOrigenDefault()
	}
	


  if(!usuario){
    return <Login setUsuario={setUsuario}/>
  }
  

	return (
	  <div className="main-container">
		<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
		  <h1>CALCUFLETES</h1>
		  <button onClick={cerrarSesion}>Cerrar sesión</button>
		</div>

		<div className="tabs">
		  <button onClick={() => setTabActiva("calcular")} className={tabActiva === "calcular" ? "tab-activa" : ""}>
			Calcular Ruta
		  </button>
		  {usuario.role === "admin" && (
			<button onClick={() => setTabActiva("admin")} className={tabActiva === "admin" ? "tab-activa" : ""}>
			  Administración
			</button>
		  )}
		</div>

		{tabActiva === "calcular" && (
		<>
			
			<h2>Calcular Ruta</h2>

			<div className="form-row">

			  <div className="form-box">

				<OrigenForm
				  origen={origen}
				  setOrigen={setOrigen}
				  provincias={provincias}
				  origenes={origenes}
				  origenSeleccionado={origenSeleccionado}
				  cambiarOrigen={cambiarOrigen}
				  busquedaLocalidadOrigen={busquedaLocalidadOrigen}
				  setBusquedaLocalidadOrigen={setBusquedaLocalidadOrigen}
				  resultadosOrigen={resultadosOrigen}
				  setResultadosOrigen={setResultadosOrigen}
				  mostrarLocalidadesProvinciaOrigen={mostrarLocalidadesProvinciaOrigen}
				/>

			  </div>


			  <div className="form-box">

				<DestinoForm
				  destino={destino}
				  setDestino={setDestino}
				  provincias={provincias}
				  busquedaLocalidadDestino={busquedaLocalidadDestino}
				  setBusquedaLocalidadDestino={setBusquedaLocalidadDestino}
				  resultadosDestino={resultadosDestino}
				  setResultadosDestino={setResultadosDestino}
				/>

			  </div>

			</div>
			

			<ProductosForm
				key={keyProductosForm}
				productos={productos}
				setProductos={setProductos}
			/>

			<ListaProductos
			  productos={productos}
			  setProductos={setProductos}
			/>

			<div className="totales-productos">

			  <p>Peso total: {totales.pesoTotal} kg</p>

			  <p>Volumen total: {totales.volumenTotal} m³</p>

			  <p>Bultos: {totales.bultos}</p>

			</div>

			<div className="button-container">

					  <button onClick={cancelarCalculo}>
					  Cancelar
					  </button>
					  <button onClick={calcular}>
						Mostrar transportistas
					  </button>

					</div>
					


			{resultado && (
				<div className="resultado-section">
					<ResultadoRuta resultado={resultado}/>
					
					{cargandoTransportistas ? (
						<p>Buscando precios...</p>
					) : (
						<TransportistasDisponibles
							transportistas={transportistas}
							seleccionarTransportista={seleccionarTransportista}
						/>
					)}
				</div>
			)}

			{mensaje && (
			  <p className="mensaje">{mensaje}</p>
			)}


			{transportistaSeleccionado && (
				<div className="precio-box">

					<h3>Precio del flete</h3>
					<input
						type="text"
						value={precioFlete ? Number(precioFlete).toLocaleString("es-AR") : ""}
						disabled
					/>

					<h3>Precio de la factura</h3>
					<input
						type="text"
						value={precioFactura ? Number(precioFactura).toLocaleString("es-AR") : ""}
						onChange={(e) => {
							// guardar solo el número limpio internamente
							const limpio = e.target.value.replace(/\./g, "").replace(",", ".")
							if (/^\d*\.?\d*$/.test(limpio)) {
								setPrecioFactura(limpio)
							}
						}}
						placeholder="Ingresá el precio de la factura"
					/>

					{precioFactura && Number(precioFactura) > 0 && (
						<div className="porcentaje-box">
							{(() => {
								const porcentaje = (precioFlete / Number(precioFactura)) * 100
								const superaLimite = porcentaje > 4
								return (
									<>
										<p>
											El flete representa el{" "}
											<strong>{porcentaje.toFixed(2)}%</strong>{" "}
											de la factura
										</p>
										{superaLimite ? (
											<p className="advertencia">
												⚠️ El flete supera el 4% de la factura
											</p>
										) : (
											<p className="positivo">
												✅ El flete está dentro del límite del 4%
											</p>
										)}
									</>
								)
							})()}
						</div>
					)}

				</div>
			)}
		
		<div className="button-container">
		  <button onClick={cancelarCalculo}>Nueva cotización</button>
		</div>
		
		</>
		)}

		{tabActiva === "admin" && usuario.role === "admin" && (
		  <AdminPanel usuario={usuario} onOrigenCambiado={cargarOrigenes} />
		)}
	  </div>
	
	)
}	

export default App