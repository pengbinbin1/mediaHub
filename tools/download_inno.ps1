# 通过系统代理下载 Inno Setup（PowerShell 走 Windows 证书存储，比 git-bash curl 兼容）
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Url = "https://github.com/jrsoftware/issrc/releases/download/is-6_7_4/innosetup-6.7.4.exe"
$Out = "tools\downloads\innosetup-6.7.4.exe"

# 显式走系统代理（127.0.0.1:7897）
$proxy = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings").ProxyServer
if (-not $proxy) { $proxy = "127.0.0.1:7897" }
Write-Host "using proxy: $proxy"

for ($i = 1; $i -le 5; $i++) {
    Write-Host "=== attempt $i ==="
    try {
        Invoke-WebRequest -Uri $Url -OutFile $Out -UseBasicParsing -Proxy "http://$proxy" -ProxyUseDefaultCredentials
        if ((Test-Path $Out) -and ((Get-Item $Out).Length -gt 5000000)) {
            Write-Host ("OK  {0} ({1:N1} MB)" -f $Out, ((Get-Item $Out).Length / 1MB))
            exit 0
        }
        Write-Host "downloaded file too small or missing, retrying..."
    } catch {
        Write-Host "error: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds 10
}
Write-Host "DOWNLOAD-FAILED"
exit 1
