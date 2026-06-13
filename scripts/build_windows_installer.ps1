$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$version = uv run python -c "import tomllib; print(tomllib.loads(open('pyproject.toml','rb').read().decode('utf-8'))['project']['version'])"
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"

if (-not (Test-Path $iscc)) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "未找到 Inno Setup 编译器 ISCC.exe"
    }
    $iscc = $command.Source
}

if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }

uv run pyinstaller `
    --name TomatoClock `
    --windowed `
    --clean `
    --noconfirm `
    --add-data "pyproject.toml;." `
    --icon icon.ico `
    src/main.py

& $iscc `
    "/DAppVersion=$version" `
    "/DSourceDir=$($root)\dist\TomatoClock" `
    "/O$($root)\dist" `
    "$($root)\packaging\windows\TomatoClock.iss"

$installer = Join-Path $root "dist\TomatoClock-Setup-$version-Windows.exe"
$hash = Get-FileHash -Algorithm SHA256 $installer
"$($hash.Hash.ToLower())  $(Split-Path $installer -Leaf)" | Set-Content "$installer.sha256"
Write-Host "Created $installer"
