# ============================================================
# setup_certificate.ps1
# Generates a self-signed certificate for the Newsletter Agent
# app registration (client secrets blocked by tenant policy).
#
# Usage:  .\setup_certificate.ps1
# Output: NewsletterAgent.cer  (upload to Azure Portal)
#         NewsletterAgent.pfx  (used by MSAL in code)
# ============================================================

param(
    [string]$Subject      = "CN=NewsletterAgent",
    [string]$OutDir       = $PSScriptRoot,          # same folder as this script
    [string]$PfxPassword  = "TempPass123!",
    [int]$ValidYears      = 2
)

Write-Host "`n=== Newsletter Agent - Certificate Setup ===" -ForegroundColor Cyan

# 1. Generate self-signed cert in CurrentUser\My store
Write-Host "`n[1/4] Creating self-signed certificate ($Subject)..." -ForegroundColor Yellow
$cert = New-SelfSignedCertificate `
    -Subject $Subject `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable `
    -KeySpec Signature `
    -KeyLength 2048 `
    -NotAfter (Get-Date).AddYears($ValidYears)

Write-Host "      Thumbprint : $($cert.Thumbprint)" -ForegroundColor Green
Write-Host "      Expires    : $($cert.NotAfter.ToString('yyyy-MM-dd'))" -ForegroundColor Green

# 2. Export public key (.cer) — upload this to Azure Portal
$cerPath = Join-Path $OutDir "NewsletterAgent.cer"
Write-Host "`n[2/4] Exporting public certificate (.cer)..." -ForegroundColor Yellow
Export-Certificate -Cert $cert -FilePath $cerPath | Out-Null
Write-Host "      Saved to: $cerPath" -ForegroundColor Green

# 3. Export private key (.pfx) — used by MSAL ConfidentialClientApplication
$pfxPath = Join-Path $OutDir "NewsletterAgent.pfx"
Write-Host "`n[3/4] Exporting private key (.pfx)..." -ForegroundColor Yellow
$securePwd = ConvertTo-SecureString -String $PfxPassword -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $securePwd | Out-Null
Write-Host "      Saved to: $pfxPath" -ForegroundColor Green
Write-Host "      Password : $PfxPassword" -ForegroundColor Green

# 4. Show thumbprint for local.settings.json
Write-Host "`n[4/4] Add these to local.settings.json:" -ForegroundColor Yellow
Write-Host @"

    "GRAPH_CERT_THUMBPRINT": "$($cert.Thumbprint)",
    "GRAPH_CERT_PATH": "$($pfxPath -replace '\\','\\')",
    "GRAPH_CERT_PASSWORD": "$PfxPassword"

"@ -ForegroundColor White

Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Go to Azure Portal > App registrations > aa23d311-f2dd-49b7-9e81-2bee909ed946"
Write-Host "2. Certificates & secrets > Certificates tab > Upload certificate"
Write-Host "3. Browse to: $cerPath"
Write-Host "4. API permissions > Add permission > Microsoft Graph > Application > Mail.Send"
Write-Host "5. Click 'Grant admin consent'"
Write-Host ""
