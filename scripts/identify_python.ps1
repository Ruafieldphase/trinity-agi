# Identify what each Python process is running
Write-Host "=== Identifying Python Processes ===" -ForegroundColor Cyan

Get-Process -Name "python*" -ErrorAction SilentlyContinue | ForEach-Object {
    $proc = $_
    try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        Write-Host "`nPID: $($proc.Id) | Name: $($proc.ProcessName)"
        Write-Host "  Started: $($proc.StartTime)"
        Write-Host "  Command: $cmd"
    } catch {
        Write-Host "`nPID: $($proc.Id) | Name: $($proc.ProcessName)"
        Write-Host "  (Unable to get command line)"
    }
}