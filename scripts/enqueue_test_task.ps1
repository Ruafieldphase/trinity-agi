param(
    [string]$Server = 'http://127.0.0.1:8091',
    [string]$Type = 'ping',
    [string]$DataJson = '{}'
)

try {
    if (-not ($DataJson -match '^\s*\{')) {
        Write-Error "DataJson must be a JSON object string."
        exit 1
    }
    $uri = "$Server/api/tasks/create"
    $dataObj = $DataJson | ConvertFrom-Json
    $payload = @{ type = $Type; data = $dataObj } | ConvertTo-Json -Compress
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Uri $uri -Body $payload
    $content = $resp.Content
    Write-Output $content
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
