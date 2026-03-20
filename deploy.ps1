<#
.SYNOPSIS
    Deploy Newsletter & MoR agents to Azure (Functions + App Service).

.DESCRIPTION
    Creates:
      - Resource Group
      - Storage Account       (for Azure Functions)
      - Azure Function App    (timer triggers: newsletter + MoR)
      - App Service Plan      (B1 Linux for Streamlit UI)
      - Web App               (Streamlit UI)
    Then deploys code and configures application settings.

.PARAMETER BaseName
    Base name for all resources (default: fabricbi-spm).

.PARAMETER Location
    Azure region (default: eastus).

.PARAMETER SkipFunctions
    Skip deploying the Azure Functions app.

.PARAMETER SkipWebApp
    Skip deploying the Streamlit web app.

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -BaseName "myproject" -Location "westus2"
    .\deploy.ps1 -SkipWebApp
#>

param(
    [string]$BaseName  = "fabricbi-spm",
    [string]$Location  = "westus2",
    [switch]$SkipFunctions,
    [switch]$SkipWebApp
)

$ErrorActionPreference = "Stop"

# -- Derived names ---------------------------------------------------
$rgName       = "rg-$BaseName"
$storageName  = ($BaseName -replace "[^a-z0-9]", "") + "st"   # max 24 chars, lowercase
if ($storageName.Length -gt 24) { $storageName = $storageName.Substring(0, 24) }
$funcName     = "func-$BaseName"
$planName     = "asp-$BaseName"
$webAppName   = "app-$BaseName"

Write-Host "`n=== Deployment Configuration ===" -ForegroundColor Cyan
Write-Host "  Resource Group   : $rgName"
Write-Host "  Storage Account  : $storageName"
Write-Host "  Function App     : $funcName"
Write-Host "  App Service Plan : $planName"
Write-Host "  Web App          : $webAppName"
Write-Host "  Location         : $Location"
Write-Host ""

# -- Load local.settings.json for app settings ----------------------
$settingsFile = Join-Path $PSScriptRoot "local.settings.json"
if (-not (Test-Path $settingsFile)) {
    Write-Error "local.settings.json not found - needed for app settings."
    exit 1
}
$settings = (Get-Content $settingsFile -Raw | ConvertFrom-Json).Values
# Build a flat hashtable, excluding Functions-runtime keys
$appSettings = @{}
$excludeKeys = @("AzureWebJobsStorage", "FUNCTIONS_WORKER_RUNTIME")
$settings.PSObject.Properties | ForEach-Object {
    if ($_.Name -notin $excludeKeys -and $_.Value) {
        $appSettings[$_.Name] = $_.Value
    }
}

# -- 1) Resource Group ----------------------------------------------
Write-Host "`n[1/7] Creating resource group '$rgName'..." -ForegroundColor Yellow
az group create --name $rgName --location $Location --output none
Write-Host "  Done." -ForegroundColor Green

# -- 2) Storage Account (for Functions) -----------------------------
if (-not $SkipFunctions) {
    Write-Host "`n[2/7] Creating storage account '$storageName'..." -ForegroundColor Yellow
    az storage account create `
        --name $storageName `
        --resource-group $rgName `
        --location $Location `
        --sku Standard_LRS `
        --output none
    Write-Host "  Done." -ForegroundColor Green
}
else {
    Write-Host "`n[2/7] Skipped (storage account)." -ForegroundColor DarkGray
}

# -- 3) Function App ------------------------------------------------
if (-not $SkipFunctions) {
    Write-Host "`n[3/7] Creating Function App '$funcName'..." -ForegroundColor Yellow
    az functionapp create `
        --name $funcName `
        --resource-group $rgName `
        --storage-account $storageName `
        --consumption-plan-location $Location `
        --runtime python `
        --runtime-version 3.11 `
        --functions-version 4 `
        --os-type Linux `
        --output none

    # Enable remote build
    az functionapp config appsettings set `
        --name $funcName `
        --resource-group $rgName `
        --settings "SCM_DO_BUILD_DURING_DEPLOYMENT=true" "ENABLE_ORYX_BUILD=true" `
        --output none

    Write-Host "  Done." -ForegroundColor Green
}
else {
    Write-Host "`n[3/7] Skipped (Function App)." -ForegroundColor DarkGray
}

