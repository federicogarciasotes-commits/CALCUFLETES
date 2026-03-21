function ResultadoRuta({resultado}){

return(

<div className="resultado-section">

<h2 className="resultado-titulo">Resultado</h2>

<div className="result-container">

<div className="map-container">
<img src={resultado.mapa} alt="Mapa de ruta"/>
</div>

<div className="resultado-info">

  <div className="info-item">
    <strong>Distancia: </strong>
    <span>{resultado.distancia}</span>
  </div>

  <div className="info-item">
    <strong>Tiempo estimado: </strong>
    <span>{resultado.duracion}</span>
  </div>

</div>

</div>

</div>

)

}

export default ResultadoRuta