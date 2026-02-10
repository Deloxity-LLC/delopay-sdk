param()

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $repoRoot
try {
  npm --workspace @delopay/sdk run test
  if ($LASTEXITCODE -ne 0) {
    throw "TypeScript tests failed with exit code $LASTEXITCODE"
  }

  if ($IsWindows) {
    & "$repoRoot\sdks\java\gradlew.bat" -p "$repoRoot\sdks\java" test
  } else {
    & "$repoRoot/sdks/java/gradlew" -p "$repoRoot/sdks/java" test
  }
  if ($LASTEXITCODE -ne 0) {
    throw "Java tests failed with exit code $LASTEXITCODE"
  }

  python -m pip install --upgrade pip | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Python pip upgrade failed with exit code $LASTEXITCODE"
  }
  python -m pip install -e "$repoRoot/sdks/python[dev]" | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Python dependency installation failed with exit code $LASTEXITCODE"
  }
  python -m pytest "$repoRoot/sdks/python/tests"
  if ($LASTEXITCODE -ne 0) {
    throw "Python tests failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}
