# Runbook: Application Slow Response
Status: APPROVED-FOR-HACKATHON
Version: 1.0

## Trigger
User reports application slowness or response time exceeds threshold.

## Diagnostic Steps
1. Confirm incident time window.
2. Check application response time and error rate.
3. Check DB connection pool and thread pool utilization.
4. Review application logs.
5. Check server CPU, memory, filesystem, and swap.
6. Check VMware CPU Ready and memory ballooning.
7. Check storage latency and I/O metrics.
8. Check network latency, packet loss, and interface errors.
9. Correlate anomalies in the same time window.

## Decision Guidance
- If application pool/error metrics are abnormal while infrastructure remains normal, use Application-domain RCA Hypothesis.
- If application is slow but application internal metrics remain normal and an infrastructure metric is abnormal at the same time, investigate infrastructure.
- If evidence is incomplete or contradictory, return Insufficient Evidence.

## Control
Do not execute remediation automatically in the Hackathon.
