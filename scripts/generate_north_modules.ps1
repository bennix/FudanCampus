# Build GLB modules for north-campus buildings 3, 5, 7 from north_buildings_specs.json
# Run from repo root: powershell -ExecutionPolicy Bypass -File scripts/generate_north_modules.ps1
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Public = Join-Path $Root 'web/public'
$utf8 = New-Object System.Text.UTF8Encoding $false
function Read-Json($path) {
    return (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
$Specs = Read-Json (Join-Path $Root 'scripts/north_buildings_specs.json')
$Records = Read-Json (Join-Path $Root 'references/buildings.json')
$Labels = (Read-Json (Join-Path $Public 'buildings.json')).buildings
$ManifestPath = Join-Path $Public 'campus-manifest.json'
$Manifest = Read-Json $ManifestPath

function Get-CampusXY($record) {
    $x = ($record.x - 1200) * 0.8
    $y = (1000 - $record.y) * 0.8
    return @($x, $y)
}

function Add-BoxMesh($meshes, $matIndex, $offX, $offY, $offZ, $width, $depth, $height) {
    $offX = [double]$offX; $offY = [double]$offY; $offZ = [double]$offZ
    $width = [double]$width; $depth = [double]$depth; $height = [double]$height
    $halfW = $width / 2.0; $halfD = $depth / 2.0; $halfH = $height / 2.0
    $corners = @(
        @($( $offX - $halfW), $( $offY - $halfD), $( $offZ - $halfH)),
        @($( $offX + $halfW), $( $offY - $halfD), $( $offZ - $halfH)),
        @($( $offX - $halfW), $( $offY + $halfD), $( $offZ - $halfH)),
        @($( $offX + $halfW), $( $offY + $halfD), $( $offZ - $halfH)),
        @($( $offX - $halfW), $( $offY - $halfD), $( $offZ + $halfH)),
        @($( $offX + $halfW), $( $offY - $halfD), $( $offZ + $halfH)),
        @($( $offX - $halfW), $( $offY + $halfD), $( $offZ + $halfH)),
        @($( $offX + $halfW), $( $offY + $halfD), $( $offZ + $halfH))
    )
    $base = $meshes[$matIndex].vertices.Count
    foreach ($c in $corners) { [void]$meshes[$matIndex].vertices.Add($c) }
    $faces = @(
        @(0, 2, 6, 4), @(1, 5, 7, 3), @(0, 1, 5, 4), @(2, 3, 7, 6), @(0, 1, 3, 2), @(4, 5, 7, 6)
    )
    foreach ($f in $faces) {
        [void]$meshes[$matIndex].indices.Add($base + $f[0])
        [void]$meshes[$matIndex].indices.Add($base + $f[1])
        [void]$meshes[$matIndex].indices.Add($base + $f[2])
        [void]$meshes[$matIndex].indices.Add($base + $f[0])
        [void]$meshes[$matIndex].indices.Add($base + $f[2])
        [void]$meshes[$matIndex].indices.Add($base + $f[3])
    }
}

function Get-Bounds($vertices) {
    $min = @(1e9, 1e9, 1e9); $max = @(-1e9, -1e9, -1e9)
    foreach ($v in $vertices) {
        $tx = $v[0]; $ty = $v[2]; $tz = -$v[1]
        if ($tx -lt $min[0]) { $min[0] = $tx }
        if ($ty -lt $min[1]) { $min[1] = $ty }
        if ($tz -lt $min[2]) { $min[2] = $tz }
        if ($tx -gt $max[0]) { $max[0] = $tx }
        if ($ty -gt $max[1]) { $max[1] = $ty }
        if ($tz -gt $max[2]) { $max[2] = $tz }
    }
    return @{ min = $min; max = $max }
}

function Write-Glb($path, $bid, $bname, $materials, $meshes) {
    $accessors = @(); $bufferViews = @(); $nodes = @(); $meshesOut = @()
    $bin = New-Object System.Collections.Generic.List[byte]
    $accIndex = 0; $meshIndex = 0
    foreach ($mesh in $meshes) {
        if ($mesh.indices.Count -eq 0) { continue }
        $posBytes = New-Object System.Collections.Generic.List[byte]
        foreach ($v in $mesh.vertices) {
            $posBytes.AddRange([BitConverter]::GetBytes([single]$v[0]))
            $posBytes.AddRange([BitConverter]::GetBytes([single]$v[2]))
            $posBytes.AddRange([BitConverter]::GetBytes([single](-$v[1])))
        }
        $idxBytes = New-Object System.Collections.Generic.List[byte]
        foreach ($i in $mesh.indices) {
            $idxBytes.AddRange([BitConverter]::GetBytes([uint16]$i))
        }
        $posOffset = $bin.Count
        $bin.AddRange($posBytes)
        while ($bin.Count % 4 -ne 0) { [void]$bin.Add(0) }
        $idxOffset = $bin.Count
        $bin.AddRange($idxBytes)
        while ($bin.Count % 4 -ne 0) { [void]$bin.Add(0) }
        $posView = $bufferViews.Count
        $bufferViews += @{
            buffer = 0; byteOffset = $posOffset; byteLength = $posBytes.Count
            target = $null
        }
        $idxView = $bufferViews.Count
        $bufferViews += @{
            buffer = 0; byteOffset = $idxOffset; byteLength = $idxBytes.Count
            target = 34963
        }
        $posAcc = $accIndex; $accIndex++
        $accessors += @{
            bufferView = $posView; componentType = 5126; count = $mesh.vertices.Count; type = 'VEC3'
            min = @(
                ($mesh.vertices | ForEach-Object { [double]$_[0] } | Measure-Object -Minimum).Minimum,
                ($mesh.vertices | ForEach-Object { [double]$_[2] } | Measure-Object -Minimum).Minimum,
                ($mesh.vertices | ForEach-Object { [double](-$_[1]) } | Measure-Object -Minimum).Minimum
            )
            max = @(
                ($mesh.vertices | ForEach-Object { [double]$_[0] } | Measure-Object -Maximum).Maximum,
                ($mesh.vertices | ForEach-Object { [double]$_[2] } | Measure-Object -Maximum).Maximum,
                ($mesh.vertices | ForEach-Object { [double](-$_[1]) } | Measure-Object -Maximum).Maximum
            )
        }
        $idxAcc = $accIndex; $accIndex++
        $accessors += @{
            bufferView = $idxView; componentType = 5123; count = $mesh.indices.Count; type = 'SCALAR'
        }
        $meshesOut += @{
            primitives = @(@{ attributes = @{ POSITION = $posAcc }; indices = $idxAcc; material = $mesh.matIndex })
        }
        $nodes += @{
            name = $mesh.name; mesh = $meshIndex
            extras = @{ building_id = $bid; building_name = $bname }
        }
        $meshIndex++
    }
    $gltf = @{
        asset = @{ version = '2.0'; generator = 'generate_north_modules.ps1' }
        scene = 0
        scenes = @(@{ nodes = (0..($nodes.Count - 1)) })
        nodes = $nodes
        meshes = $meshesOut
        materials = $materials
        accessors = $accessors
        bufferViews = $bufferViews
        buffers = @(@{ byteLength = $bin.Count })
    }
    $json = ($gltf | ConvertTo-Json -Depth 20 -Compress)
    $jsonBytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    while ($jsonBytes.Length % 4 -ne 0) { $json = $json + ' '; $jsonBytes = [System.Text.Encoding]::UTF8.GetBytes($json) }
    $total = 12 + 8 + $jsonBytes.Length + 8 + $bin.Count
    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($ms)
    $bw.Write([uint32]0x46546C67); $bw.Write([uint32]2); $bw.Write([uint32]$total)
    $bw.Write([uint32]$jsonBytes.Length); $bw.Write([uint32]0x4E4F534A); $bw.Write($jsonBytes)
    $bw.Write([uint32]$bin.Count); $bw.Write([uint32]0x004E4942); $bw.Write($bin.ToArray())
    $dir = Split-Path -Parent $path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllBytes($path, $ms.ToArray())
    return $ms.ToArray()
}

foreach ($bid in @('3','5','7')) {
    $spec = $Specs.$bid
    $record = $Records | Where-Object { $_.id -eq $bid } | Select-Object -First 1
    $label = $Labels | Where-Object { $_.id -eq $bid } | Select-Object -First 1
    $campus = Get-CampusXY $record
    $cx = $campus[0]; $cy = $campus[1]
    $matKeys = @($spec.materials.PSObject.Properties.Name)
    $materials = @()
    for ($i = 0; $i -lt $matKeys.Count; $i++) {
        $k = $matKeys[$i]; $c = $spec.materials.$k
        $materials += @{
            name = "North $bid $k"
            doubleSided = $true
            emissiveFactor = @([double]$c[0], [double]$c[1], [double]$c[2])
            pbrMetallicRoughness = @{
                baseColorFactor = @([double]$c[0], [double]$c[1], [double]$c[2], 1.0)
                metallicFactor = 0.0; roughnessFactor = $(if ($k -eq 'glass') { 0.35 } else { 0.55 })
            }
        }
    }
    $matIndexMap = @{}
    for ($i = 0; $i -lt $matKeys.Count; $i++) { $matIndexMap[$matKeys[$i]] = $i }

    foreach ($kind in @('detail','overview')) {
        $boxList = if ($kind -eq 'detail') { $spec.boxes } else { $spec.overview_boxes }
        $meshList = @()
        for ($i = 0; $i -lt $matKeys.Count; $i++) {
            $meshList += [PSCustomObject]@{
                name = "$($spec.name) · North $bid $($matKeys[$i])"
                matIndex = $i; vertices = New-Object System.Collections.Generic.List[object]
                indices = New-Object System.Collections.Generic.List[int]
            }
        }
        foreach ($box in $boxList) {
            $mi = $matIndexMap[$box.m]
            Add-BoxMesh -meshes $meshList -matIndex $mi -offX $box.dx -offY $box.dy -offZ $box.z -width $box.width -depth $box.depth -height $box.height
        }
        $rel = if ($kind -eq 'detail') { "models/buildings/$bid.glb" } else { "models/overview/$bid.glb" }
        $path = Join-Path $Public $rel
        $bytes = Write-Glb $path $bid $spec.name $materials $meshList
        $hash = [BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace('-','').Substring(0,12).ToLower()
        if ($kind -eq 'detail') {
            $allVerts = New-Object System.Collections.Generic.List[object]
            foreach ($m in $meshList) { foreach ($v in $m.vertices) { [void]$allVerts.Add($v) } }
            $bounds = Get-Bounds $allVerts
            $entry = @{
                id = $bid
                name = $spec.name
                url = $rel
                revision = $hash
                bytes = $bytes.Length
                overview = $null
                position = @($cx, 0, -$cy)
                rotation = @(0, 0, 0)
                orientationBaked = $true
                bounds = @{ min = @($bounds.min[0], $bounds.min[1], $bounds.min[2]); max = @($bounds.max[0], $bounds.max[1], $bounds.max[2]) }
                labelPosition = $label.position
                loadDistance = 240
            }
        } else {
            $ovBytes = $bytes
            $ovHash = $hash
            $ovRel = $rel
        }
    }
    $entry.overview = @{ url = $ovRel; revision = $ovHash; bytes = $ovBytes.Length }
    $Manifest.buildings = @($Manifest.buildings | Where-Object { $_.id -ne $bid })
    $Manifest.buildings += $entry
    Write-Host "Wrote building $bid $($spec.name)"
}

$Manifest.buildings = @($Manifest.buildings | Sort-Object { [int]$_.id })
$Manifest | ConvertTo-Json -Depth 20 | Set-Content -Path $ManifestPath -Encoding UTF8
Write-Host 'Updated campus-manifest.json'
