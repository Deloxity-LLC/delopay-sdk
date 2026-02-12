# CI Security Gates

## Mandatory Jobs
- `sast-semgrep`: blocking
- `sast-codeql`: visibility and trend
- `sca-trivy-fs`: blocking on HIGH,CRITICAL
- `secrets-gitleaks`: blocking
- `container-iac-trivy-config`: blocking where Docker/IaC exists
- `sbom-cyclonedx`: required artifact generation

## Branch and Trigger Policy
- Run on pull requests and pushes to `dev`.
- Weekly scheduled scan and manual dispatch supported.
- Branch protection on `dev` must require the blocking security jobs.

## Blocking Thresholds
- SAST: fail on findings that Semgrep marks as errors.
- SCA: fail on HIGH/CRITICAL vulnerabilities.
- Secrets: fail on any detected secret.
- Container/IaC: fail on HIGH/CRITICAL misconfigurations.

## Exception Process
- No permanent suppressions.
- Time-boxed exception with ticket, owner, rationale, and expiry.
- Exception must be reviewed before expiry and either fixed or re-approved.

## Dependency Hygiene
- Dependabot enabled for all relevant ecosystems and directories.
- Lockfiles are mandatory where ecosystem supports them.
- CI verifies lock/manifests consistency via deterministic install (`npm ci`, equivalent for other ecosystems).
- `delopay-sdk` uses a workspace root lockfile strategy by design. The root `package-lock.json` is the source of truth for npm dependency resolution across the monorepo.

## Remediation SLA
- Critical: 24 hours
- High: 3 business days
- Medium: 14 business days
- Low: next planned maintenance window
