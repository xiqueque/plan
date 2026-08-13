# 更新网站下载文件：把最新的 exe 和压缩包复制到 website/download
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root 'website\download'
New-Item -ItemType Directory -Path $dest -Force | Out-Null

$exe = Join-Path $root 'dist\每日计划.exe'
$zip = 'D:\Documents\压缩\每日计划_v1.0.zip'

if (Test-Path $exe) { Copy-Item -LiteralPath $exe -Destination $dest -Force }
if (Test-Path $zip) { Copy-Item -LiteralPath $zip -Destination $dest -Force }

Get-ChildItem $dest | Select-Object Name, Length
