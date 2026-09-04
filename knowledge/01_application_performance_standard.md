# Application Performance Standard — Synthetic Hackathon
Status: APPROVED-FOR-HACKATHON
Version: 1.0

## Response Time
- Healthy: <= 500 ms
- Warning: > 500 ms and <= 1000 ms
- Critical: > 1000 ms

## Error Rate
- Healthy: <= 2%
- Warning: > 2% and <= 5%
- Critical: > 5%

## Database Connection Pool Utilization
- Healthy: <= 80%
- Warning: > 80% and <= 90%
- Critical: > 90%

## Thread Pool Utilization
- Healthy: <= 80%
- Warning: > 80% and <= 90%
- Critical: > 90%

## Rule
High response time alone is not sufficient to conclude application root cause.
Correlate application metrics with server, virtualization, storage, network, alerts, and logs.
