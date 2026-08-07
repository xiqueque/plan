# 在桌面创建「每日计划」快捷方式（带应用图标）
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$pythonw = 'C:\Users\Junhong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe'
$icon = Join-Path $projectRoot 'app\assets\app_icon.ico'
$mainScript = Join-Path $projectRoot 'app\main.py'
$exe = Join-Path $projectRoot 'dist\每日计划.exe'
$lnkPath = Join-Path $desktop '每日计划.lnk'

$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut($lnkPath)
if (Test-Path $exe) {
    $lnk.TargetPath = $exe
    $lnk.Arguments = ''
} elseif (Test-Path $pythonw) {
    $lnk.TargetPath = $pythonw
    $lnk.Arguments = '"' + $mainScript + '"'
} else {
    $lnk.TargetPath = Join-Path $projectRoot '启动每日计划.bat'
    $lnk.Arguments = ''
}
$lnk.WorkingDirectory = $projectRoot
if (Test-Path $icon) {
    $lnk.IconLocation = $icon
}
$lnk.Description = '每日计划'
$lnk.Save()

Write-Host "已创建桌面快捷方式：$lnkPath"
