$FehlerAktionVorher = $ErrorActionPreference
$ErrorActionPreference = "Stop"

try {
    $Projektpfad = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $Prozesse = Get-CimInstance Win32_Process -Filter "name = 'python.exe' or name = 'pythonw.exe'" |
        Where-Object {
            $_.CommandLine -like "*fabelbund_bot.bot*"
        }

    if (-not $Prozesse) {
        Write-Host "Kein laufender Fabelbund-Bot gefunden."
        exit 0
    }

    $Ids = $Prozesse | ForEach-Object { $_.ProcessId }
    Stop-Process -Id $Ids
    Write-Host "Bot beendet. Prozess-ID(s): $($Ids -join ', ')"
}
finally {
    $ErrorActionPreference = $FehlerAktionVorher
}
