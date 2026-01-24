# CRIMSON TOOLKIT - Easy Install Script for Windows

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║                                                ║" -ForegroundColor Red
Write-Host "║         CRIMSON TOOLKIT INSTALLER              ║" -ForegroundColor Red
Write-Host "║              Windows Edition                   ║" -ForegroundColor Red
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

# Check Python
Write-Host "[*] Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[+] Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[-] Python not found. Install from: https://python.org" -ForegroundColor Red
    exit 1
}

# Check Go (for PAYLOAD-CHEF)
Write-Host "[*] Checking Go installation..." -ForegroundColor Cyan
try {
    $goVersion = go version 2>&1
    Write-Host "[+] Go detected: $goVersion" -ForegroundColor Green
} catch {
    Write-Host "[!] Go not found. Installing via winget..." -ForegroundColor Yellow
    winget install GoLang.Go
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Install Python dependencies
Write-Host "[*] Installing Python dependencies..." -ForegroundColor Cyan

$tools = @("phish-forge", "target-scout", "payload-chef")

foreach ($tool in $tools) {
    if (Test-Path $tool) {
        Write-Host "[*] Setting up $tool..." -ForegroundColor Yellow
        
        if (Test-Path "$tool\requirements.txt") {
            pip install -r "$tool\requirements.txt" --quiet
            Write-Host "[+] $tool dependencies installed" -ForegroundColor Green
        }
    }
}

# Global dependencies
Write-Host "[*] Installing global dependencies..." -ForegroundColor Cyan
pip install rich colorama requests beautifulsoup4 --quiet

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                ║" -ForegroundColor Green
Write-Host "║         INSTALLATION COMPLETE!                 ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Usage Examples:" -ForegroundColor Cyan
Write-Host "  cd phish-forge && python phish-forge.py" -ForegroundColor Yellow
Write-Host "  cd target-scout && python target-scout.py" -ForegroundColor Yellow
Write-Host "  cd payload-chef && python payload-chef.py list" -ForegroundColor Yellow
Write-Host ""
