param()

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $repoRoot
try {
  & "$repoRoot/scripts/generate-all.ps1"
  git diff --exit-code
  if ($LASTEXITCODE -ne 0) {
    throw "Codegen drift detected after generation."
  }
  & "$repoRoot/scripts/build-all.ps1"
  & "$repoRoot/scripts/test-all.ps1"
} finally {
  Pop-Location
}
