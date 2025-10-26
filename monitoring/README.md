# CMS Automation - Monitoring & Alerting

**Version**: 1.0.0
**Last Updated**: 2025-10-26

Complete monitoring stack for CMS Automation using Prometheus, Grafana, and Alertmanager.

---

## Overview

This monitoring solution provides:

- **Real-time metrics** from all system components
- **Automated alerts** for critical issues
- **Visual dashboards** for performance tracking
- **SLA compliance monitoring**
- **Cost tracking and budgeting**

---

## Quick Start

### 1. Start Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Alertmanager**: http://localhost:9093

### 3. Configure Alerts

Edit `monitoring/alertmanager.yml` and set your notification channels:

```yaml
global:
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'alerts@your-domain.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
```

---

## Architecture

### Components

**Prometheus** (Port 9090)
- Metrics collection and storage
- Alert rule evaluation
- 30-day data retention

**Grafana** (Port 3001)
- Visual dashboards
- Multi-datasource support
- Custom alerting

**Alertmanager** (Port 9093)
- Alert routing and grouping
- Email, Slack, PagerDuty integration
- Alert silencing and inhibition

### Exporters

| Exporter | Port | Metrics |
|----------|------|---------|
| postgres_exporter | 9187 | Database metrics |
| redis_exporter | 9121 | Cache metrics |
| node_exporter | 9100 | System metrics |
| nginx_exporter | 9113 | Proxy metrics |
| celery_exporter | 9540 | Worker metrics |

---

## Metrics

### Application Metrics

**API Metrics**:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `http_requests_in_progress` - Active requests

**Article Generation**:
- `article_generation_total` - Total generations
- `article_generation_success_total` - Successful generations
- `article_generation_duration_seconds` - Generation time
- `article_generation_cost_total` - API costs

**Celery Metrics**:
- `celery_workers_online` - Active workers
- `celery_queue_length` - Queue depth
- `celery_task_total` - Total tasks
- `celery_task_failed_total` - Failed tasks

### Infrastructure Metrics

**Database**:
- `pg_stat_activity_count` - Active connections
- `pg_stat_database_*` - Database statistics
- `pg_stat_activity_max_tx_duration` - Long queries

**Redis**:
- `redis_memory_used_bytes` - Memory usage
- `redis_connected_clients` - Client connections
- `redis_commands_processed_total` - Command count

**System**:
- `node_cpu_seconds_total` - CPU usage
- `node_memory_*` - Memory metrics
- `node_filesystem_*` - Disk metrics
- `node_network_*` - Network metrics

---

## Alerts

### Critical Alerts (Immediate Response)

1. **APIDown**: Backend API unreachable
2. **DatabaseDown**: PostgreSQL unavailable
3. **RedisDown**: Redis unavailable
4. **SLAViolation**: 95th percentile > 300s
5. **LowSuccessRate**: Success rate < 95%
6. **DiskSpaceLow**: < 10% disk space

### Warning Alerts (Monitor & Plan)

1. **HighAPIErrorRate**: Error rate > 5%
2. **APIResponseTimeHigh**: p95 > 300s
3. **HighCeleryQueueLength**: Queue > 100 tasks
4. **DatabaseConnectionPoolHigh**: > 80% pool usage
5. **HighMemoryUsage**: > 90% memory used
6. **DailyCostHigh**: Daily cost > $50

### Cost Alerts

1. **DailyCostHigh**: Exceeds budget
2. **ArticleCostSpike**: 2x increase vs yesterday

---

## Alert Configuration

### Email Notifications

Configure in `alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'alerts@your-domain.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
```

### Slack Integration

Add webhook URL:

```yaml
slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#cms-alerts'
```

### PagerDuty (Optional)

```yaml
pagerduty_configs:
  - service_key: '${PAGERDUTY_SERVICE_KEY}'
    description: '{{ .GroupLabels.alertname }}'
```

---

## Grafana Dashboards

### Pre-configured Dashboards

1. **System Overview**
   - API response times
   - Request rates
   - Error rates
   - Active workers

2. **Article Generation**
   - Generation time trends
   - Success/failure rates
   - Cost tracking
   - Queue lengths

3. **Infrastructure Health**
   - CPU, memory, disk usage
   - Database connections
   - Redis memory
   - Network traffic

4. **SLA Compliance**
   - p95/p99 latencies
   - Success rate trends
   - Uptime tracking

5. **Cost Analysis**
   - Daily/monthly costs
   - Cost per article
   - Budget tracking

