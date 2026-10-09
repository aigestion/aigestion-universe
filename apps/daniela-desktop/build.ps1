<#
.SYNOPSIS
    Compila Daniela Desktop con el toolchain correcto.

.DESCRIPTION
    En esta maquina hay DOS instalaciones de Rust en el PATH:
      - Chocolatey (rust-x86_64-pc-windows-gnu), que necesita `dlltool.exe`
        (MinGW) y falla al compilar cualquier crate que use `#[link]`.
      - rustup (stable-x86_64-pc-windows-msvc), que es la que corresponde y
        usa el linker de MSVC (Visual Studio Build Tools 18).

    Este script pone rustup por delante y carga el entorno de MSVC, asi que
    `.\build.ps1` funciona sin tocar el PATH global.

.EXAMPLE
    .\build.ps1                 # debug
    .\build.ps1 --release       # release
    .\build.ps1 --run           # compila y lanza
#>
[CmdletBinding()]
param(
    [switch]$Release,
    [switch]$Run
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ── 1. Entorno de MSVC (link.exe / lib.exe) ─────────────────────────
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path -LiteralPath $vswhere) {
    $vs = & $vswhere -latest -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath
    if ($vs) {
        $vcvars = Join-Path $vs 'VC\Auxiliary\Build\vcvars64.bat'
        if (Test-Path -LiteralPath $vcvars) {
            Write-Host "[build] cargando entorno MSVC: $vs" -ForegroundColor DarkGray
            # vcvars64.bat escribe en el entorno del proceso hijo; volcamos su
            # resultado a este para que lo hereden cargo y rustc.
            $line = cmd /c "`"$vcvars`" >nul 2>&1 && set"
            foreach ($l in $line) {
                if ($l -match '^([^=]+)=(.*)$') { Set-Item -Path "env:$($matches[1])" -Value $matches[2] }
            }
        }
    }
}
else {
    Write-Warning 'vswhere no encontrado: se espera que link.exe ya este en el PATH.'
}

# ── 2. rustup por delante de Chocolatey ─────────────────────────────
$rustupBin = Join-Path $env:USERPROFILE '.cargo\bin'
if (Test-Path -LiteralPath $rustupBin) {
    $env:PATH = "$rustupBin;$env:PATH"
}
$toolchainBin = Join-Path $env:USERPROFILE '.rustup\toolchains\stable-x86_64-pc-windows-msvc\bin'
if (Test-Path -LiteralPath $toolchainBin) {
    $env:PATH = "$toolchainBin;$env:PATH"
}

$host_ = & rustc -vV | Select-String 'host:' | ForEach-Object { $_.ToString().Split(':')[1].Trim() }
Write-Host "[build] toolchain: $host_  ($( & rustc --version ))" -ForegroundColor Cyan
if ($host_ -ne 'x86_64-pc-windows-msvc') {
    throw "Se esperaba el toolchain MSVC y hay '$host_'. Revisa el PATH o `rustup toolchain install stable-x86_64-pc-windows-msvc`."
}

# ── 3. Compilar ─────────────────────────────────────────────────────
$flags = @()
if ($Release) { $flags += '--release' }
& cargo build --manifest-path (Join-Path $raiz 'Cargo.toml') @flags
if ($LASTEXITCODE -ne 0) { throw "cargo build fallo ($LASTEXITCODE)" }

$bin = if ($Release) { 'release' } else { 'debug' }
$exe = Join-Path $raiz "target\$bin\daniela-desktop.exe"
Write-Host "[build] ok: $exe" -ForegroundColor Green

if ($Run) {
    Write-Host '[build] lanzando...' -ForegroundColor Cyan
    & $exe
}