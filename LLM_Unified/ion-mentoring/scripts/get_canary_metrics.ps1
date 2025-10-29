[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$BaseUrl = 'https://ion-api-canary-x4qvsargwa-uc.a.run.app',
    [Parameter(Mandatory = $false)]
    [string]$LegacyUrl = 'https://ion-api-x4qvsargwa-uc.a.run.app'
)

$ErrorActionPreference = 'Stop'

try {
    # Ensure TLS 1.2
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    # Build URL robustly
    $base = $BaseUrl.TrimEnd('/')
    $endpoint = "$base/api/v2/canary/metrics"
    Add-Type -AssemblyName System.Web -ErrorAction SilentlyContinue | Out-Null
    $builder = New-Object System.UriBuilder($endpoint)
    if ($LegacyUrl -and $LegacyUrl.Trim().Length -gt 0) {
        $qs = [System.Web.HttpUtility]::ParseQueryString($builder.Query)
        $qs.Set('legacy_url', $LegacyUrl)
        $builder.Query = $qs.ToString()
    }
    $url = $builder.Uri.AbsoluteUri

    Write-Verbose ("[get_canary_metrics] Request URL: {0}" -f $url)

    # Validate URL
    $uri = $null
    if (-not [System.Uri]::TryCreate($url, [System.UriKind]::Absolute, [ref]$uri)) {
        throw "Built URL is invalid: $url"
    }
    $res = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 60
    $json = $res | ConvertTo-Json -Depth 12
    Write-Output $json
}
catch {
    Write-Error ("Failed to fetch canary metrics: " + $_.Exception.Message)
    exit 1
}
