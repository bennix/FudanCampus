# DEPRECATED: this script corrupts GLB files. Use: python scripts/strip_modular_from_shared.py
# Remove modular building meshes from a shared district GLB (e.g. drop 3/5/7 from 03.glb).
param(
    [string]$SharedId = '03',
    [string[]]$BuildingIds = @('3', '5', '7')
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$path = Join-Path $Root "web/public/models/shared/$SharedId.glb"
$bytes = [IO.File]::ReadAllBytes($path)
$jsonLen = [BitConverter]::ToUInt32($bytes, 12)
$json = [Text.Encoding]::UTF8.GetString($bytes, 20, $jsonLen)
$gltf = $json | ConvertFrom-Json
$drop = @{}
for ($i = 0; $i -lt $gltf.nodes.Count; $i++) {
    $ex = $gltf.nodes[$i].extras
    if ($null -ne $ex -and $BuildingIds -contains [string]$ex.building_id) { $drop[$i] = $true }
}
if ($drop.Count -eq 0) { Write-Host "No nodes to remove in $SharedId.glb"; exit 0 }
$keepNodes = @()
for ($i = 0; $i -lt $gltf.nodes.Count; $i++) { if (-not $drop[$i]) { $keepNodes += $gltf.nodes[$i] } }
$gltf.nodes = $keepNodes
$gltf.scenes[0].nodes = @(0..($keepNodes.Count - 1))
$newJson = ($gltf | ConvertTo-Json -Depth 30 -Compress)
while ($newJson.Length % 4 -ne 0) { $newJson += ' ' }
$newJsonBytes = [Text.Encoding]::UTF8.GetBytes($newJson)
$binStart = 20 + $jsonLen
if ($binStart + 8 -gt $bytes.Length) { $binChunk = @() } else {
    $binLen = [BitConverter]::ToUInt32($bytes, $binStart)
    $binChunk = $bytes[($binStart + 8)..($binStart + 8 + $binLen - 1)]
}
$total = 12 + 8 + $newJsonBytes.Length + 8 + $binChunk.Length
$ms = New-Object IO.MemoryStream
$bw = New-Object IO.BinaryWriter($ms)
$bw.Write([uint32]0x46546C67); $bw.Write([uint32]2); $bw.Write([uint32]$total)
$bw.Write([uint32]$newJsonBytes.Length); $bw.Write([uint32]0x4E4F534A); $bw.Write($newJsonBytes)
$bw.Write([uint32]$binChunk.Length); $bw.Write([uint32]0x004E4942); $bw.Write($binChunk)
[IO.File]::WriteAllBytes($path, $ms.ToArray())
$hash = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($ms.ToArray())).Replace('-','').Substring(0,12).ToLower()
$manifestPath = Join-Path $Root 'web/public/campus-manifest.json'
$manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($s in $manifest.shared) {
    if ($s.id -eq $SharedId) {
        $s.revision = $hash
        $s.bytes = $ms.Length
    }
}
$manifest | ConvertTo-Json -Depth 20 | Set-Content $manifestPath -Encoding UTF8
Write-Host "Stripped $($drop.Count) nodes from shared/$SharedId.glb revision $hash"
