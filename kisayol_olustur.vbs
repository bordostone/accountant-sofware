' Özerler Mermer - Masaüstü ve Başlat Menüsü Kısayol Oluşturucu
Option Explicit

Dim ws, fso, desktop, programs, progDir, targetDir
Dim sc1, sc2, sc3, sc4

Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

If WScript.Arguments.Count > 0 Then
    targetDir = WScript.Arguments(0)
Else
    targetDir = fso.GetParentFolderName(WScript.ScriptFullName)
End If

desktop = ws.SpecialFolders("Desktop")
programs = ws.SpecialFolders("Programs")

' 1. Masaüstü Kısayolu
Set sc1 = ws.CreateShortcut(desktop & "\Özerler Mermer - Ön Muhasebe.lnk")
sc1.TargetPath = "wscript.exe"
sc1.Arguments = Chr(34) & targetDir & "\Baslat_Sessiz.vbs" & Chr(34)
sc1.WorkingDirectory = targetDir
sc1.IconLocation = targetDir & "\app.ico,0"
sc1.Description = "Özerler Mermer Ön Muhasebe ve Fatura Takip Programı"
sc1.Save

' 2. Başlat Menüsü Klasörü ve Kısayolları
progDir = programs & "\Özerler Mermer"
If Not fso.FolderExists(progDir) Then
    fso.CreateFolder(progDir)
End If

Set sc2 = ws.CreateShortcut(progDir & "\Ön Muhasebe Pro.lnk")
sc2.TargetPath = "wscript.exe"
sc2.Arguments = Chr(34) & targetDir & "\Baslat_Sessiz.vbs" & Chr(34)
sc2.WorkingDirectory = targetDir
sc2.IconLocation = targetDir & "\app.ico,0"
sc2.Save

Set sc3 = ws.CreateShortcut(progDir & "\Sunucuyu Durdur.lnk")
sc3.TargetPath = targetDir & "\Durdur.bat"
sc3.WorkingDirectory = targetDir
sc3.Save

Set sc4 = ws.CreateShortcut(progDir & "\Konsollu Başlat (Hata Ayıklama).lnk")
sc4.TargetPath = targetDir & "\Baslat.bat"
sc4.WorkingDirectory = targetDir
sc4.IconLocation = targetDir & "\app.ico,0"
sc4.Save
