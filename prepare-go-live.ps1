param(
  [string]$DbPath = "",
  [switch]$Backup = $false,
  [string]$Confirm = "",
  [ValidateSet("KeepSchema","DropSchema","TruncateFile")][string]$ResetMode = "KeepSchema"
)

if (($env:BW_GOLIVE_CONFIRM -ne "DELETE") -and ($Confirm -ne "DELETE")) {
  Write-Error "Abbruch: Setze -Confirm DELETE oder Umgebungsvariable BW_GOLIVE_CONFIRM=DELETE."; exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir "..") 2>$null

function Find-Db {
  param([string]$start)
  $candidates = @(
    # Priorität: Verzeichnis des Skripts
    (Join-Path $ScriptDir "buildwise.db"),
    (Join-Path $ScriptDir "var\buildwise.db"),
    # Repo-üblich: BuildWise unter RepoRoot
    (Join-Path $RepoRoot "BuildWise\buildwise.db"),
    (Join-Path $RepoRoot "BuildWise\var\buildwise.db"),
    # Startpfad als Fallback
    (Join-Path $start "buildwise.db"),
    (Join-Path $start "var\buildwise.db")
  )
  foreach ($c in $candidates) { if (Test-Path $c) { return (Resolve-Path $c).Path } }
  # Eingeschränkte rekursive Suche: erst unter ScriptDir, dann BuildWise im Repo, dann Startpfad
  $searchRoots = @($ScriptDir, (Join-Path $RepoRoot 'BuildWise'), $start) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique
  foreach ($root in $searchRoots) {
    $found = Get-ChildItem -Path $root -Recurse -File -Filter "buildwise.db" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "97_Backup|Backup|_bak|\\backup\\" } | Select-Object -First 1
    if ($found) { return $found.FullName }
  }
  return $null
}

if ([string]::IsNullOrWhiteSpace($DbPath)) {
  $startPath = if ($RepoRoot) { $RepoRoot } else { (Get-Location).Path }
  $DbPath = Find-Db $startPath
}

if (-not $DbPath) { Write-Error "Keine buildwise.db gefunden. Übergib -DbPath oder lege die Datei ins Repo."; exit 2 }
if (-not (Test-Path $DbPath)) { Write-Error "Datei nicht gefunden: $DbPath"; exit 3 }

Write-Host "Ziel-DB: $DbPath" -ForegroundColor Yellow

if ($Backup) {
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"; $bak = Join-Path (Split-Path $DbPath -Parent) ("buildwise.backup.$stamp.db")
  try { Copy-Item -Path $DbPath -Destination $bak -Force; Write-Host "Backup erstellt: $bak" -ForegroundColor Green } catch { Write-Warning "Backup fehlgeschlagen: $($_.Exception.Message)" }
}

try { $fs = [System.IO.File]::Open($DbPath, 'Open', 'ReadWrite', 'None'); $fs.Close() } catch { Write-Error "DB in Benutzung (Lock). Beende Backend/Server und versuche erneut."; exit 4 }

function Invoke-DbResetWithPython {
  param([string]$dbPath, [string]$mode)
  $py = Get-Command python -ErrorAction SilentlyContinue
  if (-not $py) { return $false }
  $temp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "bw_reset_db.py")
  $code = @"
import sqlite3
import sys

db = r'''$DbPath'''
mode = r'''$ResetMode'''

con = sqlite3.connect(db)
con.isolation_level = None
cur = con.cursor()
try:
    cur.execute('PRAGMA foreign_keys=OFF;')
    if mode == 'KeepSchema':
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        tables = [t for t in tables if t != 'alembic_version']
        for t in tables:
            cur.execute(f'DELETE FROM "{t}";')
        try:
            cur.execute('DELETE FROM sqlite_sequence;')
        except Exception:
            pass
    elif mode == 'DropSchema':
        views = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='view'")]
        for v in views:
            cur.execute(f'DROP VIEW IF EXISTS "{v}";')
        trigs = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='trigger'")]
        for tr in trigs:
            cur.execute(f'DROP TRIGGER IF EXISTS "{tr}";')
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for t in tables:
            cur.execute(f'DROP TABLE IF EXISTS "{t}";')
    else:
        sys.exit(2)
    con.commit()
    cur.execute('VACUUM;')
    con.commit()
