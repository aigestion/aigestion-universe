# Backup & Recovery Procedures
## aig / Daniela OS

---

## 📦 Volume Backup Strategy

### What Gets Backed Up
| Volume | Description | Retention |
|--------|-------------|-----------|
| `aig_redis` | Redis cache & session data | 3 daily |
| `aig_prometheus` | Metrics data (Prometheus) | 7 daily |
| `aig_grafana` | Grafana dashboards & config | 3 daily |
| `aig_redis_android` | Android app Redis | 3 daily |
| `aig_redis_data` | Additional Redis data | 3 daily |
| `aig_postgres` | PostgreSQL data (if used) | 7 daily |

### Backup Schedule
- **Frequency**: Daily at 03:00 AM (via Windows Task Scheduler)
- **Retention**: 3 daily, 1 weekly, 1 monthly
- **Storage**: `C:\Users\Alejandro\aig\backups\`

### Backup Script
```powershell
# scripts/deploy/backup_volumes.ps1
# Run via Windows Task Scheduler daily at 03:00

# Usage:
#   .\backup_volumes.ps1           # Run backup
#   .\backup_volumes.ps1 --list    # List available backups
#   .\backup_volumes.ps1 --dry-run # Preview what would be backed up
```

### Restore Procedure
```powershell
# 1. Stop affected services
docker compose -f config/docker-compose.yml stop <service>

# 2. Restore volume from backup
docker run --rm -v aig_redis:/dst -v C:\Users\Alejandro\aig\backups:/src alpine tar xzf /src/vol-redis-20260926_030000.tgz -C /dst

# 3. Restart service
docker compose -f config/docker-compose.yml up -d <service>
```

---

## 🔄 Disaster Recovery Runbook

### Scenario 1: Complete System Failure
**RTO**: 30 min | **RPO**: 24 hours

1. **Assess Damage**
   ```bash
   docker compose -f config/docker-compose.yml ps
   ```

2. **Restore from Latest Backup**
   ```powershell
   # Run from aig root
   .\scripts\deploy\backup_volumes.ps1 --restore --latest
   ```

3. **Verify Services**
   ```bash
   docker compose -f config/docker-compose.yml ps
   python scripts/core/ci_health_gate.py --base-url http://localhost --fail-under 95
   ```

### Scenario 2: Database Corruption
**RTO**: 1 hour | **RPO**: 24 hours

1. Stop affected services
2. Restore database volume from latest backup
3. Run migrations if needed
4. Verify data integrity

### Scenario 3: Complete Infrastructure Loss
**RTO**: 2 hours | **RPO**: 24 hours

1. Provision new host
2. Clone repo & restore `.env`
3. Run `docker compose -f config/docker-compose.yml up -d`
4. Restore volumes from backup
5. Verify all services

---

## 🔐 Secrets Rotation Schedule

| Secret | Rotation | Location | Owner |
|--------|----------|----------|-------|
| `GEMINI_API_KEY` | 90 days | `.env` | Owner |
| `OPENAI_API_KEY` | 90 days | `.env` | Owner |
| `GEMINI_API_KEY` | 90 days | `.env` | Owner |
| `JWT_SECRET` | 180 days | `.env` | Owner |
| `JWT_SECRET_KEY` | 180 days | `.env` | Owner |
| `SECRET_KEY` | 180 days | `.env` | Owner |
| `POSTGRES_PASSWORD` | 90 days | `.env` | Owner |
| `REDIS_PASSWORD` | 90 days | `.env` | Owner |
| `SUPABASE_KEY` | 90 days | `.env` | Owner |
| `STRIPE_SECRET_KEY` | 90 days | `.env` | Owner |
| `GEMINI_API_KEY` | 90 days | `.env` | Owner |
| `OPENROUTER_API_KEY` | 90 days | `.env` | Owner |
| `GEMINI_API_KEY` | 90 days | `.env` | Owner |
| `GITHUB_TOKEN` | 90 days | GitHub Secrets | Owner |
| `DOCKER_HUB_TOKEN` | 90 days | GitHub Secrets | Owner |

### Rotation Procedure
1. Generate new secret
2. Update `.env` locally
3. Update GitHub Secrets (if used in CI)
4. Restart affected services
4. Verify functionality
5. Revoke old secret (if applicable)

---

## 📋 Incident Response Runbook

### Severity Levels
| Level | Definition | Response Time | Escalation |
|-------|------------|---------------|------------|
| **SEV-1** | Total outage, data loss | 15 min | Owner immediately |
| **SEV-2** | Major feature down | 1 hour | Owner within 1h |
| **SEV-3** | Minor degradation | 4 hours | Owner within 4h |
| **SEV-4** | Minor issue | 24 hours | Next business day |

### SEV-1 Response Checklist
- [ ] Acknowledge alert within 15 min
- [ ] Assess impact & communicate status
- [ ] Identify root cause
- [ ] Implement fix or rollback
- [ ] Verify fix with health gate
- [ ] Document in incident log
- [ ] Post-mortem within 48h

### Key Dashboards
- **Grafana**: http://localhost:3000 (admin/aig2026)
- **Prometheus**: http://localhost:9090
- **Caddy**: http://localhost:2019/metrics
- **Grafana Observability**: http://localhost:3001

---

## 🔧 Maintenance Windows

| Task | Frequency | Window | Automation |
|------|-----------|--------|------------|
| Dependency updates | Weekly | Mon 06:00 | Dependabot |
| Security patches | Monthly | 1st Sun 02:00 | Manual |
| Backup verification | Weekly | Sun 04:00 | Automated |
| Log rotation | Daily | 03:00 | logrotate |
| Certificate renewal | 90 days | Auto | Let's Encrypt |

---

## 📞 Emergency Contacts

| Role | Name | Contact | Backup |
|------|------|---------|--------|
| Primary Owner | Alejandro | [REDACTED] | — |
| Infrastructure | — | — | — |
| Security | — | — | — |

---

## 📝 Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-09-26 | 1.0.0 | Initial runbook | System |
| 2026-09-26 | 1.0.1 | Added backup scripts | System |