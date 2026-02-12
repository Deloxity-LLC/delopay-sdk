# DeloPay SDK Monorepo

Multi-language SDK workspace for DeloPay.

## Layout

- `openapi/openapi.json`: committed OpenAPI snapshot (single source for generation)
- `config/openapi-generator/*`: generator configs per language
- `scripts/*`: sync, generate, and version tooling
- `sdks/typescript`: `@delopay/sdk`
- `sdks/java`: `io.delopay:delopay-java`
- `sdks/python`: `delopay`

## Quick Start

Prerequisites:

- Node.js 22+
- Java 17+
- Python 3.11+

1. Sync OpenAPI from backend (when backend is running):

```powershell
npm run sync:openapi
```

2. Generate language baselines:

```powershell
npm run generate
```

3. Build + test all SDKs:

```powershell
npm run build
npm run test
```

## Staging Smoke And Canary

If you want stronger confidence with real API traffic (not only mocked tests), use:

- integration smoke checks against staging/sandbox
- real special-character path checks (`paymentId`, `clientOrderId`, `providerId`)
- short post-deploy canary checks with 4xx/5xx tracking

Required:

- API key with staging/sandbox access
- reachable base URL (default: `https://sandbox-delopay.deloxity.com`)

Local usage:

```powershell
$env:DELOPAY_STAGING_API_KEY = "..."
$env:DELOPAY_BASE_URL = "https://sandbox-delopay.deloxity.com"

npm run test:smoke
npm run test:canary
```

Useful canary options:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/canary-check.ps1 `
  -Iterations 5 `
  -IntervalSeconds 15 `
  -Max4xxRate 0.00 `
  -Max5xxRate 0.00
```

GitHub Actions:

- workflow: `Staging Smoke & Canary` (`.github/workflows/staging-smoke-canary.yml`)
- required repository secret: `DELOPAY_STAGING_API_KEY`

## Versioning

- Shared version is stored in `VERSION`.
- Use `scripts/bump-version.ps1` to sync version across SDK manifests.

## OpenAPI Policy

`openapi/openapi.json` is committed by design to ensure reproducible SDK generation and deterministic CI checks.

## Publishing Targets

- npm: `@delopay/sdk`
- Maven Central: `io.delopay:delopay-java`
- PyPI: `delopay`

Required release secrets:

- `NPM_TOKEN`
- `MAVEN_CENTRAL_USERNAME`
- `MAVEN_CENTRAL_PASSWORD`
- `MAVEN_GPG_PRIVATE_KEY`
- `MAVEN_GPG_PASSPHRASE`
- `PYPI_API_TOKEN`

## License

Proprietary.
