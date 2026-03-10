import axios from "axios"
import { buscarLocalidades } from "../services/localidades"

function DestinoForm({
  destino,
  setDestino,
  provincias,
  busquedaLocalidadDestino,
  setBusquedaLocalidadDestino,
  resultadosDestino,
  setResultadosDestino
}) {

return (

<div className="form-box">

<h3>Destino</h3>

<input
placeholder="Calle"
value={destino.calle}
onChange={(e)=>
setDestino({...destino, calle:e.target.value})
}
/>

<input
placeholder="Número"
value={destino.altura}
onChange={(e)=>
setDestino({...destino, altura:e.target.value})
}
/>

<select
value={destino.provincia_id}
onChange={(e)=>{

const provincia_id = e.target.value

setDestino({
...destino,
provincia_id,
localidad_id:""
})

}}
>

<option value="">Provincia</option>

{provincias.map((p)=>(
<option key={p.id} value={p.id}>
{p.nombre}
</option>
))}

</select>

<div className="autocomplete">

<input
type="text"
placeholder="Buscar localidad..."
value={busquedaLocalidadDestino}
onBlur={() => setTimeout(() => setResultadosDestino([]), 200)}

onFocus={async () => {

if (!destino.provincia_id) return

const res = await axios.get(
`http://localhost:8000/localidades/${destino.provincia_id}`
)

setResultadosDestino(res.data)

}}

onChange={async (e)=>{

const texto = e.target.value
setBusquedaLocalidadDestino(texto)

if (texto.length < 2) return

const data = await buscarLocalidades(texto)

setResultadosDestino(data)

}}
/>

{resultadosDestino.length > 0 && (

<div className="autocomplete-list">

{resultadosDestino.map((loc) => (

<div
key={loc.id}
className="autocomplete-item"
onClick={() => {

setDestino({
...destino,
localidad_id: loc.id
})

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

</div>

)

}

export default DestinoForm