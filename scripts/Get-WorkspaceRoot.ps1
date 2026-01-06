function Get-WorkspaceRoot {
    $envRoot = $env:AGI_WORKSPACE_ROOT
    if (-not $envRoot) {
        $envRoot = $env:WORKSPACE_ROOT
    }
    if ($envRoot) {
        try {
            return (Resolve-Path -LiteralPath $envRoot -ErrorAction Stop).Path
        }
        catch {
        }
    }

    $scriptRoot = $PSScriptRoot
    if (-not $scriptRoot) {
        $scriptRoot = (Get-Location).Path
    }

    $root = Split-Path -Parent $scriptRoot
    return (Resolve-Path -LiteralPath $root -ErrorAction Stop).Path
}