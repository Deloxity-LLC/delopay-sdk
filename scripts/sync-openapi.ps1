param(
  [string]$Url = "http://localhost:8082/v3/api-docs",
  [string]$OutputPath = "openapi/openapi.json"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$targetPath = Join-Path $repoRoot $OutputPath
$targetDir = Split-Path $targetPath -Parent
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

Write-Host "Fetching OpenAPI from $Url"
$response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
if ($response.StatusCode -ne 200) {
  throw "OpenAPI endpoint returned HTTP $($response.StatusCode)."
}

$parsed = $response.Content | ConvertFrom-Json
if (-not $parsed.openapi) {
  throw "Invalid OpenAPI document: missing 'openapi' field."
}

$requiredPaths = @(
  "/api/payments/create",
  "/api/payments/{paymentId}",
  "/api/providers"
)

$existingPaths = @($parsed.paths.PSObject.Properties.Name)
foreach ($requiredPath in $requiredPaths) {
  if ($existingPaths -notcontains $requiredPath) {
    throw "Invalid OpenAPI document: missing required path '$requiredPath'."
  }
}

$parsed | ConvertTo-Json -Depth 100 | Set-Content -Path $targetPath -Encoding utf8
Write-Host "OpenAPI snapshot updated at $targetPath"
