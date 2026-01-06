param(
    [string]$Server = 'http://127.0.0.1:8091',
    [string]$Action = 'wait',
    [string]$ParamsJson = '{"seconds":1.0}'
)

try {
    if (-not ($ParamsJson -match '^\s*\{')) {
        Write-Error "ParamsJson must be a JSON object string."
        exit 1
    }
    $uri = "$Server/api/tasks/create"
    $paramsObj = $ParamsJson | ConvertFrom-Json
    $payloadObj = @{ type = 'rpa'; data = @{ action = $Action; params = $paramsObj } }
    $payload = $payloadObj | ConvertTo-Json -Compress
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Uri $uri -Body $payload
    $content = $resp.Content
    Write-Output $content
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}