# -- 4) App Service Plan --------------------------------------------
if (-not $SkipWebApp) {
    Write-Host "`n[4/7] Creating App Service Plan '$planName' (B1 Linux)..." -ForegroundColor Yellow
    az appservice plan create `
        --name $planName `
        --resource-group $rgName `
        --location $Location `
        --sku B1 `
        --is-linux `
        --output none
    Write-Host "  Done." -ForegroundColor Green
}
else {
    Write-Host "`n[4/7] Skipped (App Service Plan)." -ForegroundColor DarkGray
}

# -- 5) Web App (Streamlit) -----------------------------------------
if (-not $SkipWebApp) {
    Write-Host "`n[5/7] Creating Web App '$webAppName'..." -ForegroundColor Yellow
    az webapp create `
        --name $webAppName `
        --resource-group $rgName `
        --plan $planName `
        --runtime "PYTHON:3.11" `
        --output none

    # Set startup command and port
    $startupCmd = "python -m streamlit run ui/app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false"
    az webapp config set `
        --name $webAppName `
        --resource-group $rgName `
        --startup-file $startupCmd `
        --output none

    az webapp config appsettings set `
        --name $webAppName `
        --resource-group $rgName `
        --settings "WEBSITES_PORT=8000" "SCM_DO_BUILD_DURING_DEPLOYMENT=true" `
        --output none

    Write-Host "  Done." -ForegroundColor Green
}
else {
    Write-Host "`n[5/7] Skipped (Web App)." -ForegroundColor DarkGray
}

# -- 6) Configure App Settings --------------------------------------
Write-Host "`n[6/7] Configuring application settings..." -ForegroundColor Yellow

# Write settings to a temp JSON array that az CLI can consume
$settingsJson = $appSettings.GetEnumerator() | ForEach-Object {
    @{ name = $_.Key; value = $_.Value; slotSetting = $false }
}
$tempSettingsJson = Join-Path $env:TEMP "deploy_appsettings.json"
$settingsJson | ConvertTo-Json -Depth 3 | Set-Content $tempSettingsJson -Encoding UTF8

if (-not $SkipFunctions) {
    Write-Host "  -> Function App ($($appSettings.Count) settings)..."
    foreach ($kvp in $appSettings.GetEnumerator()) {
        az functionapp config appsettings set `
            --name $funcName `
            --resource-group $rgName `
            --settings "$($kvp.Key)=$($kvp.Value)" `
            --output none 2>$null
    }
}

if (-not $SkipWebApp) {
    Write-Host "  -> Web App ($($appSettings.Count) settings)..."
    foreach ($kvp in $appSettings.GetEnumerator()) {
        az webapp config appsettings set `
            --name $webAppName `
            --resource-group $rgName `
            --settings "$($kvp.Key)=$($kvp.Value)" `
            --output none 2>$null
    }
}
Remove-Item $tempSettingsJson -Force -ErrorAction SilentlyContinue
Write-Host "  Done." -ForegroundColor Green

# -- 7) Deploy Code -------------------------------------------------
Write-Host "`n[7/7] Deploying code..." -ForegroundColor Yellow

$projectRoot = $PSScriptRoot
$tempZipFunc = Join-Path $env:TEMP "func-deploy.zip"
$tempZipWeb  = Join-Path $env:TEMP "webapp-deploy.zip"

