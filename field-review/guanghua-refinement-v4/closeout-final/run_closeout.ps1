[CmdletBinding()]
param(
    [ValidateSet('Full', 'Render', 'Export', 'Verify', 'Review', 'ServeReview')]
    [string]$Mode = 'Verify',
    [switch]$Strict,
    [switch]$CheckReviewPage,
    [int]$ReviewPort = 8766
)

$ErrorActionPreference = 'Stop'
$DeliveryDirectory = $PSScriptRoot
$WorkspaceDirectory = (Resolve-Path -LiteralPath (Join-Path $DeliveryDirectory '../../..')).Path
$PythonRuntime = Join-Path $WorkspaceDirectory '.local/road-venv/Scripts/python.exe'
$BlenderRuntime = Join-Path $WorkspaceDirectory '.local/blender-runtime/blender-4.4.3-windows-x64/blender.exe'
$NodeRuntime = 'D:/nodejs/node.exe'
$NpmRuntime = 'D:/nodejs/npm.cmd'
$FinalSource = Join-Path $DeliveryDirectory 'guanghua-closeout-final.blend'
$ProtectedSource = Join-Path $DeliveryDirectory '../scene-closeout-v7/guanghua-unified-closeout-v7.blend'
$ProtectedHash = '641a3ab8f02443ef98ce1bc2dcb2e8a6fdb63ba194dd6fffbec7a92aeeb146a2'

function Assert-Exit([string]$StepName) {
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $StepName (exit $LASTEXITCODE). Review its log before continuing."
    }
}

function Invoke-BlenderStep([string]$ScriptName, [string[]]$StageArguments = @()) {
    $ScriptPath = Join-Path $DeliveryDirectory $ScriptName
    if (-not (Test-Path -LiteralPath $ScriptPath)) { throw "Missing script: $ScriptPath" }
    Write-Host "Native stage: $ScriptName"
    $RunLog = Join-Path $DeliveryDirectory ('reproduce-' + [IO.Path]::GetFileNameWithoutExtension($ScriptName) + '.log')
    & $BlenderRuntime -b -t 8 --python-exit-code 1 --python $ScriptPath -- @StageArguments 2>&1 | Tee-Object -FilePath $RunLog
    Assert-Exit $ScriptName
}

function Invoke-PythonStep([string]$ScriptName, [string[]]$StageArguments = @()) {
    & $PythonRuntime -X utf8 (Join-Path $DeliveryDirectory $ScriptName) @StageArguments
    Assert-Exit $ScriptName
}

function Invoke-NodeStep([string]$ScriptName, [string[]]$StageArguments = @()) {
    & $NodeRuntime (Join-Path $DeliveryDirectory $ScriptName) @StageArguments
    Assert-Exit $ScriptName
}

function Test-CampusService {
    try {
        $CampusResponse = Invoke-WebRequest -Uri 'http://localhost:5188/' -UseBasicParsing -TimeoutSec 3
        return $CampusResponse.StatusCode -eq 200
    } catch { return $false }
}

function Start-CampusIfNeeded {
    if (Test-CampusService) { return }
    $CampusStdout = Join-Path $DeliveryDirectory 'reproduce-campus-server.log'
    $CampusStderr = Join-Path $DeliveryDirectory 'reproduce-campus-server-error.log'
    $QuotedCampusCli = '"' + (Join-Path $WorkspaceDirectory 'web/node_modules/vinext/dist/cli.js') + '"'
    Start-Process -FilePath $NodeRuntime -ArgumentList @($QuotedCampusCli, 'dev', '--host', '127.0.0.1', '--port', '5188') -WorkingDirectory (Join-Path $WorkspaceDirectory 'web') -WindowStyle Hidden -RedirectStandardOutput $CampusStdout -RedirectStandardError $CampusStderr | Out-Null
    for ($Attempt = 0; $Attempt -lt 20; $Attempt++) {
        if (Test-CampusService) { return }
        Start-Sleep -Milliseconds 1500
    }
    throw 'Campus service did not become ready at http://localhost:5188/. Review the server log.'
}

function Invoke-WebChecks {
    Push-Location (Join-Path $WorkspaceDirectory 'web')
    try {
        & $NodeRuntime 'validate-models.mjs'
        Assert-Exit 'validate-models'
    } finally { Pop-Location }
    Start-CampusIfNeeded
    Invoke-NodeStep 'benchmark.cjs' @('final')
    $WebQaScript = @('web-qa.cjs', 'web_qa.cjs', 'browser_qa.cjs') | Where-Object { Test-Path -LiteralPath (Join-Path $DeliveryDirectory $_) } | Select-Object -First 1
    if ($WebQaScript) {
        Invoke-NodeStep $WebQaScript @('visual', '--frozen')
        Invoke-NodeStep $WebQaScript @('performance', '--frozen')
        Invoke-NodeStep $WebQaScript @('build', '--frozen')
        Invoke-NodeStep $WebQaScript @('decode', '--frozen')
        Invoke-BlenderStep 'reimport-check.py'
    } else {
        Write-Warning 'The saved browser QA entry is missing. web-checks.json will not be fabricated; strict delivery remains blocked.'
    }
}

