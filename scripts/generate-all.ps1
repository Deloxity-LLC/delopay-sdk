param(
  [string]$SpecPath = "openapi/openapi.json",
  [switch]$SkipTypescript,
  [switch]$SkipJava,
  [switch]$SkipPython
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$spec = Join-Path $repoRoot $SpecPath
$generatedReadmePlaceholder = @(
  "Generated code is written here by ``scripts/generate-all.ps1``."
  ""
  "This placeholder exists so smoke tests can verify directory presence before first generation."
) -join [Environment]::NewLine

function Set-GeneratedReadmePlaceholder {
  param(
    [string]$OutputDirectory
  )

  Set-Content -Path (Join-Path $OutputDirectory "README.md") -Value $generatedReadmePlaceholder
}

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
  Set-GeneratedReadmePlaceholder -OutputDirectory $output

  Write-Host "Generating $Generator SDK to $OutputPath"
  & npx --no-install openapi-generator-cli generate `
    -i $spec `
    -g $Generator `
    -c $config `
    -o $output `
    --global-property apiDocs=false,modelDocs=false `
    --skip-overwrite

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
