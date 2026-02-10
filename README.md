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
