# Stripe CLI Installation Script for Windows
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Stripe CLI Installation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Download URL (latest release)
$stripeCliUrl = "https://github.com/stripe/stripe-cli/releases/download/v1.21.8/stripe_1.21.8_windows_x86_64.zip"
$downloadPath = "$env:TEMP\stripe_cli.zip"
$extractPath = "$env:USERPROFILE\.stripe"

Write-Host "[1/4] Erstelle Stripe-Verzeichnis..." -ForegroundColor Yellow
if (!(Test-Path $extractPath)) {
    New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
}

Write-Host "[2/4] Lade Stripe CLI herunter..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $stripeCliUrl -OutFile $downloadPath
    Write-Host "   OK Download erfolgreich" -ForegroundColor Green
} catch {
    Write-Host "   FEHLER beim Download: $_" -ForegroundColor Red
    exit 1
}

Write-Host "[3/4] Entpacke Stripe CLI..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force
    Write-Host "   OK Entpacken erfolgreich" -ForegroundColor Green
} catch {
    Write-Host "   FEHLER beim Entpacken: $_" -ForegroundColor Red
    exit 1
}

Write-Host "[4/4] Fuege zu PATH hinzu..." -ForegroundColor Yellow

# Pruefe ob bereits im PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$extractPath*") {
    $newPath = "$currentPath;$extractPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "   OK PATH aktualisiert" -ForegroundColor Green
    Write-Host "   WICHTIG Bitte oeffne ein NEUES PowerShell-Fenster!" -ForegroundColor Yellow
} else {
    Write-Host "   OK Bereits im PATH" -ForegroundColor Green
}

# Cleanup
Remove-Item $downloadPath -Force

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "OK Installation abgeschlossen!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Naechste Schritte:" -ForegroundColor Yellow
Write-Host "1. Oeffne ein NEUES PowerShell-Fenster" -ForegroundColor White
Write-Host "2. Teste mit: stripe --version" -ForegroundColor White
Write-Host "3. Login mit: stripe login" -ForegroundColor White
Write-Host ""