---

## Usage Examples

### Check System Health

```bash
# Prometheus health check
curl http://localhost:9090/-/healthy

# View all targets
curl http://localhost:9090/api/v1/targets

# Query current metrics
curl http://localhost:9090/api/v1/query?query=up
```

### Query Metrics

```promql
# Average response time (last 5min)
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Success rate (last 1h)
rate(article_generation_success_total[1h]) / rate(article_generation_total[1h])

# Daily cost
sum(increase(article_generation_cost_total[24h]))
```

### Silence Alerts

```bash
# Create silence (maintenance window)
amtool silence add \
  alertname=HighCeleryQueueLength \
  --duration=2h \
  --comment="Planned maintenance"
```

---

## Maintenance

### Data Retention

Prometheus retains data for 30 days by default. Adjust in `docker-compose.monitoring.yml`:

```yaml
command:
  - '--storage.tsdb.retention.time=90d'  # 90 days
```

### Backup Prometheus Data

```bash
# Stop Prometheus
docker-compose -f docker-compose.monitoring.yml stop prometheus

# Backup data directory
tar -czf prometheus-backup-$(date +%Y%m%d).tar.gz prometheus_data/

# Restart Prometheus
docker-compose -f docker-compose.monitoring.yml start prometheus
```

### Update Alert Rules

```bash
# Edit rules
vi monitoring/alerts.yml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
```

---

## Troubleshooting

### Prometheus Not Scraping Targets

1. Check target health: http://localhost:9090/targets
2. Verify network connectivity
3. Check exporter logs:
   ```bash
   docker-compose -f docker-compose.monitoring.yml logs postgres_exporter
   ```

### Alerts Not Firing

1. Verify alert rules: http://localhost:9090/alerts
2. Check Alertmanager: http://localhost:9093
3. Test alert routing:
   ```bash
   amtool alert add \
     alertname=TestAlert \
     severity=warning
   ```

### Missing Metrics

1. Check scrape interval in `prometheus.yml`
2. Verify exporter is exposing metrics:
   ```bash
   curl http://localhost:9187/metrics  # postgres_exporter
   ```
3. Check Prometheus logs:
   ```bash
   docker-compose -f docker-compose.monitoring.yml logs prometheus
   ```

---

## Best Practices

### Alert Fatigue Prevention

1. Set appropriate thresholds
2. Use alert grouping
3. Configure inhibition rules
4. Regular alert review and tuning

### Dashboard Organization

1. Create role-specific dashboards
2. Use consistent naming
3. Add annotations for deployments
4. Set up snapshot sharing

### Cost Monitoring

1. Set daily/monthly budgets
2. Alert on cost spikes
3. Track cost per feature
4. Regular cost optimization reviews

---

## Integration with CI/CD

### Pre-deployment Checks

```bash
# Validate Prometheus config
promtool check config monitoring/prometheus.yml

# Validate alert rules
promtool check rules monitoring/alerts.yml

# Test alert rules
promtool test rules monitoring/tests/alerts_test.yml
```

### Deployment Annotations

Add deployment markers to Grafana:

```bash
curl -X POST http://localhost:3001/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Deployment: v1.2.3",
    "tags": ["deployment", "production"],
    "time": '$(date +%s000)'
  }'
```

---

## Security Considerations

1. **Access Control**
   - Enable Grafana authentication
   - Use RBAC for dashboards
   - Restrict Prometheus API access

2. **Data Protection**
   - Enable HTTPS for all services
   - Encrypt sensitive configs
   - Regular backup of metrics data

3. **Alert Security**
   - Secure webhook URLs
   - Use encrypted SMTP
   - Validate alert sources

---

## Performance Tuning

### Prometheus

```yaml
# Reduce scrape interval for high-volume metrics
scrape_configs:
  - job_name: 'high-freq'
    scrape_interval: 5s  # More frequent
  - job_name: 'low-freq'
    scrape_interval: 60s  # Less frequent
```

### Grafana

- Limit dashboard query time range
- Use query caching
- Optimize panel queries
- Reduce refresh rates

---

## Support

- **Documentation**: See [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Issues**: GitHub Issues
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/

---

## Version History

**1.0.0** (2025-10-26)
- Initial monitoring stack
- Prometheus + Grafana + Alertmanager
- Complete metrics coverage
- Automated alert rules
- Production-ready configuration

---

**Last Updated**: 2025-10-26
**Maintained by**: CMS Automation Team
