# CMS Automation - Security Action Plan

**Version**: 1.0.0
**Created**: 2025-10-26
**Owner**: Security Team
**Status**: In Progress

---

## Purpose

This action plan addresses the security findings from the automated security scans and outlines the steps needed to achieve production-ready security posture for the CMS Automation system.

---

## Priority Matrix

| Priority | Timeline | Blocking Production? |
|----------|----------|---------------------|
| **P0 - Critical** | This week | YES |
| **P1 - High** | Before production | YES |
| **P2 - Medium** | Within 1 month | NO |
| **P3 - Low** | Ongoing | NO |

---

## P0 - Critical Actions (This Week)

### 1. Python Dependency Vulnerability Review

**Finding**: Safety scan detected 9 vulnerabilities in Python dependencies

**Action Items**:
- [ ] Register for Safety CLI account (free tier) OR install pip-audit
- [ ] Run detailed vulnerability scan to identify specific CVEs
- [ ] Categorize vulnerabilities by severity (Critical/High/Medium/Low)
- [ ] Update affected packages to secure versions
- [ ] Test application after updates

**Commands**:
```bash
# Option 1: Use Safety (requires registration)
cd backend
poetry run safety auth login
poetry run safety scan --output screen

# Option 2: Use pip-audit (alternative)
pip install pip-audit
cd backend
poetry export -f requirements.txt | pip-audit -r /dev/stdin

# Option 3: Manual check
poetry show --outdated
```

**Owner**: Backend Team
**Due Date**: 2025-10-29
**Success Criteria**: All critical and high severity vulnerabilities resolved

---

### 2. Secret Scanning

**Finding**: No secret scanning has been performed on repository

**Action Items**:
- [ ] Install gitleaks
- [ ] Scan entire git history for leaked secrets
- [ ] Rotate any found credentials immediately
- [ ] Set up pre-commit hook to prevent future leaks

**Commands**:
```bash
# Install gitleaks
brew install gitleaks

# Scan entire repository
gitleaks detect --source . --report-path gitleaks-report.json --verbose

# If secrets found:
# 1. Rotate credentials immediately
# 2. Remove from git history using BFG Repo-Cleaner
# 3. Force push to remote (coordinate with team)

# Set up pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks protect --staged --verbose
EOF
chmod +x .git/hooks/pre-commit
```

**Owner**: DevOps Team
**Due Date**: 2025-10-28
**Success Criteria**: Clean gitleaks scan + pre-commit hook configured

---

### 3. Container Image Scanning

**Finding**: Docker images have not been scanned for vulnerabilities

**Action Items**:
- [ ] Install Trivy scanner
- [ ] Scan all production Docker images
- [ ] Fix HIGH and CRITICAL vulnerabilities
- [ ] Integrate into CI/CD pipeline

**Commands**:
```bash
# Install Trivy
brew install trivy

# Scan backend image
docker build -t cms-automation-backend:test -f backend/Dockerfile.prod backend/
trivy image --severity HIGH,CRITICAL cms-automation-backend:test

# Scan nginx image (if custom)
trivy image --severity HIGH,CRITICAL nginx:latest

# Generate detailed report
trivy image --format json --output trivy-report.json cms-automation-backend:test
```

**Owner**: DevOps Team
**Due Date**: 2025-10-30
**Success Criteria**: Zero HIGH/CRITICAL vulnerabilities in production images

---

## P1 - High Priority (Before Production)

### 4. Authentication System Implementation

**Finding**: No authentication currently implemented (per SECURITY_AUDIT.md)

**Action Items**:
- [ ] Design authentication architecture
  - JWT tokens with 15-minute expiration
  - Refresh tokens with 7-day expiration
  - Token rotation on refresh
- [ ] Implement API key authentication for service-to-service
- [ ] Add authentication middleware to FastAPI
- [ ] Implement rate limiting per API key/user
- [ ] Create admin vs user roles

**Technical Spec**:
```python
# backend/src/api/middleware/auth.py (enhance existing)

from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Verify expiration, user_id, permissions
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Owner**: Backend Team
**Due Date**: 2025-11-05
**Success Criteria**:
- All endpoints protected with JWT authentication
- Rate limiting active (100 req/min per user)
- RBAC implemented

---

### 5. Secrets Management

**Finding**: Secrets currently in .env files (local only)

**Action Items**:
- [ ] Choose secrets management solution (AWS Secrets Manager or HashiCorp Vault)
- [ ] Migrate all production secrets:
  - Database credentials
  - Redis password
  - Anthropic API key
  - CMS credentials
  - JWT signing keys
- [ ] Update deployment scripts to fetch secrets at runtime
- [ ] Document secret rotation procedure
- [ ] Set up 90-day rotation schedule

**Implementation (AWS Secrets Manager)**:
```python
# backend/src/config/secrets.py

