#!/usr/bin/env pwsh
# Setup SSH Key Authentication to Linux VM

param(
    [string]$LinuxHost = "binoche@192.168.119.128",
    [string]$Password = "0000"
)

$WORKSPACE_ROOT = Split-Path -Parent $PSScriptRoot

Write-Host "═══════════════════════════════════════"
Write-Host "🔐 Setting up SSH Key Authentication"
Write-Host "═══════════════════════════════════════"

# Check if SSH key exists
if (-not (Test-Path ~/.ssh/id_rsa.pub)) {
    Write-Host "📝 Generating SSH key..."
    ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\id_rsa" -N '""'
}
else {
    Write-Host "✅ SSH key already exists"
}

# Read public key
$pubKey = Get-Content ~/.ssh/id_rsa.pub

Write-Host "📤 Deploying public key to Linux VM..."
Write-Host "   (Password required: $Password)"

# Use sshpass alternative with PowerShell
$sshCommand = @"
mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$pubKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'SSH key added successfully'
"@

# Create expect-like script
$expectScript = @"
spawn ssh $LinuxHost "$sshCommand"
expect "password:"
send "$Password\r"
expect eof
"@

# For Windows, we'll use a different approach with plink or manual entry
Write-Host ""
Write-Host "⚠️  Automatic deployment requires 'sshpass' which is not available on Windows."
Write-Host "📋 Please run this command manually:"
Write-Host ""
Write-Host "ssh $LinuxHost 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo ""$pubKey"" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'"
Write-Host ""
Write-Host "Password: $Password"
Write-Host ""
Write-Host "Or copy this command to add the key:"
Write-Host "echo '$pubKey' | ssh $LinuxHost 'cat >> ~/.ssh/authorized_keys'"
