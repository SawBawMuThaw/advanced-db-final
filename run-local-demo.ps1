[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$RecreateVenv,
    [switch]$VisibleWindows,
    [switch]$Reload,
    [switch]$NoWeb,
    [string]$Python = "python",
    [int]$WebPort = 5500
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$VenvDir = Join-Path $ProjectRoot ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
$LogDir = Join-Path $ProjectRoot ".logs"
$JwtPrivateKeyPath = Join-Path $LogDir "jwt_private_key.pem"
$JwtPublicKeyPath = Join-Path $LogDir "jwt_public_key.pem"

$Services = @(
    @{
        Name = "donation_user"
        Module = "donation_user.main:app"
        Port = 3001
        EnvPath = "donation_user\.env"
    },
    @{
        Name = "campaign_comment"
        Module = "campaign_comment.main:app"
        Port = 3002
        EnvPath = "campaign_comment\.env"
    },
    @{
        Name = "saga_orchestrator"
        Module = "saga_orchestrator.main:app"
        Port = 3003
        EnvPath = "saga_orchestrator\.env"
    },
    @{
        Name = "gateway"
        Module = "gateway.main:app"
        Port = 3000
        EnvPath = "gateway\.env"
    }
)

function Quote-Single {
    param([string]$Value)
    return "'" + ($Value -replace "'", "''") + "'"
}

function Quote-Argument {
    param([string]$Value)
    return '"' + ($Value -replace '"', '\"') + '"'
}

function Test-PortInUse {
    param([int]$Port)

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne(500)) {
            return $false
        }
        $client.EndConnect($async)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Assert-PortsFree {
    $ports = @($Services | ForEach-Object { $_.Port })
    if (-not $NoWeb) {
        $ports += $WebPort
    }

    $busy = @()
    foreach ($port in $ports) {
        if (Test-PortInUse -Port $port) {
            $busy += $port
        }
    }

    if ($busy.Count -gt 0) {
        throw "Port(s) already in use: $($busy -join ', '). Stop those processes or change the port before running again."
    }
}

function New-EncodedCommand {
    param([string]$ScriptText)
    return [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($ScriptText))
}

function Start-ManagedProcess {
    param(
        [string]$Name,
        [string]$ScriptText
    )

    $launcherPath = Join-Path $LogDir "start-$Name.ps1"
    $stdoutPath = Join-Path $LogDir "$Name.log"
    $stderrPath = Join-Path $LogDir "$Name.err.log"

    Set-Content -LiteralPath $launcherPath -Value $ScriptText -Encoding UTF8

    $arguments = "-NoProfile -ExecutionPolicy Bypass -File $(Quote-Argument $launcherPath)"
    $windowStyle = "Hidden"

    if ($VisibleWindows) {
        $arguments = "-NoExit $arguments"
        $windowStyle = "Normal"
    }

    $startParams = @{
        FilePath = "powershell.exe"
        ArgumentList = $arguments
        WorkingDirectory = $ProjectRoot
        WindowStyle = $windowStyle
        PassThru = $true
    }

    if (-not $VisibleWindows) {
        $startParams.RedirectStandardOutput = $stdoutPath
        $startParams.RedirectStandardError = $stderrPath
    }

    $process = Start-Process @startParams
    Start-Sleep -Milliseconds 1200

    if ($process.HasExited) {
        $out = ""
        $err = ""
        if (Test-Path -LiteralPath $stdoutPath) {
            $out = (Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue).Trim()
        }
        if (Test-Path -LiteralPath $stderrPath) {
            $err = (Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue).Trim()
        }

        throw @"
$Name exited immediately.
stdout:
$out

stderr:
$err
"@
    }

    Add-Content -LiteralPath (Join-Path $LogDir "pids.txt") -Value "$Name=$($process.Id)"
    Write-Host "Started $Name (PID $($process.Id))"
    return $process
}

function Wait-Port {
    param(
        [string]$Name,
        [int]$Port,
        [int]$TimeoutSeconds = 20
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortInUse -Port $Port) {
            return
        }
        Start-Sleep -Milliseconds 500
    }

    $stdoutPath = Join-Path $LogDir "$Name.log"
    $stderrPath = Join-Path $LogDir "$Name.err.log"
    $out = ""
    $err = ""
    if (Test-Path -LiteralPath $stdoutPath) {
        $out = (Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue).Trim()
    }
    if (Test-Path -LiteralPath $stderrPath) {
        $err = (Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue).Trim()
    }

    throw @"
$Name did not start listening on port $Port within $TimeoutSeconds seconds.
stdout:
$out

stderr:
$err
"@
}

function Ensure-DevJwtKeys {
    $keyScriptPath = Join-Path $LogDir "generate-dev-jwt-keys.py"
    $keyScript = @"
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

private_path = Path(r"$JwtPrivateKeyPath")
public_path = Path(r"$JwtPublicKeyPath")

if private_path.exists() and public_path.exists():
    raise SystemExit(0)

private_path.parent.mkdir(parents=True, exist_ok=True)
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

private_path.write_bytes(
    key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
)

public_path.write_bytes(
    key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
)
"@

    Set-Content -LiteralPath $keyScriptPath -Value $keyScript -Encoding UTF8
    & $PythonExe $keyScriptPath
}