# Helper: create a zip from project root, excluding patterns
function New-DeployZip {
    param([string]$ZipPath, [string[]]$ExcludePatterns)

    if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

    # Gather all files, apply exclusions
    $allFiles = Get-ChildItem -Path $projectRoot -Recurse -File
    $filtered = $allFiles | Where-Object {
        $rel = $_.FullName.Substring($projectRoot.Length + 1)
        $dominated = $false
        foreach ($pat in $ExcludePatterns) {
            if ($rel -like $pat) { $dominated = $true; break }
        }
        -not $dominated
    }

    # Create zip
    $tempDir = Join-Path $env:TEMP "deploy_staging_$(Get-Random)"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    foreach ($f in $filtered) {
        $rel = $f.FullName.Substring($projectRoot.Length + 1)
        $dest = Join-Path $tempDir $rel
        $destDir = Split-Path $dest -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item $f.FullName $dest
    }

    Compress-Archive -Path (Join-Path $tempDir "*") -DestinationPath $ZipPath -Force
    Remove-Item $tempDir -Recurse -Force
    return $ZipPath
}

if (-not $SkipFunctions) {
    Write-Host "  -> Packaging Function App..."
    $funcExcludes = @(
        ".venv*", ".git*", "ui*", "tests*", "output*", "logs*",
        "config*", "*.html", "*.md", "*.cer", "*.pfx", "*.pem",
        "deploy.ps1", "setup_certificate.ps1", "spec.txt",
        "local.settings.json", ".env*", "__pycache__*",
        "Dockerfile", ".dockerignore", "startup.txt",
        "old*.html", "run_local.py"
    )
    New-DeployZip -ZipPath $tempZipFunc -ExcludePatterns $funcExcludes | Out-Null

    Write-Host "  -> Deploying to Function App '$funcName'..."
    az functionapp deployment source config-zip `
        --name $funcName `
        --resource-group $rgName `
        --src $tempZipFunc `
        --build-remote true `
        --output none

    Remove-Item $tempZipFunc -Force -ErrorAction SilentlyContinue
    Write-Host "  -> Function App deployed." -ForegroundColor Green
}

if (-not $SkipWebApp) {
    Write-Host "  -> Packaging Web App..."
    $webExcludes = @(
        ".venv*", ".git*", "tests*", "output*", "logs*",
        "*.cer", "*.pfx", "*.pem",
        "deploy.ps1", "setup_certificate.ps1", "spec.txt",
        "local.settings.json", ".env*", "__pycache__*",
        "function.json", "old*.html"
    )
    New-DeployZip -ZipPath $tempZipWeb -ExcludePatterns $webExcludes | Out-Null

    Write-Host "  -> Deploying to Web App '$webAppName'..."
    az webapp deploy `
        --name $webAppName `
        --resource-group $rgName `
        --src-path $tempZipWeb `
        --type zip `
        --output none

    Remove-Item $tempZipWeb -Force -ErrorAction SilentlyContinue
    Write-Host "  -> Web App deployed." -ForegroundColor Green
}

# -- Summary ---------------------------------------------------------
Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
if (-not $SkipFunctions) {
    Write-Host "  Function App : https://$funcName.azurewebsites.net" -ForegroundColor Green
    Write-Host "    Triggers   : newsletter_timer (9 AM UTC, 1st monthly)"
    Write-Host "                 mor_timer        (10 AM UTC, 1st monthly)"
}
if (-not $SkipWebApp) {
    Write-Host "  Streamlit UI : https://$webAppName.azurewebsites.net" -ForegroundColor Green
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Enable Managed Identity on both apps (az functionapp identity assign / az webapp identity assign)"
Write-Host "  2. Grant the managed identity access to Azure OpenAI resource"
Write-Host "  3. Store ADO PATs in Key Vault and use Key Vault references"
Write-Host "  4. Upload PFX certificate to Function App (az functionapp config ssl upload) if using Graph auth"
Write-Host "  5. Update HOT_TOPICS_FOLDER / GRAPH_CERT_PATH for cloud paths"
Write-Host ""
