Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")

REM 检查是否已有 python.exe 进程在运行 main.py
Set colItems = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'python.exe' AND CommandLine LIKE '%main.py%'")

If colItems.Count > 0 Then
    WScript.Quit
End If

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = fso.BuildPath(scriptDir, "start_service.bat")
WshShell.Run Chr(34) & batPath & Chr(34), 0, False
