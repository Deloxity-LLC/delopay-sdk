# Security Incident Runbook

## Severity Triage
- Sev 1: active exploitation, confirmed data exposure, credential compromise.
- Sev 2: confirmed high-impact vulnerability with feasible exploit path.
- Sev 3: suspicious activity requiring investigation, no confirmed impact yet.

## Immediate Actions
1. Contain: disable compromised keys/tokens, isolate affected services, apply traffic controls.
2. Eradicate: remove malicious artifacts, patch vulnerable components/config.
3. Recover: restore service, validate integrity, monitor for recurrence.

## Communication
- Incident commander opens incident channel and assigns owners.
- Internal updates at fixed intervals until containment.
- External communication prepared when customer/regulatory impact exists.

## Mandatory Rotation Playbooks
- API keys and webhook secrets
- session or auth secrets
- CI/CD tokens and publishing credentials

## Evidence and Forensics
- Preserve logs, CI artifacts, scanner reports, and deployment metadata.
- Record timeline: detection time, containment time, recovery time, root cause.

## Post Incident
- Blameless postmortem within 5 business days.
- Corrective actions tracked with owner and due date.
- Add detection rules and regression tests to prevent recurrence.