foreach ($RuntimePath in @($PythonRuntime, $NodeRuntime)) {
    if (-not (Test-Path -LiteralPath $RuntimePath)) { throw "Configured runtime is missing: $RuntimePath" }
}
if ((Get-FileHash -LiteralPath $ProtectedSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ProtectedHash) {
    throw 'The accepted v7 baseline hash changed. No reconstruction stage was run.'
}
if ($Mode -in @('Full', 'Render', 'Export', 'Verify') -and -not (Test-Path -LiteralPath $BlenderRuntime)) {
    throw "Configured Blender runtime is missing: $BlenderRuntime"
}

Push-Location $WorkspaceDirectory
try {
    if ($Mode -eq 'Full') {
        # Every full native run begins at v7; incremental geometry stages are not
        # repeated on an already edited source. Existing historical files remain.
        Invoke-BlenderStep 'audit_baseline.py'
        Invoke-BlenderStep 'extract_structure.py'
        Invoke-PythonStep 'prepare_planters.py'
        Invoke-PythonStep 'prepare_structures.py'
        Invoke-BlenderStep 'assemble.py'
        Invoke-BlenderStep 'finish.py'
        Invoke-BlenderStep 'finish_surfaces.py'
        Invoke-BlenderStep 'repair_shared_foliage.py'
        Invoke-BlenderStep 'refine_canopy.py'
        Invoke-BlenderStep 'repair_ground.py'
        Invoke-BlenderStep 'extract_native_audit_geometry.py'
        Invoke-PythonStep 'prepare_ground_trim.py' @('--padding', '0')
        Invoke-BlenderStep 'repair_native_audit.py'
        # The second cutter is rebuilt from the same original geometry extract;
        # it records the now-current source SHA and fixes only float32 boundaries.
        Invoke-PythonStep 'prepare_ground_trim.py' @('--padding', '0.00002')
        Invoke-BlenderStep 'repair_ground_trim_boundary.py'
        Invoke-PythonStep 'verify_ground_trim.py'
        Invoke-PythonStep 'fit_camera.py'
    }
    if ($Mode -in @('Full', 'Verify')) {
        Invoke-BlenderStep 'audit_native.py'
        Invoke-BlenderStep 'camera_validate.py'
    }
    if ($Mode -in @('Full', 'Render')) {
        Invoke-BlenderStep 'render.py' @('final')
        Invoke-BlenderStep 'render.py' @('canopy-before')
    }
    if ($Mode -in @('Full', 'Export')) {
        Invoke-BlenderStep 'export_web.py'
        Invoke-NodeStep 'optimize.mjs'
        Invoke-NodeStep 'trim_forest.mjs'
        & $PythonRuntime -X utf8 (Join-Path $WorkspaceDirectory 'scripts/integrate_guanghua_landscape.py') --source $FinalSource --report-dir $DeliveryDirectory
        Assert-Exit 'local campus integration'
    }
    if ($Mode -in @('Full', 'Export', 'Verify')) { Invoke-WebChecks }
    if ($Mode -eq 'ServeReview') {
        $ReviewStdout = Join-Path $DeliveryDirectory 'review-server.log'
        $ReviewStderr = Join-Path $DeliveryDirectory 'review-server-error.log'
        $QuotedDirectory = '"' + $WorkspaceDirectory + '"'
        Start-Process -FilePath $PythonRuntime -ArgumentList @('-X', 'utf8', '-m', 'http.server', $ReviewPort, '--bind', '127.0.0.1', '--directory', $QuotedDirectory) -WorkingDirectory $WorkspaceDirectory -WindowStyle Hidden -RedirectStandardOutput $ReviewStdout -RedirectStandardError $ReviewStderr | Out-Null
        Write-Host "Review: http://127.0.0.1:$ReviewPort/field-review/guanghua-refinement-v4/closeout-final/review.html"
    }
    $ReviewArguments = @('--campus-url', 'http://localhost:5188/')
    if ($Strict) { $ReviewArguments += '--strict' }
    Invoke-PythonStep 'build_review.py' $ReviewArguments
    if ($CheckReviewPage) {
        Invoke-NodeStep 'review_page_qa.cjs' @("http://127.0.0.1:$ReviewPort/field-review/guanghua-refinement-v4/closeout-final/review.html")
    }
    if ((Get-FileHash -LiteralPath $ProtectedSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ProtectedHash) { throw 'Protected v7 changed during reproduction.' }
    Write-Host 'Review and version evidence refreshed. The current-scene pointer, Git history and publishing were not changed by this entry.'
} finally { Pop-Location }