function New-ServiceScript {
    param(
        [string]$Name,
        [string]$Module,
        [int]$Port,
        [string]$EnvPath
    )

    $root = Quote-Single $ProjectRoot
    $pythonExeQuoted = Quote-Single $PythonExe
    $envFile = Quote-Single (Join-Path $ProjectRoot $EnvPath)
    $jwtPrivate = Quote-Single $JwtPrivateKeyPath
    $jwtPublic = Quote-Single $JwtPublicKeyPath
    $reloadFlag = ""
    if ($Reload) {
        $reloadFlag = " --reload"
    }

    $runLine = "& $pythonExeQuoted -m uvicorn $Module --host 127.0.0.1 --port $Port$reloadFlag"

@"
`$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $root

function Import-DotEnv {
    param([string]`$Path)

    if (-not (Test-Path -LiteralPath `$Path)) {
        return
    }

    Get-Content -LiteralPath `$Path | ForEach-Object {
        `$line = `$_.Trim()
        if (`$line.Length -eq 0 -or `$line.StartsWith("#")) {
            return
        }

        `$separator = `$line.IndexOf("=")
        if (`$separator -lt 1) {
            return
        }

        `$key = `$line.Substring(0, `$separator).Trim()
        `$value = `$line.Substring(`$separator + 1).Trim()

        if ((`$value.StartsWith('"') -and `$value.EndsWith('"')) -or (`$value.StartsWith("'") -and `$value.EndsWith("'"))) {
            `$value = `$value.Substring(1, `$value.Length - 2)
        }

        [Environment]::SetEnvironmentVariable(`$key, `$value, "Process")
    }
}

Import-DotEnv -Path $envFile
[Environment]::SetEnvironmentVariable("JWT_PRIVATE_KEY_PATH", $jwtPrivate, "Process")
[Environment]::SetEnvironmentVariable("JWT_PUBLIC_KEY_PATH", $jwtPublic, "Process")
[Environment]::SetEnvironmentVariable("DONATION_USER_SERVICE", "http://127.0.0.1:3001", "Process")
[Environment]::SetEnvironmentVariable("USER_DONATION_SERVICE", "http://127.0.0.1:3001", "Process")
[Environment]::SetEnvironmentVariable("CAMPAIGN_COMMENT_SERVICE", "http://127.0.0.1:3002", "Process")
[Environment]::SetEnvironmentVariable("SAGA_SERVICE", "http://127.0.0.1:3003", "Process")
[Environment]::SetEnvironmentVariable("USER_SERVICE_URL", "http://127.0.0.1:3000", "Process")
Write-Host "Starting $Name on http://127.0.0.1:$Port"
$runLine
"@
}

function New-WebScript {
    $root = Quote-Single $ProjectRoot
    $pythonExeQuoted = Quote-Single $PythonExe
    $webDir = Quote-Single (Join-Path $ProjectRoot "web")

    $runLine = "& $pythonExeQuoted -m http.server $WebPort --bind 127.0.0.1 --directory $webDir"

@"
`$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $root
Write-Host "Starting web UI on http://127.0.0.1:$WebPort"
$runLine
"@
}

if (-not (Test-Path -LiteralPath $RequirementsFile)) {
    throw "Missing requirements.txt at $RequirementsFile"
}

if ($RecreateVenv -and (Test-Path -LiteralPath $VenvDir)) {
    Write-Host "Removing existing virtual environment..."
    Remove-Item -LiteralPath $VenvDir -Recurse -Force
}

if (-not (Test-Path -LiteralPath $PythonExe)) {
    Write-Host "Creating virtual environment..."
    & $Python -m venv $VenvDir
}

if (-not $SkipInstall) {
    Write-Host "Installing Python requirements..."
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r $RequirementsFile
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Ensure-DevJwtKeys
Remove-Item -LiteralPath (Join-Path $LogDir "pids.txt") -Force -ErrorAction SilentlyContinue
Assert-PortsFree

foreach ($service in $Services) {
    $scriptText = New-ServiceScript `
        -Name $service.Name `
        -Module $service.Module `
        -Port $service.Port `
        -EnvPath $service.EnvPath

    Start-ManagedProcess -Name $service.Name -ScriptText $scriptText | Out-Null
    Wait-Port -Name $service.Name -Port $service.Port
}

if (-not $NoWeb) {
    Start-ManagedProcess -Name "web" -ScriptText (New-WebScript) | Out-Null
    Wait-Port -Name "web" -Port $WebPort
}

Write-Host ""
Write-Host "Gateway: http://127.0.0.1:3000"
if (-not $NoWeb) {
    Write-Host "Web UI:  http://127.0.0.1:$WebPort"
}
Write-Host "Logs:    $LogDir"
Write-Host "PIDs:    $(Join-Path $LogDir "pids.txt")"
Write-Host ""
Write-Host "Use -SkipInstall after the first run. Use -VisibleWindows to watch each service window."
Write-Host "Use -Reload only if your Windows permissions allow Uvicorn's reloader."
