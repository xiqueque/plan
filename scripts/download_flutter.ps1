$ErrorActionPreference = 'Stop'
$total = 1927280652
$n = 8
$seg = [math]::Ceiling($total / $n)
$url = 'https://mirror.nju.edu.cn/flutter/flutter_infra_release/releases/stable/windows/flutter_windows_3.47.0-stable.zip'
$resolve = 'mirror.nju.edu.cn:443:210.28.130.3'

function Get-Len([string]$p) {
  if (Test-Path $p) { return (Get-Item $p).Length } else { return 0 }
}

for ($i = 0; $i -lt $n; $i++) {
  $segStart = $i * $seg
  $end = [Math]::Min($segStart + $seg - 1, $total - 1)
  $expected = $end - $segStart + 1
  $part = "D:\dev\flutter_part_${i}.bin"
  $tmp = "D:\dev\flutter_part_${i}.tmp"
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  $cur = Get-Len $part
  if ($cur -ge $expected) {
    Write-Output "part ${i} already complete"
    continue
  }
  Write-Output "part ${i}: resume from $([math]::Round($cur / 1MB, 1))MB to $([math]::Round($expected / 1MB, 1))MB"
  $failCount = 0
  while ($cur -lt $expected) {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    $fromAbs = $segStart + $cur
    & curl.exe -s -L --retry 3 --connect-timeout 30 --speed-limit 1024 --speed-time 60 --resolve $resolve -r "${fromAbs}-${end}" -o $tmp $url
    $got = Get-Len $tmp
    if ($got -gt 0) {
      $fs = [System.IO.File]::Open($part, 'Append')
      try {
        $bytes = [System.IO.File]::ReadAllBytes($tmp)
        $take = [Math]::Min($bytes.Length, $expected - $cur)
        $fs.Write($bytes, 0, $take)
      } finally {
        $fs.Dispose()
      }
      Remove-Item $tmp -Force -ErrorAction SilentlyContinue
      $cur = Get-Len $part
      $failCount = 0
      Write-Output "part ${i}: $([math]::Round($cur / 1MB, 1))MB / $([math]::Round($expected / 1MB, 1))MB"
      if ($cur -gt $expected) {
        Write-Output "part ${i}: size exceeded, truncating to expected"
        $fs2 = [System.IO.File]::Open($part, 'Open')
        try {
          $fs2.SetLength($expected)
        } finally {
          $fs2.Dispose()
        }
        $cur = $expected
      }
    } else {
      $failCount++
      if ($failCount -ge 10) {
        Write-Output "part ${i}: 10 consecutive failures, pause 30s"
        $failCount = 0
        Start-Sleep -Seconds 30
      } else {
        Start-Sleep -Seconds 5
      }
    }
  }
  Write-Output "part ${i} done ($([math]::Round($cur / 1MB, 1))MB)"
}

$sum = (Get-ChildItem D:\dev\flutter_part_*.bin | Measure-Object Length -Sum).Sum
Write-Output "ALL DONE: $([math]::Round($sum / 1MB, 1))MB / $([math]::Round($total / 1MB, 1))MB"
