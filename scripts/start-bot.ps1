param(
    [switch]$Vordergrund,
    [double]$Zeitfaktor = 1.0
)

$FehlerAktionVorher = $ErrorActionPreference
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

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
        $AlleIds = @($Bestehend | ForEach-Object { $_.ProcessId })
        $HauptIds = @(
            $Bestehend |
                Where-Object { $AlleIds -notcontains $_.ParentProcessId } |
                ForEach-Object { $_.ProcessId }
        )
        Write-Host "Der Bot läuft bereits. Hauptprozess-ID(s): $($HauptIds -join ', ')"
        if ($AlleIds.Count -gt $HauptIds.Count) {
            $KindIds = @($AlleIds | Where-Object { $HauptIds -notcontains $_ })
            Write-Host "Zugehörige Kindprozess-ID(s): $($KindIds -join ', ')"
        }
        Write-Host "Nutze .\scripts\stop-bot.ps1, wenn du ihn neu starten möchtest."
        exit 0
    }

    if ($Vordergrund) {
        Set-Location $Projektpfad
        $env:FABELBUND_BEFEHLE_SYNCHRONISIEREN = "1"
        $env:FABELBUND_ZEITFAKTOR = [string]$Zeitfaktor
        & $Python -m fabelbund_bot.bot
        exit $LASTEXITCODE
    }

    $AusgabeLog = Join-Path $Projektpfad "bot.log"
    $FehlerLog = Join-Path $Projektpfad "bot.err"
    $env:FABELBUND_BEFEHLE_SYNCHRONISIEREN = "1"
    $env:FABELBUND_ZEITFAKTOR = [string]$Zeitfaktor
    Start-Process -FilePath $Python `
        -ArgumentList "-m fabelbund_bot.bot" `
        -WorkingDirectory $Projektpfad `
        -WindowStyle Hidden `
        -RedirectStandardOutput $AusgabeLog `
        -RedirectStandardError $FehlerLog

    Write-Host "Bot gestartet: Zeitfaktor $($Zeitfaktor)x. Logs: bot.log, bot.err"
}
finally {
    $ErrorActionPreference = $FehlerAktionVorher
}
