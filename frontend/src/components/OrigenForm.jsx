import axios from "axios"
import { buscarLocalidades } from "../services/localidades"

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
  mostrarLocalidadesProvinciaOrigen
}) {

  return (

<div className="form-box">

<h3>Origen (default)</h3>

<select
  value={origenSeleccionado?.id || ""}
  onChange={(e) => cambiarOrigen(e.target.value)}
>

{origenes.map(o => (
<option key={o.id} value={o.id}>
{o.nombre}
</option>
))}

</select>

<input
value={origen.calle}
placeholder="Calle"
onChange={(e)=>
setOrigen({...origen, calle:e.target.value})
}
/>

<input
value={origen.altura}
placeholder="Número"
onChange={(e)=>
setOrigen({...origen, altura:e.target.value})
}
/>

<select
value={origen.provincia_id}
onChange={async (e)=>{

const provincia_id = e.target.value

setOrigen({
...origen,
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
value={busquedaLocalidadOrigen}
onBlur={() => setTimeout(() => setResultadosOrigen([]), 200)}

onFocus={mostrarLocalidadesProvinciaOrigen}

onChange={async (e)=>{

const texto = e.target.value
setBusquedaLocalidadOrigen(texto)

if (texto.length < 2) {
mostrarLocalidadesProvinciaOrigen()
return
}

const data = await buscarLocalidades(texto)

setResultadosOrigen(data)

}}
/>

{resultadosOrigen.length > 0 && (

<div className="autocomplete-list">

{resultadosOrigen.map((loc) => (

<div
key={loc.id}
className="autocomplete-item"
onClick={() => {

setOrigen({
...origen,
localidad_id: loc.id
})

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

</div>

  )
}

export default OrigenForm