<#
Starts Docker Desktop (optional), waits for Docker daemon to become ready,
starts the compose stack, activates the project's virtualenv, and optionally
runs DB truncate, fetch and print verification steps.

Usage examples:
  # Start Docker Desktop, bring up compose, activate venv and run clear+fetch+print
  .\scripts\dev_bootstrap.ps1 -StartDocker -RunClear -RunFetch -RunPrint -Target 2118600117 -Limit 100

  # Only bring up compose and activate venv (no DB actions)
  .\scripts\dev_bootstrap.ps1

#>

param(
    [switch]$StartDocker,
    [switch]$RunClear,
    [switch]$RunFetch,
    [switch]$RunPrint,
    [string]$Target = '2118600117',
    [int]$Limit = 100,
    [string]$PgDsn = 'postgresql://pguser:pgpass@localhost:5432/tgdata'
)

function Wait-DockerReady {
    param([int]$TimeoutSeconds = 30)
    $t = $TimeoutSeconds
    while ($t -gt 0) {
        try {
            docker info > $null 2>&1
            return $true
        } catch {
            Start-Sleep -Seconds 1
            $t -= 1
        }
    }
    return $false
}

# Determine repository root (parent of the scripts folder) and use it as cwd.
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Write-Host "Repository root: $repoRoot"
Set-Location -Path $repoRoot

if ($StartDocker) {
    Write-Host 'Starting Docker Desktop (if not running)...'
    if (-not (Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue)) {
        $exe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
        if (Test-Path $exe) {
            Start-Process -FilePath $exe
            Write-Host 'Launched Docker Desktop.'
        } else {
            Write-Host "Docker Desktop executable not found at $exe; trying to start Docker service instead."
            try { Start-Service -Name 'com.docker.service' -ErrorAction SilentlyContinue } catch { }
            try { Start-Service -Name 'Docker' -ErrorAction SilentlyContinue } catch { }
        }
    } else {
        Write-Host 'Docker Desktop already running.'
    }

    Write-Host 'Waiting for Docker daemon...'
    if (-not (Wait-DockerReady -TimeoutSeconds 60)) {
        Write-Error 'Docker did not become ready in time.'
        exit 1
    }
}

Write-Host 'Bringing up docker-compose services...'
docker compose up -d

# Activate the venv in the current session (repo root relative)
$activate = Join-Path $repoRoot '.venv\Scripts\Activate.ps1'
if (Test-Path $activate) {
    Write-Host 'Activating virtual environment...'
    . $activate
} else {
    Write-Host 'Virtualenv activate script not found (.venv\Scripts\Activate.ps1). Please create and install requirements.'
}

# Set DSN for the session
$env:PG_DSN = $PgDsn
Write-Host "PG_DSN set to: $env:PG_DSN"

if ($RunClear) {
    Write-Host 'Running scripts/clear_messages.py to truncate messages table...'
    python .\scripts\clear_messages.py
}

if ($RunFetch) {
    Write-Host "Running collect.py target=$Target limit=$Limit..."
    python .\collect.py $Target --limit $Limit --pg-dsn $env:PG_DSN
}

if ($RunPrint) {
    Write-Host 'Running scripts/print_pg.py to verify DB contents...'
    python .\scripts\print_pg.py
}

Write-Host 'Done.'