import boto3
import json
from functools import lru_cache

@lru_cache
def get_secret(secret_name: str) -> dict:
    """Fetch secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage in settings.py
secrets = get_secret('cms-automation/production')
DATABASE_URL = secrets['database_url']
ANTHROPIC_API_KEY = secrets['anthropic_api_key']
```

**Owner**: DevOps + Backend Team
**Due Date**: 2025-11-08
**Success Criteria**: Zero secrets in environment variables or config files

---

### 6. Database Encryption

**Finding**: PostgreSQL TDE not configured

**Action Items**:
- [ ] Enable PostgreSQL Transparent Data Encryption (TDE)
- [ ] Configure SSL/TLS for database connections
- [ ] Enable encrypted backups
- [ ] Document encryption key management

**Configuration**:
```yaml
# docker-compose.prod.yml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_INITDB_ARGS: "--data-checksums"
  command: |
    postgres
    -c ssl=on
    -c ssl_cert_file=/etc/ssl/certs/server.crt
    -c ssl_key_file=/etc/ssl/private/server.key
  volumes:
    - ./certs/server.crt:/etc/ssl/certs/server.crt:ro
    - ./certs/server.key:/etc/ssl/private/server.key:ro
```

**Owner**: DBA + DevOps Team
**Due Date**: 2025-11-10
**Success Criteria**:
- Data-at-rest encrypted
- SSL connections enforced
- Encrypted backups verified

---

### 7. Security Monitoring Enhancement

**Finding**: Basic monitoring exists but needs security-specific enhancements

**Action Items**:
- [ ] Add security event logging
  - Failed authentication attempts
  - Permission denied events
  - Unusual API usage patterns
  - Admin action audit trail
- [ ] Configure security-specific alerts
  - Multiple failed login attempts (5+ in 1 min)
  - Privilege escalation attempts
  - Suspicious file access patterns
- [ ] Set up centralized log aggregation
- [ ] Enable log integrity protection

**Prometheus Alert Rules**:
```yaml
# monitoring/security-alerts.yml
groups:
  - name: security_alerts
    rules:
      - alert: BruteForceAttempt
        expr: rate(http_requests_total{status="401"}[1m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Potential brute force attack detected"
          description: "{{ $value }} failed auth attempts per second"

      - alert: UnauthorizedAccess
        expr: rate(http_requests_total{status="403"}[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of unauthorized access attempts"
```

**Owner**: Backend + Monitoring Team
**Due Date**: 2025-11-12
**Success Criteria**: Security alerts firing correctly in test scenarios

---

## P2 - Medium Priority (Within 1 Month)

### 8. Penetration Testing

**Action Items**:
- [ ] Hire third-party security firm
- [ ] Define scope (API endpoints, authentication, authorization)
- [ ] Schedule testing window
- [ ] Remediate findings
- [ ] Re-test after fixes

**Budget**: $5,000 - $15,000
**Owner**: CTO + Security Team
**Due Date**: 2025-11-30

---

### 9. GDPR Compliance Review

**Action Items**:
- [ ] Data mapping - what personal data is collected?
- [ ] Implement consent management
- [ ] Add "Right to Erasure" endpoint
- [ ] Create data portability export
- [ ] Publish privacy policy
- [ ] Document data retention schedule

**Owner**: Legal + Product Team
**Due Date**: 2025-11-30

---

### 10. Automated Security Testing in CI/CD

**Action Items**:
- [ ] Add Bandit to CI pipeline (fail on MEDIUM+)
- [ ] Add npm audit to CI pipeline (fail on HIGH+)
- [ ] Add Trivy container scanning
- [ ] Add gitleaks secret scanning
- [ ] Configure GitHub Dependabot
- [ ] Set up automated dependency updates (with tests)

**GitHub Actions Workflow**:
```yaml
# .github/workflows/security.yml
name: Security Checks

on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Secret Scanning
        uses: gitleaks/gitleaks-action@v2

      - name: Python Security (Bandit)
        run: |
          pip install bandit
          bandit -r backend/src/ -ll -f json
        continue-on-error: false

      - name: Dependency Scanning (Safety)
        run: |
          pip install safety
          safety check --json
        env:
          SAFETY_API_KEY: ${{ secrets.SAFETY_API_KEY }}

      - name: Container Scanning (Trivy)
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'cms-automation-backend:${{ github.sha }}'
          severity: 'CRITICAL,HIGH'

      - name: Frontend Audit
        run: |
          cd frontend
          npm audit --audit-level=high
```

**Owner**: DevOps Team
**Due Date**: 2025-11-25

---

## P3 - Low Priority (Ongoing)

### 11. Security Training

**Action Items**:
- [ ] OWASP Top 10 training for developers
- [ ] Secure coding practices workshop
- [ ] Incident response simulation
- [ ] Quarterly security review meetings

**Owner**: HR + Security Team
**Cadence**: Quarterly

---

### 12. Bug Bounty Program

**Action Items**:
- [ ] Set up HackerOne or BugCrowd account
- [ ] Define scope and rules
- [ ] Set bounty amounts
- [ ] Launch private program initially

**Owner**: Security + Product Team
**Timeline**: Q2 2026

---

## Progress Tracking

### Week 1 (2025-10-26 to 2025-11-01)
- [x] Security scan completed
- [x] Security findings documented
- [ ] P0-1: Dependency vulnerability review
- [ ] P0-2: Secret scanning
- [ ] P0-3: Container scanning

### Week 2 (2025-11-02 to 2025-11-08)
- [ ] P1-4: Authentication implementation (started)
- [ ] P1-5: Secrets management migration

### Week 3 (2025-11-09 to 2025-11-15)
- [ ] P1-6: Database encryption
- [ ] P1-7: Security monitoring

### Week 4 (2025-11-16 to 2025-11-22)
- [ ] P1 items completion
- [ ] Production readiness review

---

## Success Metrics

### Before Production Deployment

- [ ] **Zero** HIGH or CRITICAL vulnerabilities in dependencies
- [ ] **Zero** secrets in source code or environment files
- [ ] **Zero** HIGH or CRITICAL container vulnerabilities
- [ ] **100%** of API endpoints protected with authentication
- [ ] **All** production secrets in secrets manager
- [ ] Database encryption enabled
- [ ] Security monitoring and alerting active
- [ ] Penetration test completed with findings remediated

### Ongoing Metrics

- **Mean Time to Patch (MTTP)**: < 7 days for HIGH vulnerabilities
- **Security Scan Coverage**: 100% of code scanned weekly
- **Failed Login Rate**: < 1% of total requests
- **Security Alert Response Time**: < 15 minutes for CRITICAL

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Delayed dependency fixes block deployment | Medium | High | Start immediately, allocate dedicated resources |
| Secrets found in git history | Low | Critical | Run gitleaks scan ASAP, rotate if found |
| Container vulnerabilities require base image changes | Medium | Medium | Use minimal base images, scan early |
| Authentication implementation delays | Medium | Critical | Assign senior developer, consider auth library |
| Penetration test finds critical issues | Medium | High | Schedule with buffer time for remediation |

---

## Communication Plan

### Daily Standup
- Security action plan progress
- Blockers and dependencies
- Risk updates

### Weekly Security Review
- **When**: Every Friday 2pm
- **Who**: Security Team, Tech Lead, DevOps Lead
- **Agenda**:
  - Progress on P0/P1 items
  - New vulnerabilities discovered
  - Decision needed on acceptable risks

### Production Readiness Gate
- **When**: 2025-11-20
- **Who**: CTO, Security Lead, DevOps Lead, Product Lead
- **Criteria**: All P0 and P1 items completed
- **Outcome**: Go/No-Go decision for production

---

## Escalation Path

1. **Blocker on P0 item**: Immediately escalate to Tech Lead
2. **Critical vulnerability discovered**: Alert Security Lead within 1 hour
3. **Timeline at risk**: Escalate to CTO within 24 hours
4. **Production deployment decision**: CTO + Security Lead sign-off required

---

## Appendix: Quick Reference

### Useful Commands

```bash
# Security scans
poetry run bandit -r src/
poetry run safety scan
npm audit --production
trivy image <image-name>
gitleaks detect

# Dependency updates
poetry update
npm update
poetry show --outdated

# Container operations
docker scan <image-name>
docker build --no-cache -t <image> .
```

### Key Contacts

- **Security Lead**: TBD
- **CTO**: TBD
- **DevOps Lead**: TBD
- **Backend Lead**: TBD

---

**Document Owner**: Security Team
**Last Updated**: 2025-10-26
**Next Review**: Weekly until production deployment

---

**End of Action Plan**
