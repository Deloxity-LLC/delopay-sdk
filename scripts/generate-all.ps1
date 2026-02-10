param(
  [string]$SpecPath = "openapi/openapi.json",
  [switch]$SkipTypescript,
  [switch]$SkipJava,
  [switch]$SkipPython
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$spec = Join-Path $repoRoot $SpecPath
if (-not (Test-Path $spec)) {
  throw "Spec file not found: $spec"
}

$null = Get-Content -Raw $spec | ConvertFrom-Json

function Invoke-Generator {
  param(
    [string]$Generator,
    [string]$ConfigPath,
    [string]$OutputPath
  )

  $config = Join-Path $repoRoot $ConfigPath
  $output = Join-Path $repoRoot $OutputPath

  if (Test-Path $output) {
    Remove-Item -Recurse -Force $output
  }
  New-Item -ItemType Directory -Force -Path $output | Out-Null

  Write-Host "Generating $Generator SDK to $OutputPath"
  & npx --yes @openapitools/openapi-generator-cli@2.16.0 generate `
    -i $spec `
    -g $Generator `
    -c $config `
    -o $output `
    --global-property apiDocs=false,modelDocs=false

  if ($LASTEXITCODE -ne 0) {
    throw "OpenAPI generation failed for $Generator"
  }
}

if (-not $SkipTypescript) {
  Invoke-Generator -Generator "typescript-fetch" -ConfigPath "config/openapi-generator/typescript.yaml" -OutputPath "sdks/typescript/generated"
}
if (-not $SkipJava) {
  Invoke-Generator -Generator "java" -ConfigPath "config/openapi-generator/java.yaml" -OutputPath "sdks/java/generated"
}
if (-not $SkipPython) {
  Invoke-Generator -Generator "python" -ConfigPath "config/openapi-generator/python.yaml" -OutputPath "sdks/python/generated"
}

Write-Host "All requested generators completed."
