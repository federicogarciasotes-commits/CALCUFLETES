import OrigenForm from "../components/OrigenForm"
import DestinoForm from "../components/DestinoForm"
import ResultadoRuta from "../components/ResultadoRuta"
import TransportistasDisponibles from "../components/TransportistasDisponibles"

function Rutas() {
  return (
    <div className="cf-route-section">

      <div className="cf-route-forms">

        <div className="cf-form-card">
          <OrigenForm />
        </div>

        <div className="cf-form-card">
          <DestinoForm />
        </div>

      </div>

      <div className="cf-results-section">

        <div className="cf-result-card">
          <ResultadoRuta />
        </div>

        <div className="cf-result-card">
          <TransportistasDisponibles />
        </div>

      </div>

    </div>
  )
}

export default Rutas