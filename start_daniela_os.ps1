<#
.SYNOPSIS
  Arranque completo Daniela OS: Docker (slim) + Desktop + Dashboard + Health Check
.DESCRIPTION
  Ejecutar al login (Task Scheduler o Startup folder).
  Idempotente: si ya corre, no duplica.
#>
param(
    [switch]$SkipDocker,
    [switch]$SkipDesktop,
    [switch]$Verbose
)

$ErrorActionPreference = "SilentlyContinue"
$Repo = "C:\Users\Alejandro\aig"
$LogDir = Join-Path $Repo "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = Join-Path $LogDir "daniela_os_startup.log"

function Log([string]$Msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Log-Error([string]$Msg) {
    $line = "[{0}] ERROR: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Write-Host $line -ForegroundColor Red
    Add-Content -Path $LogFile -Value $line
}

Log "=========================================="
Log "DANIELA OS STARTUP INICIADO"
Log "=========================================="

# 1. Docker Stack (slim - 10 servicios core)
if (-not $SkipDocker) {
    Log "Levantando Docker stack (slim - 10 servicios core)..."
    Set-Location $Repo
    try {
        $running = docker compose -f config\docker\docker-compose.slim.yml ps -q 2>$null
        if (-not $running) {
            Log "  No hay contenedores corriendo. Arrancando..."
            $result = docker compose -f config\docker\docker-compose.slim.yml up -d 2>&1
            if ($LASTEXITCODE -ne 0) {
                Log-Error "  Fallo al arrancar: $result"
            } else {
                Log "  Contenedores arrancados. Esperando health checks (60s)..."
                Start-Sleep 60
            }
        } else {
            Log "  Ya corriendo ($($running.Count) contenedores)"
        }
    } catch {
        Log-Error "  Excepcion Docker: $($_.Exception.Message)"
    }
}

# 2. Desktop
if (-not $SkipDesktop) {
    Log "Arrancando escritorio cyberpunk..."
    try {
        & "$Repo\scripts\desktop\start_desktop.ps1" -Dashboard
        Log "  Desktop + Dashboard lanzado"
    } catch {
        Log-Error "  Excepcion Desktop: $($_.Exception.Message)"
    }
}

# 3. Health Gate - Solo servicios core del stack slim
Log "Verificando salud de servicios core..."
try {
    $coreServices = @(
        @{name="daniela"; port=9200; path="/api/status"},
        @{name="hermes"; port=9300; path="/api/status"},
        @{name="infra"; port=9700; path="/api/infra/status"},
        @{name="perf"; port=9998; path="/api/perf/status"}
    )
    $healthy = 0
    foreach ($svc in $coreServices) {
        $url = "http://localhost:$($svc.port)$($svc.path)"
        try {
            $resp = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
            if ($resp.StatusCode -eq 200) {
                $data = $resp.Content | ConvertFrom-Json
                $status = $data.status
                if ($status -in @("alive","healthy","ok","running")) {
                    Log "  OK $($svc.name):$($svc.port) UP ($status)"
                    $healthy++
                } else {
                    Log "  WARN $($svc.name):$($svc.port) status=$status"
                }
            } else {
                Log "  FAIL $($svc.name):$($svc.port) HTTP $($resp.StatusCode)"
            }
        } catch {
            Log "  FAIL $($svc.name):$($svc.port) $($_.Exception.Message)"
        }
    }
    Log "  $healthy/$($coreServices.Count) servicios core UP"
    if ($healthy -lt $coreServices.Count) {
        Log-Error "  ALGUNOS SERVICIOS CORE NO ESTAN SALUDABLES"
    }
} catch {
    Log-Error "  Excepcion Health Gate: $($_.Exception.Message)"
}

Log "DANIELA OS VIVA"
Log "=========================================="