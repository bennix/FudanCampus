# Dot-source this file: . .\tools\Enter-Blender.ps1
# Set BLENDER_EXE before loading to select a different installation.
$blenderResolved = 'D:\BlenderCLI\blender-4.4.3-windows-x64\blender.exe'
if ($env:BLENDER_EXE) { $blenderResolved = $env:BLENDER_EXE }
if (-not (Test-Path -LiteralPath $blenderResolved -PathType Leaf)) {
    throw "Blender not found at $blenderResolved. Install Blender 4.4.3 or set BLENDER_EXE explicitly."
}
$env:BLENDER_EXE = (Resolve-Path -LiteralPath $blenderResolved).Path
$blenderDirectory = Split-Path -Parent $env:BLENDER_EXE
$blenderOtherPaths = ($env:PATH -split ';') | Where-Object { $_ -and $_ -ne $blenderDirectory }
$env:PATH = $blenderDirectory + ';' + ($blenderOtherPaths -join ';')
Write-Host "Blender CLI: $env:BLENDER_EXE"
