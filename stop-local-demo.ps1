[CmdletBinding()]
param(
    # Must match ports used by run-local-demo.ps1 (services + default web)
    [int[]]$Ports = @(3001, 3002, 3003, 3000, 5500)
)

$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = $PSScriptRoot
$PidFile = Join-Path $ProjectRoot ".logs\pids.txt"

function Stop-ProcessTree {
    param([int]$ProcessId)

    if ($ProcessId -le 0) {
        return
    }

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Stop-ListenersOnPort {
    param([int]$Port)

    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) {
        return
    }

    $owning = @($conns | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($procId in $owning) {
        if ($procId -eq 0 -or $procId -eq 4) {
            continue
        }
        Write-Host "Stopping listener on port $Port (PID $procId)"
        Stop-ProcessTree -ProcessId $procId
    }
}

# 1) Stop launcher trees from last run (PowerShell parents -> python/uvicorn children)
if (Test-Path -LiteralPath $PidFile) {
    Get-Content -LiteralPath $PidFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line) {
            return
        }

        $parts = $line -split "=", 2
        if ($parts.Count -lt 2) {
            return
        }

        $name = $parts[0].Trim()
        $idText = $parts[1].Trim()
        $id = 0
        if (-not [int]::TryParse($idText, [ref]$id)) {
            Write-Host "Skipping bad line: $line"
            return
        }

        Write-Host "Stopping $name (recorded root PID $id) and its child processes"
        Stop-ProcessTree -ProcessId $id
    }

    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}
else {
    Write-Host "No PID file at $PidFile (still sweeping ports for stray listeners)"
}

# 2) Always sweep ports — fixes orphans if only the parent was killed or PID file was lost
Write-Host "Sweeping listener ports: $($Ports -join ', ')"
foreach ($port in $Ports) {
    Stop-ListenersOnPort -Port $port
}

Write-Host "Done."
