Set oShell = CreateObject("WScript.Shell")

' Backend
oShell.Run "cmd /c cd /d C:\Users\Usuario\Documents\Proyectos_Milenium\CALCUFLETES && venv\Scripts\activate && python -m app.run_server", 0, False

WScript.Sleep 3000

' Frontend
oShell.Run "cmd /c cd /d C:\Users\Usuario\Documents\Proyectos_Milenium\CALCUFLETES\frontend && npm run start", 0, False
