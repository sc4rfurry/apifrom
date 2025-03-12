# Monitoring and Alerting

This document provides information about the monitoring and alerting setup for APIFromAnything.

## Overview

APIFromAnything includes a comprehensive monitoring and alerting system that helps you track the performance and health of your API. The system is built on the following components:

- **Prometheus**: For metrics collection and storage
- **Grafana**: For visualization and dashboards
- **AlertManager**: For alert management and notifications

## Metrics

APIFromAnything exposes various metrics that can be collected by Prometheus:

### Request Metrics

- `apifrom_request_count`: Count of requests received, labeled by method, endpoint, and status code
- `apifrom_request_latency_seconds`: Histogram of request latency in seconds, labeled by method and endpoint
- `apifrom_requests_in_progress`: Gauge of requests currently being processed, labeled by method and endpoint
- `apifrom_error_count`: Count of errors occurred, labeled by method, endpoint, and exception type

### Database Metrics

- `apifrom_db_query_latency_seconds`: Histogram of database query latency in seconds, labeled by operation and table

### Cache Metrics

- `apifrom_cache_hit_count`: Count of cache hits, labeled by cache name
- `apifrom_cache_miss_count`: Count of cache misses, labeled by cache name

### System Metrics

- `apifrom_system_info`: System information, labeled by version and Python version

## Monitoring Setup

### Docker Compose

The monitoring stack is included in the `docker-compose.yml` file and consists of the following services:

- `prometheus`: Collects and stores metrics
- `grafana`: Visualizes metrics and provides dashboards
- `alertmanager`: Manages alerts and notifications

### Configuration

#### Prometheus

Prometheus is configured in `monitoring/prometheus/prometheus.yml`. The configuration includes:

- Scrape configurations for various services
- Alert rules
- AlertManager configuration

#### Grafana

Grafana is configured with:

- Datasources in `monitoring/grafana/provisioning/datasources/prometheus.yml`
- Dashboards in `monitoring/grafana/provisioning/dashboards/`

#### AlertManager

AlertManager is configured in `monitoring/alertmanager/alertmanager.yml`. The configuration includes:

- Notification receivers (email, Slack, PagerDuty)
- Routing configuration
- Inhibition rules

## Dashboards

APIFromAnything comes with a pre-configured Grafana dashboard that provides insights into the performance and health of your API. The dashboard includes the following panels:

- Request Rate
- Request Latency
- Error Rate
- Requests In Progress
- Database Query Latency
- Cache Hit/Miss Rate

## Alerts

APIFromAnything includes pre-configured alerts that notify you when certain conditions are met. The alerts include:

- **HighRequestLatency**: Triggered when the 95th percentile of request latency is above 1s for an endpoint
- **HighErrorRate**: Triggered when the error rate is above 5% for an endpoint
- **CriticalErrorRate**: Triggered when the error rate is above 20% for an endpoint
- **HighRequestRate**: Triggered when the request rate is above 100 requests per second for an endpoint
- **HighDatabaseLatency**: Triggered when the 95th percentile of database query latency is above 0.5s
- **HighCacheMissRate**: Triggered when the cache miss rate is above 80%
- **InstanceDown**: Triggered when an instance is down for more than 1 minute
- **HighMemoryUsage**: Triggered when memory usage is above 1GB

## Integration with Application Code

### Middleware

APIFromAnything includes a Prometheus middleware that automatically collects request metrics. The middleware is configured in `apifrom/monitoring.py`.

### Custom Metrics

You can add custom metrics to your application by using the `apifrom.monitoring` module. For example:

```python
from apifrom.monitoring import DatabaseMetrics, CacheMetrics

# Track database query time
async with DatabaseMetrics.track_query_time("select", "users"):
    result = await db.fetch_all("SELECT * FROM users")

# Record cache hit/miss
if result_from_cache:
    CacheMetrics.record_hit("user_cache")
else:
    CacheMetrics.record_miss("user_cache")
```

## Accessing Monitoring Tools

When running with Docker Compose, the monitoring tools are available at the following URLs:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default credentials: admin/admin)
- AlertManager: http://localhost:9093

## Customizing Monitoring

### Adding Custom Metrics

You can add custom metrics by modifying the `apifrom/monitoring.py` file. For example, to add a new counter:

```python
from prometheus_client import Counter

MY_COUNTER = Counter(
    'apifrom_my_counter',
    'Description of my counter',
    ['label1', 'label2'],
    registry=registry
)

# Increment the counter
MY_COUNTER.labels(label1='value1', label2='value2').inc()
```

### Adding Custom Dashboards

You can add custom Grafana dashboards by adding JSON files to the `monitoring/grafana/provisioning/dashboards/` directory.

### Customizing Alerts

You can customize alerts by modifying the `monitoring/prometheus/rules/alerts.yml` file.

## Best Practices

- Monitor both application-level metrics (request rate, latency) and system-level metrics (CPU, memory)
- Set up alerts for critical conditions that require immediate attention
- Use dashboards to visualize trends and identify potential issues before they become critical
- Regularly review and adjust alert thresholds based on your application's performance characteristics
- Implement proper logging alongside metrics for better debugging capabilities 