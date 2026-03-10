function ResultadoRuta({resultado}){

return(

<div className="resultado-section">

<h2 className="resultado-titulo">Resultado</h2>

<div className="result-container">

<div className="map-container">
<img src={resultado.mapa} alt="Mapa de ruta"/>
</div>

<div className="info-container">
<p><b>Distancia:</b> {resultado.distancia}</p>
<p><b>Tiempo estimado:</b> {resultado.duracion}</p>
</div>

</div>

</div>

)

}

export default ResultadoRuta