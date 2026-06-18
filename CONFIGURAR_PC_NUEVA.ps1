$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Require-Command {
    param([string]$Name, [string]$Message)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw $Message
    }
}

Write-Host "=== Configurando Calcufletes ===" -ForegroundColor Cyan
Require-Command "py" "Falta Python. Instalalo desde https://python.org marcando Add Python to PATH."
Require-Command "npm" "Falta Node.js LTS. Instalalo desde https://nodejs.org."

if (-not (Get-Command "mkcert" -ErrorAction SilentlyContinue)) {
    Require-Command "winget" "Falta mkcert y no se encontro winget para instalarlo."
    Write-Host "Instalando mkcert..." -ForegroundColor Yellow
    winget install --id FiloSottile.mkcert --exact --accept-package-agreements --accept-source-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    Require-Command "mkcert" "mkcert se instalo, pero Windows todavia no lo encuentra. Reinicia la terminal y ejecuta nuevamente este archivo."
}

Write-Host "Preparando el backend..." -ForegroundColor Yellow
& py -3 -m venv venv
& "$PSScriptRoot\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$PSScriptRoot\venv\Scripts\python.exe" -m pip install -r requirements.txt

Write-Host "Preparando el frontend..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\frontend"
try {
    npm ci
} finally {
    Pop-Location
}

Write-Host "Generando el certificado HTTPS de esta computadora..." -ForegroundColor Yellow
mkcert -install
New-Item -ItemType Directory -Path "$PSScriptRoot\certs" -Force | Out-Null
$addresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.IPAddress -ne "127.0.0.1" -and
        $_.IPAddress -notlike "169.254.*" -and
        $_.AddressState -eq "Preferred"
    } |
    Select-Object -ExpandProperty IPAddress -Unique
$names = @("localhost", "127.0.0.1", "::1", $env:COMPUTERNAME) + $addresses
mkcert -key-file "$PSScriptRoot\certs\dev-key.pem" -cert-file "$PSScriptRoot\certs\dev-cert.pem" $names

if (-not (Test-Path "$PSScriptRoot\.env")) {
    Copy-Item "$PSScriptRoot\.env.example" "$PSScriptRoot\.env"
    Write-Warning "Se creo .env sin secretos. Completa GOOGLE_API_KEY y las credenciales necesarias."
}

Write-Host ""
Write-Host "Configuracion terminada." -ForegroundColor Green
Write-Host "La tarea existente puede seguir ejecutando arrancar_server\start_silent.vbs."
Write-Host "Tambien podes iniciar el sistema manualmente con INICIAR.bat."
Write-Host "URL local: https://localhost:5173"
foreach ($address in $addresses) {
    Write-Host "URL de red: https://${address}:5173"
}
