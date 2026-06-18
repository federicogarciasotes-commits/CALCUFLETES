@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
  echo Falta configurar esta PC. Ejecuta CONFIGURAR_PC_NUEVA.bat.
  pause
  exit /b 1
)

if not exist "certs\dev-cert.pem" (
  echo Faltan los certificados. Ejecuta CONFIGURAR_PC_NUEVA.bat.
  pause
  exit /b 1
)

start "Calcufletes backend" /min "venv\Scripts\python.exe" -m app.run_server
timeout /t 2 /nobreak >nul
start "Calcufletes frontend" /min cmd /c "cd /d ""%~dp0frontend"" && npm run start"

echo Calcufletes iniciado en https://localhost:5173
timeout /t 4 /nobreak >nul
