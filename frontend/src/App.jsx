import { useState, useEffect } from "react";
import './App.css'
import axios from "axios"

import { calcularRuta } from "./services/rutas"

import Login from "./components/Login"
import OrigenForm from "./components/OrigenForm"
import DestinoForm from "./components/DestinoForm"
import ResultadoRuta from "./components/ResultadoRuta"
import TransportistasDisponibles from "./components/TransportistasDisponibles"

function App() {

  const [usuario, setUsuario] = useState(null)

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

  // cargar provincias
  useEffect(() => {

    async function cargarProvincias() {

      try {

        const res = await axios.get(
          "http://localhost:8000/provincias"
        )

        setProvincias(res.data)

      } catch (error) {
        console.error(error)
      }

    }

    cargarProvincias()

  }, [])

  // origen default
  useEffect(() => {

    async function cargarOrigenDefault() {

      try {

        const res = await axios.get(
          "http://localhost:8000/origenes/default"
        )

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

        setBusquedaLocalidadOrigen(
          data.direccion.localidad
        )

      } catch (error) {

        console.error(error)

      }

    }

    cargarOrigenDefault()

  }, [])

  // cargar titulos de origen
  useEffect(() => {

    axios
      .get("http://localhost:8000/origenes/titulos")
      .then(res => setOrigenes(res.data))

  }, [])

  async function cambiarOrigen(id){

    try{

      const res = await axios.get(
        `http://localhost:8000/origenes/${id}`
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
      `http://localhost:8000/localidades/${origen.provincia_id}`
    )

    setResultadosOrigen(res.data)

  }

  const calcular = async () => {

    try {

      const data = await calcularRuta(origen, destino)

      setResultado(data)
	  
	  
	  if(destino.localidad_id){
      obtenerTransportistas(destino.localidad_id)
	  }
    } catch (error) {

      console.error(error)
      setMensaje("Error al calcular ruta")

    }

  }
  
  const obtenerTransportistas = async (localidad_id) => {

	  try {

		const res = await axios.get(
		  `http://localhost:8000/transportistas/por-destino/${localidad_id}`
		)
		
		setTransportistas(res.data)
		
	  } catch (error) {

		console.error("Error cargando transportistas", error)

	  }

	}
	
  const seleccionarTransportista = (t) => {

	  setTransportistaSeleccionado(t)

	  if (t.precio) {
		setPrecioFlete(t.precio)
	  }

	}


  if(!usuario){
    return <Login setUsuario={setUsuario}/>
  }

  return (

    <div className="main-container">

      <h1>CALCUFLETES</h1>
      <h2>Calcular Ruta</h2>

      <div className="form-row">

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

      <div className="button-container">

        <button onClick={calcular}>
          Calcular Ruta
        </button>

      </div>

	{resultado && (
	  <>
		<ResultadoRuta resultado={resultado}/>

		<TransportistasDisponibles
		  transportistas={transportistas}
		  seleccionarTransportista={seleccionarTransportista}
		/>

	  </>
	)}

  <p>{mensaje}</p>

	  {transportistaSeleccionado && (

	  <div style={{marginTop: "20px"}}>

		<h3>Precio del flete</h3>

		<input
		  type="text"
		  value={precioFlete} disabled
		/>

	  </div>

	)}

  </div>
  )
}

export default App