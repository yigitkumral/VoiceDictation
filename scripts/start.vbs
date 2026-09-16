' VoiceDictation - Windows gizli baslatici (Startup kisayolu buna bakar).
' Repo kokunu kendi konumundan bulur (scripts\ klasorunun bir ustu); yol sabit yazilmaz.
Option Explicit
Dim fso, sh, repo, py
Set fso = CreateObject("Scripting.FileSystemObject")
repo = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
py = repo & "\venv\Scripts\pythonw.exe"
If Not fso.FileExists(py) Then
    MsgBox "venv bulunamadi: " & py & vbCrLf & "Once scripts\setup.bat calistirin.", vbExclamation, "VoiceDictation"
    WScript.Quit 1
End If
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = repo
sh.Run """" & py & """ dictation.py", 0, False
