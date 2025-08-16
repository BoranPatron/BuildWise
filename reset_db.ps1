# BuildWise Database Reset - PowerShell Script
# Erweiterte Funktionen für Windows PowerShell

param(
    [switch]$NoAdmin,
    [switch]$CleanStorage,
    [switch]$FullReset,
    [switch]$RecreateStructure,
    [switch]$Backup,
    [switch]$Quiet,
    [switch]$Help
)

function Show-Help {
    Write-Host @"

BuildWise Database Auto-Reset Tool (PowerShell)

VERWENDUNG:
    .\reset_db.ps1 [OPTIONEN]

OPTIONEN:
    -NoAdmin            Keinen Admin-User erstellen
    -CleanStorage       Storage-Verzeichnis bereinigen
    -FullReset          Vollständiger Reset (Daten + Storage)
    -RecreateStructure  Datenbank-Struktur komplett neu erstellen
    -Backup             Backup der bestehenden DB erstellen
    -Quiet              Weniger Ausgaben
    -Help               Diese Hilfe anzeigen

BEISPIELE:
    .\reset_db.ps1                      # Standard: Daten löschen, Struktur behalten
    .\reset_db.ps1 -NoAdmin             # Ohne Admin-User
    .\reset_db.ps1 -CleanStorage        # Mit Storage-Bereinigung
    .\reset_db.ps1 -FullReset           # Vollständiger Reset
    .\reset_db.ps1 -RecreateStructure   # Struktur komplett neu
    .\reset_db.ps1 -Backup              # Mit Backup

"@
}

function Test-PythonAvailable {
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Python gefunden: $pythonVersion" -ForegroundColor Green
            return $true
        }
    } catch {
        # Ignore
    }
    
    Write-Host "❌ Python nicht gefunden!" -ForegroundColor Red
    Write-Host "💡 Bitte installieren Sie Python oder fügen Sie es zum PATH hinzu" -ForegroundColor Yellow
    return $false
}

function Show-Banner {
    if (-not $Quiet) {
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host "🔄 BuildWise Database Auto-Reset (PowerShell)" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host ""
    }
}

# Hauptlogik
if ($Help) {
    Show-Help
    exit 0
}

Show-Banner

# Ins Skript-Verzeichnis wechseln
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not $Quiet) {
    Write-Host "📍 Arbeitsverzeichnis: $ScriptDir" -ForegroundColor Blue
}

# Python verfügbarkeit prüfen
if (-not (Test-PythonAvailable)) {
    exit 1
}

# Python-Skript existiert prüfen
$PythonScript = Join-Path $ScriptDir "reset_database_auto.py"
if (-not (Test-Path $PythonScript)) {
    Write-Host "❌ Python-Skript nicht gefunden: $PythonScript" -ForegroundColor Red
    exit 1
}

# Argumente für Python-Skript zusammenstellen
$PythonArgs = @()
if ($NoAdmin) { $PythonArgs += "--no-admin" }
if ($CleanStorage) { $PythonArgs += "--clean-storage" }
if ($FullReset) { $PythonArgs += "--full-reset" }
if ($RecreateStructure) { $PythonArgs += "--recreate-structure" }
if ($Backup) { $PythonArgs += "--backup" }
if ($Quiet) { $PythonArgs += "--quiet" }

# Python-Skript ausführen
try {
    if (-not $Quiet) {
        Write-Host "🚀 Starte Database Reset..." -ForegroundColor Green
        Write-Host ""
    }
    
    & python $PythonScript @PythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        if (-not $Quiet) {
            Write-Host ""
            Write-Host "✅ Database Reset erfolgreich abgeschlossen!" -ForegroundColor Green
        }
    } else {
        Write-Host "❌ Database Reset fehlgeschlagen (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "❌ Fehler beim Ausführen des Python-Skripts: $_" -ForegroundColor Red
    exit 1
}

# Pause nur wenn nicht quiet und interaktiv
if (-not $Quiet -and [Environment]::UserInteractive) {
    Write-Host ""
    Write-Host "Drücken Sie eine beliebige Taste zum Beenden..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
