Set oShell = CreateObject("WScript.Shell")

' Backend
oShell.Run "cmd /c cd /d C:\Users\Usuario\Documents\Proyectos_Milenium\CALCUFLETES && venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile certs/dev-key.pem --ssl-certfile certs/dev-cert.pem", 0, False

WScript.Sleep 3000

' Frontend
oShell.Run "cmd /c cd /d C:\Users\Usuario\Documents\Proyectos_Milenium\CALCUFLETES\frontend && npm run dev", 0, False