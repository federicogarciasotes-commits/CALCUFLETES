Set oShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectDir = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))

' Backend
oShell.Run "cmd /c cd /d """ & projectDir & """ && venv\Scripts\python.exe -m app.run_server", 0, False

WScript.Sleep 3000

' Frontend
oShell.Run "cmd /c cd /d """ & projectDir & "\frontend"" && npm run start", 0, False
