# Security Baseline Standard

## Scope and Standard
- Mandatory baseline: OWASP ASVS Level 2
- Mandatory risk model: OWASP Top 10
- Applies to application code, CI/CD, dependencies, containers, infra config, and release artifacts.

## Minimum Technical Controls
- Authentication: strong credential handling, session security, brute-force protection.
- Authorization: backend-enforced RBAC, deny-by-default for protected operations.
- Input handling: validation, output encoding where relevant, safe defaults.
- Transport: TLS 1.2+ (prefer 1.3), HSTS at edge and/or app where applicable.
- Secrets: no committed secrets, mandatory secret scanning in CI.
- Supply chain: dependency scanning, SBOM generation, version pinning/lockfile usage.
- Logging and monitoring: security event logs, alert thresholds, incident response process.

## Severity and Gate Policy
- High/Critical findings are blocking in CI for SAST/SCA/Secrets/Container-IaC scans.
- Medium/Low findings are tracked with remediation SLAs.
- Temporary exceptions require ticket reference, owner, expiry date, and compensating controls.

## ASVS L2 Focus Areas
- V1 Architecture and Design: documented trust boundaries and secure defaults.
- V2 Authentication: secure session lifecycle, rotation, timeout, brute-force controls.
- V3 Session Management: secure cookies/token handling and CSRF defense where cookie auth is used.
- V4 Access Control: server-side authorization enforcement.
- V5 Validation/Sanitization and V8 Data Protection controls.
- V9 Communications: TLS and security headers.
- V14 Configuration and V14.2 dependency hygiene in CI/CD.
