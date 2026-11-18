# Create desktop shortcut for MiniHub.
# ASCII-only script: Chinese name is built from char codes so the file
# encoding never matters (PowerShell 5.1 reads BOM-less files as ANSI/GBK).
$ErrorActionPreference = "Stop"

# U+6781 U+7B80 U+5A92 U+4F53 U+4E2D U+5FC3 = "ji jian mei ti zhong xin"
$name = -join @([char]0x6781, [char]0x7B80, [char]0x5A92, [char]0x4F53, [char]0x4E2D, [char]0x5FC3)

$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath("Desktop")
$exe = Join-Path $PSScriptRoot "dist\MiniHub\MiniHub.exe"
if (-not (Test-Path $exe)) { Write-Error "exe not found: $exe"; exit 1 }

# Remove any existing shortcut that points to our exe (clean up garbled ones)
Get-ChildItem $desktop -Filter "*.lnk" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $l = $ws.CreateShortcut($_.FullName)
        if ($l.TargetPath -and $l.TargetPath -ieq $exe) { Remove-Item $_.FullName -Force }
    } catch { }
}

$lnkPath = Join-Path $desktop "$name.lnk"
$lnk = $ws.CreateShortcut($lnkPath)
$lnk.TargetPath = $exe
$lnk.WorkingDirectory = Split-Path $exe
$lnk.IconLocation = "$exe,0"
$lnk.Description = $name
$lnk.Save()
Write-Host "OK shortcut -> $lnkPath"
