# 验证桌面快捷方式已创建且指向正确的 exe
$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "极简媒体中心.lnk"
if (Test-Path $lnkPath) {
    $lnk = $ws.CreateShortcut($lnkPath)
    Write-Host ("OK  shortcut: " + $lnkPath)
    Write-Host ("    target  : " + $lnk.TargetPath)
    Write-Host ("    workdir : " + $lnk.WorkingDirectory)
    if (Test-Path $lnk.TargetPath) { Write-Host "    target exists" } else { Write-Host "    TARGET MISSING!" }
} else {
    Write-Host "FAIL shortcut not found: $lnkPath"
}
