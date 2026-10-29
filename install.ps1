# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Gyccc0828 and contributors

param([string]$PythonPath, [string]$CodexPath)
$ErrorActionPreference = 'Stop'
if (-not $PythonPath) { $PythonPath = (Get-Command python -ErrorAction Stop).Source }
if (-not $CodexPath) { $CodexPath = (Get-Command codex -ErrorAction Stop).Source }
$pythonw = Join-Path (Split-Path -Parent $PythonPath) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) { throw 'pythonw.exe is missing next to the selected Python interpreter.' }
& $PythonPath -c 'from PyQt5 import QtCore,QtGui,QtWidgets; import ctypes; assert ctypes.WinDLL'
if ($LASTEXITCODE -ne 0) { throw 'This Windows plugin requires PyQt5 in the selected Python environment.' }
$deployRoot = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'CodexSpeedOverlay\marketplace'
[IO.Directory]::CreateDirectory($deployRoot) | Out-Null
foreach ($part in @('.agents', 'plugins')) {
    $sourcePart = Join-Path $PSScriptRoot $part
    foreach ($file in Get-ChildItem -LiteralPath $sourcePart -Recurse -File -Force) {
        if ($file.FullName -match '[\\/]__pycache__[\\/]' -or $file.Name -eq 'runtime-path.txt') { continue }
        $relative = $file.FullName.Substring($PSScriptRoot.Length).TrimStart([char]'\', [char]'/')
        $destination = Join-Path $deployRoot $relative
        [IO.Directory]::CreateDirectory((Split-Path -Parent $destination)) | Out-Null
        if ($file.FullName -ne $destination) { Copy-Item -LiteralPath $file.FullName -Destination $destination -Force }
    }
}
$runtimeFile = Join-Path $deployRoot 'plugins\codex-speed-overlay\runtime-path.txt'
[IO.File]::WriteAllText($runtimeFile, $pythonw, [Text.Encoding]::Unicode)
& $CodexPath plugin marketplace add $deployRoot --json
if ($LASTEXITCODE -ne 0) { throw 'Could not register the local plugin marketplace.' }
& $CodexPath plugin add 'codex-speed-overlay@speed-overlay-local' --json
if ($LASTEXITCODE -ne 0) { throw 'Could not install the local plugin.' }
Write-Host 'Installed. Review and trust the SessionStart hook using /hooks before expecting automatic launch.'
Write-Host 'No hook trust, model provider, account credentials, or Windows startup settings were changed by this script.'
