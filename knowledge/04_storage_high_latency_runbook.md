# Runbook: Storage High Latency
Status: APPROVED-FOR-HACKATHON
Version: 1.0

## Trigger
Storage latency >= 5 ms or application slowdown is suspected to be storage-related.

## Diagnostic Steps
1. Confirm latency start time and duration.
2. Check latency, IOPS, throughput, queue depth, and capacity.
3. Identify affected storage pool and datastore.
4. Correlate storage latency with application response time.
5. Check server and VMware metrics.
6. Check network metrics.
7. Review monitoring alerts.

## RCA Hypothesis Guidance
Storage degradation is a reasonable RCA Hypothesis when:
- Storage latency breaches threshold.
- Application response time degrades in the same time window.
- Application internal saturation is not present.
- Compute and network do not show competing critical anomalies.

## Control
Recommend actions only. Do not perform remediation automatically in the Hackathon.
