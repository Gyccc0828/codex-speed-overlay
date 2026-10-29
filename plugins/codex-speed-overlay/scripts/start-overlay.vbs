' SPDX-License-Identifier: GPL-3.0-only
' Copyright (C) 2026 Gyccc0828 and contributors

Option Explicit
On Error Resume Next
Dim fs, shell, pluginRoot, runtimeFile, stream, runtime, app
Set fs = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
pluginRoot = fs.GetParentFolderName(fs.GetParentFolderName(WScript.ScriptFullName))
runtimeFile = fs.BuildPath(pluginRoot, "runtime-path.txt")
If Not fs.FileExists(runtimeFile) Then WScript.Quit 0
Set stream = fs.OpenTextFile(runtimeFile, 1, False, -1)
runtime = Trim(stream.ReadAll)
stream.Close
If Not fs.FileExists(runtime) Then WScript.Quit 0
app = fs.BuildPath(pluginRoot, "app\overlay.pyw")
If Not fs.FileExists(app) Then WScript.Quit 0
shell.Run """" & runtime & """ """ & app & """", 1, False
WScript.Quit 0
