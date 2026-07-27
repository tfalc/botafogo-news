# Download Botafogo brand manual (local reference only)
$ErrorActionPreference = 'Stop'
$destDir = Join-Path $PSScriptRoot 'botafogo'
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$dest = Join-Path $destDir 'manual_marca_botafogo.pdf'
$url = 'https://static.botafogo.com.br/upload/manual_marca.pdf'
Write-Host "Downloading $url ..."
Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
Get-Item $dest | Format-List FullName, Length, LastWriteTime
Write-Host 'Done. See USAGE-RIGHTS.md before using any visual element on the public site.'
