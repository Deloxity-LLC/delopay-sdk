param()

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $repoRoot
try {
  npm --workspace @delopay/sdk run build
  if ($LASTEXITCODE -ne 0) {
    throw "TypeScript build failed with exit code $LASTEXITCODE"
  }

  if ($IsWindows) {
    & "$repoRoot\sdks\java\gradlew.bat" -p "$repoRoot\sdks\java" build
  } else {
    & "$repoRoot/sdks/java/gradlew" -p "$repoRoot/sdks/java" build
  }
  if ($LASTEXITCODE -ne 0) {
    throw "Java build failed with exit code $LASTEXITCODE"
  }

  python -m pip install --upgrade pip build | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Python build dependencies installation failed with exit code $LASTEXITCODE"
  }
  python -m build "$repoRoot/sdks/python"
  if ($LASTEXITCODE -ne 0) {
    throw "Python build failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}
