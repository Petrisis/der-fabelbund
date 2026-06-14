param(
    [string]$DatenbankPfad,
    [switch]$Bestätigen
)

$FehlerAktionVorher = $ErrorActionPreference
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $Projektpfad = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    if (-not $DatenbankPfad) {
        $DatenbankPfad = Join-Path $Projektpfad "fabelbund.sqlite3"
    }

    if (-not $Bestätigen) {
        Write-Host "Abbruch: Spielerreset löscht alle Spieler, Fablinge, Aufträge und Aktivitäten."
        Write-Host "Server-Konfigurationen bleiben erhalten."
        Write-Host "Aufruf: .\scripts\spieler-reset.ps1 -Bestätigen"
        exit 1
    }

    $Python = Join-Path $Projektpfad ".venv\Scripts\python.exe"
    if (-not (Test-Path $Python)) {
        $Python = "python"
    }

    $ResetProgramm = Join-Path $Projektpfad "scripts\spieler_reset.py"
    & $Python $ResetProgramm $DatenbankPfad
    exit $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $FehlerAktionVorher
}


