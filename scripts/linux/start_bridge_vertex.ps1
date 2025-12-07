# Background Self Bridge Launcher (Vertex AI Enabled)
# ====================================================

# Set Vertex AI Environment Variables
$env:VERTEX_PROJECT_ID = "naeda-genesis"
$env:VERTEX_LOCATION = "global"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\workspace\original_data\Obsidian_Vault\Nas_Obsidian_Vault\naeda-genesis-5034a5936036.json"

# Launch Bridge
Write-Host "🌉 Starting Background Self Bridge with Vertex AI..."
Write-Host "   Project: $env:VERTEX_PROJECT_ID"
Write-Host "   Location: $env:VERTEX_LOCATION"
Write-Host "   Credentials: $env:GOOGLE_APPLICATION_CREDENTIALS"
Write-Host ""

python scripts/linux/background_self_bridge.py
