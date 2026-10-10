' Ozerler Mermer - On Muhasebe Pro Sessiz Masaustu Baslatici
Option Explicit

Dim fso, WshShell, currentPath, runPy, pywExe

Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

currentPath = fso.GetParentFolderName(WScript.ScriptFullName)
runPy = currentPath & "\run.py"
WshShell.CurrentDirectory = currentPath

' 1. Yerel pythonw veya sistem pythonw kontrolu
Dim candidates, p, userProf, progFiles, progFiles86, localApp
userProf = WshShell.ExpandEnvironmentStrings("%USERPROFILE%")
localApp = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
progFiles = WshShell.ExpandEnvironmentStrings("%ProgramFiles%")
progFiles86 = WshShell.ExpandEnvironmentStrings("%ProgramFiles(x86)%")

candidates = Array(_
    currentPath & "\.venv\Scripts\pythonw.exe",_
    currentPath & "\python\pythonw.exe",_
    localApp & "\Programs\Python\Python313\pythonw.exe",_
    localApp & "\Programs\Python\Python312\pythonw.exe",_
    localApp & "\Programs\Python\Python311\pythonw.exe",_
    localApp & "\Programs\Python\Python310\pythonw.exe",_
    localApp & "\Programs\Python\Python39\pythonw.exe",_
    progFiles & "\Python313\pythonw.exe",_
    progFiles & "\Python312\pythonw.exe",_
    progFiles & "\Python311\pythonw.exe",_
    progFiles & "\Python310\pythonw.exe",_
    "C:\Python312\pythonw.exe",_
    "C:\Python311\pythonw.exe",_
    "C:\Python310\pythonw.exe"_
)

pywExe = ""
For Each p In candidates
    If fso.FileExists(p) Then
        pywExe = p
        Exit For
    End If
Next

If pywExe <> "" Then
    ' pythonw ile tamamen sessiz (sifir konsol penceresi) baslat
    WshShell.Run Chr(34) & pywExe & Chr(34) & " " & Chr(34) & runPy & Chr(34), 0, False
Else
    ' Pythonw yolu bulunamadiysa, pyw/pythonw komutunu dene veya Baslat.bat'a yonlendir
    On Error Resume Next
    Dim exitCode
    exitCode = WshShell.Run("pyw -3 " & Chr(34) & runPy & Chr(34), 0, False)
    If Err.Number <> 0 Then
        Err.Clear
        exitCode = WshShell.Run("pythonw " & Chr(34) & runPy & Chr(34), 0, False)
        If Err.Number <> 0 Then
            WshShell.Run Chr(34) & currentPath & "\Baslat.bat" & Chr(34), 1, False
        End If
    End If
    On Error GoTo 0
End If
