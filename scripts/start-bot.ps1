param(
    [switch]$Vordergrund
)

$FehlerAktionVorher = $ErrorActionPreference
$ErrorActionPreference = "Stop"

try {
    $Projektpfad = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $Python = Join-Path $Projektpfad ".venv\Scripts\python.exe"
    if (-not (Test-Path $Python)) {
        $Python = "python"
    }

    $Bestehend = Get-CimInstance Win32_Process -Filter "name = 'python.exe' or name = 'pythonw.exe'" |
        Where-Object {
            $_.CommandLine -like "*fabelbund_bot.bot*"
        }

    if ($Bestehend) {
        $Ids = ($Bestehend | ForEach-Object { $_.ProcessId }) -join ", "
        Write-Host "Der Bot läuft bereits. Prozess-ID(s): $Ids"
        exit 0
    }

    if ($Vordergrund) {
        Set-Location $Projektpfad
        $env:FABELBUND_BEFEHLE_SYNCHRONISIEREN = "1"
        $env:FABELBUND_ZEITFAKTOR = "5.0"
        & $Python -m fabelbund_bot.bot
        exit $LASTEXITCODE
    }

    $AusgabeLog = Join-Path $Projektpfad "bot.log"
    $FehlerLog = Join-Path $Projektpfad "bot.err"
    $env:FABELBUND_BEFEHLE_SYNCHRONISIEREN = "1"
    $env:FABELBUND_ZEITFAKTOR = "5.0"
    Start-Process -FilePath $Python `
        -ArgumentList "-m fabelbund_bot.bot" `
        -WorkingDirectory $Projektpfad `
        -WindowStyle Hidden `
        -RedirectStandardOutput $AusgabeLog `
        -RedirectStandardError $FehlerLog

    Write-Host "Bot gestartet: Testserver, Zeitfaktor 5.0x. Logs: bot.log, bot.err"
}
finally {
    $ErrorActionPreference = $FehlerAktionVorher
}
