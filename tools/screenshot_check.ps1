# 启动 MiniHub，等待窗口渲染，截全屏保存 PNG
param([int]$WaitSec = 6)
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$exe = Join-Path $PSScriptRoot "..\dist\MiniHub\MiniHub.exe"
$proc = Start-Process -FilePath $exe -PassThru
Start-Sleep -Seconds $WaitSec

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$g.Dispose()

$out = Join-Path $PSScriptRoot "app_screenshot.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

if ($proc.HasExited) {
    Write-Host "FAIL: process exited early (code $($proc.ExitCode))"
    exit 1
} else {
    Write-Host "OK: window alive, screenshot -> $out"
}
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