finally:
    con.close()
"@
  Set-Content -Path $temp -Value $code -Encoding UTF8
  try {
    & $py.Source $temp | Out-Null
    Remove-Item $temp -Force -ErrorAction SilentlyContinue
    return $true
  } catch {
    Remove-Item $temp -Force -ErrorAction SilentlyContinue
    return $false
  }
}

function Invoke-DbResetWithSqlite3 {
  param([string]$dbPath, [string]$mode)
  $cli = Get-Command sqlite3 -ErrorAction SilentlyContinue
  if (-not $cli) { return $false }
  if ($mode -eq 'KeepSchema') {
    $stmts = & $cli.Source $dbPath "SELECT 'DELETE FROM ""' || name || '"";' FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name <> 'alembic_version';"
    $sql = @(
      'PRAGMA foreign_keys=OFF;',
      $stmts,
      'DELETE FROM sqlite_sequence;',
      'VACUUM;',
      'PRAGMA foreign_keys=ON;'
    ) -join "`n"
  } elseif ($mode -eq 'DropSchema') {
    $dropViews = & $cli.Source $dbPath "SELECT 'DROP VIEW IF EXISTS ""' || name || '"";' FROM sqlite_master WHERE type='view';"
    $dropTriggers = & $cli.Source $dbPath "SELECT 'DROP TRIGGER IF EXISTS ""' || name || '"";' FROM sqlite_master WHERE type='trigger';"
    $dropTables = & $cli.Source $dbPath "SELECT 'DROP TABLE IF EXISTS ""' || name || '"";' FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    $sql = @(
      'PRAGMA foreign_keys=OFF;',
      $dropViews,
      $dropTriggers,
      $dropTables,
      'VACUUM;',
      'PRAGMA foreign_keys=ON;'
    ) -join "`n"
  } else {
    return $false
  }
  $tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "bw_reset_db.sql")
  Set-Content -Path $tmp -Value $sql -Encoding UTF8
  try {
    & $cli.Source $dbPath ".read $tmp" | Out-Null
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    return $true
  } catch {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    return $false
  }
}

switch ($ResetMode) {
  'KeepSchema' {
    if (Invoke-DbResetWithPython -dbPath $DbPath -mode 'KeepSchema') {
      Write-Host "Alle Daten entfernt, Schema behalten (KeepSchema)." -ForegroundColor Green
      break
    }
    if (Invoke-DbResetWithSqlite3 -dbPath $DbPath -mode 'KeepSchema') {
      Write-Host "Alle Daten entfernt, Schema behalten (KeepSchema, via sqlite3)." -ForegroundColor Green
      break
    }
    # Fallback: Datei leeren
    $fs = [System.IO.File]::Open($DbPath, 'Open', 'ReadWrite', 'None'); $fs.SetLength(0); $fs.Close()
    Write-Warning "Fallback verwendet: Datei auf 0 Bytes gesetzt (Truncate). SQLite initialisiert beim nächsten Schreiben neu."
  }
  'DropSchema' {
    if (Invoke-DbResetWithPython -dbPath $DbPath -mode 'DropSchema') {
      Write-Host "Komplettes Schema entfernt (DropSchema)." -ForegroundColor Green
      break
    }
    if (Invoke-DbResetWithSqlite3 -dbPath $DbPath -mode 'DropSchema') {
      Write-Host "Komplettes Schema entfernt (DropSchema, via sqlite3)." -ForegroundColor Green
      break
    }
    # Fallback: Datei leeren
    $fs = [System.IO.File]::Open($DbPath, 'Open', 'ReadWrite', 'None'); $fs.SetLength(0); $fs.Close()
    Write-Warning "Fallback verwendet: Datei auf 0 Bytes gesetzt (Truncate)."
  }
  'TruncateFile' {
    $fs = [System.IO.File]::Open($DbPath, 'Open', 'ReadWrite', 'None'); $fs.SetLength(0); $fs.Close()
    Write-Host "Datei auf 0 Bytes gesetzt (TruncateFile)." -ForegroundColor Yellow
  }
}

Write-Host "Hinweis: Falls Schema entfernt oder Datei geleert wurde, beim nächsten Start/Migration neu aufbauen (z. B. alembic upgrade head oder App-Start)." -ForegroundColor Cyan
