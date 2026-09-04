# Storage Performance Standard — Synthetic Hackathon
Status: APPROVED-FOR-HACKATHON
Version: 1.0

## Storage Latency
- Healthy: < 5 ms
- Warning: >= 5 ms and <= 20 ms
- Critical: > 20 ms

## Capacity Utilization
- Healthy: < 80%
- Warning: >= 80% and < 90%
- Critical: >= 90%

## Rule
A storage latency spike should be correlated with application response time and I/O demand.
High IOPS alone is supporting evidence, not sufficient by itself to declare a fault.
