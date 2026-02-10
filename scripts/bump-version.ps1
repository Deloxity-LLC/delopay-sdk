param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d+\.\d+\.\d+(-[A-Za-z0-9.-]+)?$')]
  [string]$Version
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Content -Path (Join-Path $repoRoot "VERSION") -Value "$Version`n" -Encoding utf8

function Update-JsonVersion {
  param(
    [string]$FilePath,
    [string]$Value
  )

  $obj = Get-Content -Raw $FilePath | ConvertFrom-Json
  $obj.version = $Value
  $obj | ConvertTo-Json -Depth 100 | Set-Content -Path $FilePath -Encoding utf8
}

Update-JsonVersion -FilePath (Join-Path $repoRoot "package.json") -Value $Version
Update-JsonVersion -FilePath (Join-Path $repoRoot "sdks/typescript/package.json") -Value $Version

$gradleProps = Join-Path $repoRoot "sdks/java/gradle.properties"
$gradleContent = Get-Content -Raw $gradleProps
$gradleContent = $gradleContent -replace 'VERSION_NAME=.*', "VERSION_NAME=$Version"
Set-Content -Path $gradleProps -Value $gradleContent -Encoding utf8

$pyproject = Join-Path $repoRoot "sdks/python/pyproject.toml"
$pyContent = Get-Content -Raw $pyproject
$pyContent = $pyContent -replace 'version = ".*"', "version = `"$Version`""
Set-Content -Path $pyproject -Value $pyContent -Encoding utf8

$configFiles = @(
  (Join-Path $repoRoot "config/openapi-generator/typescript.yaml")
  (Join-Path $repoRoot "config/openapi-generator/java.yaml")
  (Join-Path $repoRoot "config/openapi-generator/python.yaml")
)

foreach ($configFile in $configFiles) {
  $content = Get-Content -Raw $configFile
  $content = $content -replace '0\.1\.0', $Version
  Set-Content -Path $configFile -Value $content -Encoding utf8
}

Write-Host "Version synchronized to $Version"
