$FehlerAktionVorher = $ErrorActionPreference
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $Prozesse = Get-CimInstance Win32_Process -Filter "name = 'python.exe' or name = 'pythonw.exe'" |
        Where-Object {
            $_.CommandLine -like "*fabelbund_bot.bot*"
        }

    if (-not $Prozesse) {
        Write-Host "Kein laufender Fabelbund-Bot gefunden."
        exit 0
    }

    $AlleIds = @($Prozesse | ForEach-Object { $_.ProcessId })
    $HauptIds = @(
        $Prozesse |
            Where-Object { $AlleIds -notcontains $_.ParentProcessId } |
            ForEach-Object { $_.ProcessId }
    )
    $Ids = $AlleIds
    Stop-Process -Id $Ids
    Write-Host "Bot beendet. Hauptprozess-ID(s): $($HauptIds -join ', ')"
    if ($AlleIds.Count -gt $HauptIds.Count) {
        $KindIds = @($AlleIds | Where-Object { $HauptIds -notcontains $_ })
        Write-Host "Zugehörige Kindprozess-ID(s): $($KindIds -join ', ')"
    }
}
finally {
    $ErrorActionPreference = $FehlerAktionVorher
}
